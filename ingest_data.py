"""
Data ingestion script to populate the database with sample reviews
"""
import json
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.review import Base, Review
from app.services.ai_service_simple import AIService

# Sample reviews data
sample_reviews = [
    {
        "text": "Great experience! The staff was very friendly and the food was delicious. Highly recommend this location.",
        "rating": 5,
        "location": "Downtown Store",
        "author": "Sarah M.",
        "platform": "Google",
        "external_id": "goog_001"
    },
    {
        "text": "Food was cold when it arrived. Service was slow and the staff seemed overwhelmed. Very disappointed.",
        "rating": 2,
        "location": "Mall Location",
        "author": "Mike R.",
        "platform": "Yelp",
        "external_id": "yelp_001"
    },
    {
        "text": "Love coming here! Always clean, great atmosphere, and consistent quality. The new menu items are fantastic.",
        "rating": 5,
        "location": "Airport Location",
        "author": "Jessica L.",
        "platform": "TripAdvisor",
        "external_id": "trip_001"
    },
    {
        "text": "App crashed when trying to place my order. Had to call instead. Technology needs improvement.",
        "rating": 3,
        "location": "Downtown Store",
        "author": "David K.",
        "platform": "App Store",
        "external_id": "app_001"
    },
    {
        "text": "Bathroom was dirty and the tables weren't cleaned properly. Health standards need attention.",
        "rating": 2,
        "location": "Highway Location",
        "author": "Lisa P.",
        "platform": "Google",
        "external_id": "goog_002"
    },
    {
        "text": "Perfect location with easy parking. Staff is always helpful and prices are reasonable.",
        "rating": 4,
        "location": "Suburban Plaza",
        "author": "Tom W.",
        "platform": "Facebook",
        "external_id": "fb_001"
    },
    {
        "text": "The cashier was rude and seemed annoyed when I asked questions about the menu. Poor customer service.",
        "rating": 2,
        "location": "Mall Location",
        "author": "Rachel B.",
        "platform": "Yelp",
        "external_id": "yelp_002"
    },
    {
        "text": "Amazing food quality! You can taste the fresh ingredients. Will definitely come back.",
        "rating": 5,
        "location": "Downtown Store",
        "author": "Carlos M.",
        "platform": "Google",
        "external_id": "goog_003"
    },
    {
        "text": "Prices have gone up significantly but quality has remained the same. Getting expensive for what you get.",
        "rating": 3,
        "location": "Airport Location",
        "author": "Nancy T.",
        "platform": "TripAdvisor",
        "external_id": "trip_002"
    },
    {
        "text": "Love the new renovations! The atmosphere is much more comfortable and modern. Great job!",
        "rating": 4,
        "location": "Suburban Plaza",
        "author": "Kevin H.",
        "platform": "Facebook",
        "external_id": "fb_002"
    },
    {
        "text": "Fast service and hot food. Exactly what I expect. The drive-through is very efficient.",
        "rating": 4,
        "location": "Highway Location",
        "author": "Amanda S.",
        "platform": "Google",
        "external_id": "goog_004"
    },
    {
        "text": "Website is confusing and hard to navigate. Need better online ordering system.",
        "rating": 3,
        "location": "Online",
        "author": "James C.",
        "platform": "Website",
        "external_id": "web_001"
    },
    {
        "text": "Best customer service I've ever experienced! The manager went above and beyond to help.",
        "rating": 5,
        "location": "Mall Location",
        "author": "Patricia D.",
        "platform": "Yelp",
        "external_id": "yelp_003"
    },
    {
        "text": "Food was excellent but had to wait 20 minutes in the drive-through. Need better staffing.",
        "rating": 3,
        "location": "Highway Location",
        "author": "Robert F.",
        "platform": "Google",
        "external_id": "goog_005"
    },
    {
        "text": "Clean facilities, friendly staff, and great value for money. This is my go-to location.",
        "rating": 4,
        "location": "Suburban Plaza",
        "author": "Michelle G.",
        "platform": "Facebook",
        "external_id": "fb_003"
    },
    {
        "text": "Terrible experience. Wrong order, cold food, and rude staff. Will not be returning.",
        "rating": 1,
        "location": "Airport Location",
        "author": "Steven J.",
        "platform": "TripAdvisor",
        "external_id": "trip_003"
    },
    {
        "text": "Great location and parking is easy. Food is consistently good and staff is professional.",
        "rating": 4,
        "location": "Downtown Store",
        "author": "Laura K.",
        "platform": "Google",
        "external_id": "goog_006"
    },
    {
        "text": "Mobile app works great! Easy to order and payment was smooth. Love the convenience.",
        "rating": 5,
        "location": "Various",
        "author": "Chris N.",
        "platform": "App Store",
        "external_id": "app_002"
    },
    {
        "text": "Music was too loud and made it hard to have a conversation. Otherwise, food was good.",
        "rating": 3,
        "location": "Mall Location",
        "author": "Diana O.",
        "platform": "Yelp",
        "external_id": "yelp_004"
    },
    {
        "text": "Outstanding food quality and presentation. You can tell they care about what they serve.",
        "rating": 5,
        "location": "Suburban Plaza",
        "author": "Mark P.",
        "platform": "Facebook",
        "external_id": "fb_004"
    }
]

def create_database():
    """Create the database and tables"""
    engine = create_engine("sqlite:///./reviews.db")
    Base.metadata.create_all(bind=engine)
    return engine

def main():
    print("Creating database...")
    engine = create_database()
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Initialize AI service
    ai_service = AIService()
    
    print("Ingesting sample reviews...")
    
    # Clear existing reviews
    db.query(Review).delete()
    db.commit()
    
    # Add sample reviews with AI analysis
    for i, review_data in enumerate(sample_reviews):
        # Generate timestamp (spread over last 30 days)
        days_ago = i % 30
        created_at = datetime.now() - timedelta(days=days_ago)
        
        # Analyze with AI service
        sentiment = ai_service.analyze_sentiment(review_data["text"])
        topic = ai_service.extract_topic(review_data["text"])
        
        review = Review(
            text=review_data["text"],
            rating=review_data["rating"],
            sentiment=sentiment,
            topic=topic,
            location=review_data["location"],
            date=created_at.date()
        )
        
        db.add(review)
    
    # Commit all reviews
    db.commit()
    
    # Build similarity index
    all_reviews = db.query(Review).all()
    ai_service.build_similarity_index(all_reviews)
    
    print(f"Successfully ingested {len(sample_reviews)} reviews!")
    print("\nBreakdown by sentiment:")
    for sentiment in ['positive', 'negative', 'neutral']:
        count = db.query(Review).filter(Review.sentiment == sentiment).count()
        print(f"  {sentiment.capitalize()}: {count}")
    
    print("\nBreakdown by topic:")
    topics = db.query(Review.topic).distinct().all()
    for (topic,) in topics:
        count = db.query(Review).filter(Review.topic == topic).count()
        print(f"  {topic.capitalize()}: {count}")
    
    print("\nBreakdown by location:")
    locations = db.query(Review.location).distinct().all()
    for (location,) in locations:
        count = db.query(Review).filter(Review.location == location).count()
        print(f"  {location}: {count}")
    
    db.close()
    print("\nDatabase is ready! You can now access the API at http://localhost:8000")

if __name__ == "__main__":
    main()