from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from enum import Enum

class SentimentEnum(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"

class TopicEnum(str, Enum):
    service = "service"
    cleanliness = "cleanliness"
    price = "price"
    food = "food"
    atmosphere = "atmosphere"
    location = "location"
    technology = "technology"
    other = "other"

class ReviewBase(BaseModel):
    location: str = Field(..., max_length=100)
    rating: int = Field(..., ge=1, le=5)
    text: str = Field(..., min_length=1)
    date: date

class ReviewCreate(ReviewBase):
    id: Optional[int] = None

class ReviewIngest(BaseModel):
    reviews: List[ReviewCreate]

class ReviewUpdate(BaseModel):
    location: Optional[str] = Field(None, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    text: Optional[str] = Field(None, min_length=1)
    date: Optional[date] = None

class ReviewResponse(ReviewBase):
    id: int
    sentiment: Optional[str] = None
    topic: Optional[str] = None

    class Config:
        from_attributes = True

class ReviewsList(BaseModel):
    reviews: List[ReviewResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class SuggestedReply(BaseModel):
    reply: str
    tags: dict
    reasoning_log: str

class Analytics(BaseModel):
    sentiment_counts: dict
    topic_counts: dict
    total_reviews: int
    avg_rating: float

class SimilarReview(BaseModel):
    id: int
    text: str
    location: str
    rating: int
    similarity_score: float

class SearchResults(BaseModel):
    results: List[SimilarReview]
    query: str