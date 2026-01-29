from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(100), index=True)
    rating = Column(Integer, index=True)  # 1-5 scale
    text = Column(Text, nullable=False)
    date = Column(Date, index=True)
    sentiment = Column(String(20), index=True)  # positive, negative, neutral
    topic = Column(String(50), index=True)  # service, cleanliness, price, food, etc.
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())