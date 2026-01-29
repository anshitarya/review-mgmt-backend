from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List
import math
from datetime import datetime

from ..database import get_db
from ..models.review import Review
from ..schemas import (
    ReviewCreate, ReviewIngest, ReviewResponse, ReviewUpdate, 
    ReviewsList, SuggestedReply, Analytics, SearchResults, SimilarReview
)
from ..auth import verify_api_key
from ..services.ai_service_cohere import AIService

router = APIRouter(prefix="/api", tags=["reviews"])
ai_service = AIService()

@router.post("/ingest", response_model=dict)
async def ingest_reviews(
    review_data: ReviewIngest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Ingest multiple reviews and analyze them with AI"""
    try:
        created_reviews = []
        skipped_reviews = []
        
        for review_data_item in review_data.reviews:
            # Check for duplicates based on content, location, and date (not ID)
            existing = db.query(Review).filter(
                Review.text == review_data_item.text,
                Review.location == review_data_item.location,
                Review.date == review_data_item.date,
                Review.rating == review_data_item.rating
            ).first()
            
            if existing:
                skipped_reviews.append(review_data_item)
                continue  # Skip exact duplicates
            
            # Analyze sentiment and topic
            sentiment = ai_service.analyze_sentiment(review_data_item.text)
            topic = ai_service.extract_topic(review_data_item.text)
            
            # Create review (don't set ID, let it auto-increment)
            review = Review(
                location=review_data_item.location,
                rating=review_data_item.rating,
                text=review_data_item.text,
                date=review_data_item.date,
                sentiment=sentiment,
                topic=topic
            )
            
            db.add(review)
            created_reviews.append(review)
        
        db.commit()
        
        # Rebuild similarity index
        all_reviews = db.query(Review).all()
        ai_service.build_similarity_index(all_reviews)
        
        return {
            "message": f"Successfully ingested {len(created_reviews)} reviews",
            "created_count": len(created_reviews),
            "skipped_count": len(skipped_reviews)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error ingesting reviews: {str(e)}")

@router.get("/locations", response_model=List[str])
async def get_locations(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get all unique locations from reviews"""
    locations = db.query(Review.location).distinct().filter(Review.location.isnot(None)).all()
    return [location[0] for location in locations if location[0]]

@router.get("/reviews", response_model=ReviewsList)
async def get_reviews(
    location: Optional[str] = Query(None, description="Filter by location"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    q: Optional[str] = Query(None, description="Text search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of reviews per page"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get reviews with filtering and pagination"""
    
    query = db.query(Review)
    
    # Apply filters
    filters = []
    if location:
        filters.append(Review.location.ilike(f"%{location}%"))
    if sentiment:
        filters.append(Review.sentiment == sentiment)
    if q:
        filters.append(Review.text.ilike(f"%{q}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    reviews = query.offset(offset).limit(page_size).all()
    
    total_pages = math.ceil(total / page_size)
    
    return ReviewsList(
        reviews=[ReviewResponse.from_orm(review) for review in reviews],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get a specific review by ID"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return ReviewResponse.from_orm(review)

@router.post("/reviews/{review_id}/suggest-reply", response_model=SuggestedReply)
async def suggest_reply(
    review_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Generate AI-powered suggested reply for a review"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    try:
        reply_data = ai_service.generate_reply(
            review.text, 
            review.rating, 
            review.sentiment or "neutral", 
            review.topic or "other"
        )
        
        return SuggestedReply(**reply_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating reply: {str(e)}")

@router.get("/analytics", response_model=Analytics)
async def get_analytics(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get analytics about reviews"""
    
    # Sentiment counts
    sentiment_counts = db.query(
        Review.sentiment, func.count(Review.sentiment)
    ).group_by(Review.sentiment).all()
    
    sentiment_dict = {sentiment: count for sentiment, count in sentiment_counts}
    
    # Topic counts
    topic_counts = db.query(
        Review.topic, func.count(Review.topic)
    ).group_by(Review.topic).all()
    
    topic_dict = {topic: count for topic, count in topic_counts}
    
    # Total reviews and average rating
    total_reviews = db.query(Review).count()
    avg_rating = db.query(func.avg(Review.rating)).scalar() or 0.0
    
    return Analytics(
        sentiment_counts=sentiment_dict,
        topic_counts=topic_dict,
        total_reviews=total_reviews,
        avg_rating=round(avg_rating, 2)
    )

@router.get("/search", response_model=SearchResults)
async def search_similar_reviews(
    q: str = Query(..., description="Search query"),
    k: int = Query(5, ge=1, le=20, description="Number of similar reviews to return"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Find reviews similar to the query using TF-IDF and cosine similarity"""
    
    # Ensure similarity index is built
    all_reviews = db.query(Review).all()
    ai_service.build_similarity_index(all_reviews)
    
    # Find similar reviews
    similar_ids_scores = ai_service.find_similar_reviews(q, k)
    
    if not similar_ids_scores:
        return SearchResults(results=[], query=q)
    
    # Get review details
    similar_ids = [id_score[0] for id_score in similar_ids_scores]
    reviews = db.query(Review).filter(Review.id.in_(similar_ids)).all()
    
    # Create results with similarity scores
    results = []
    review_dict = {r.id: r for r in reviews}
    
    for review_id, score in similar_ids_scores:
        if review_id in review_dict:
            review = review_dict[review_id]
            results.append(SimilarReview(
                id=review.id,
                text=review.text,
                location=review.location,
                rating=review.rating,
                similarity_score=round(score, 3)
            ))
    
    return SearchResults(results=results, query=q)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}