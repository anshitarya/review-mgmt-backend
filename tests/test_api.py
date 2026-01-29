import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
import os

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Create test database
    Base.metadata.create_all(bind=engine)
    
    # Set test API key
    os.environ["API_KEY"] = "test-api-key"
    
    with TestClient(app) as c:
        yield c
    
    # Clean up
    Base.metadata.drop_all(bind=engine)

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_ingest_reviews_success(client):
    """Test successful review ingestion"""
    headers = {"Authorization": "Bearer test-api-key"}
    review_data = {
        "reviews": [
            {
                "id": 1,
                "location": "NYC",
                "rating": 5,
                "text": "Great service and food!",
                "date": "2025-06-15"
            },
            {
                "id": 2,
                "location": "SF",
                "rating": 2,
                "text": "Poor experience, slow service.",
                "date": "2025-06-16"
            }
        ]
    }
    
    response = client.post("/api/ingest", json=review_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["created_count"] == 2
    assert "message" in data

def test_ingest_reviews_unauthorized(client):
    """Test review ingestion without API key"""
    review_data = {
        "reviews": [
            {
                "id": 3,
                "location": "LA",
                "rating": 4,
                "text": "Good food!",
                "date": "2025-06-17"
            }
        ]
    }
    
    response = client.post("/api/ingest", json=review_data)
    assert response.status_code == 403

def test_get_reviews(client):
    """Test getting reviews with filters"""
    headers = {"Authorization": "Bearer test-api-key"}
    
    # Get all reviews
    response = client.get("/api/reviews", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "reviews" in data
    assert "total" in data
    assert data["total"] >= 0
    
    # Filter by location
    response = client.get("/api/reviews?location=NYC", headers=headers)
    assert response.status_code == 200
    data = response.json()
    if data["reviews"]:
        assert all(review["location"] == "NYC" for review in data["reviews"])

def test_get_specific_review(client):
    """Test getting a specific review"""
    headers = {"Authorization": "Bearer test-api-key"}
    
    # First add a review
    review_data = {
        "reviews": [
            {
                "id": 999,
                "location": "Test",
                "rating": 3,
                "text": "Test review",
                "date": "2025-06-18"
            }
        ]
    }
    client.post("/api/ingest", json=review_data, headers=headers)
    
    # Get the specific review
    response = client.get("/api/reviews/999", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 999
    assert data["text"] == "Test review"

def test_get_nonexistent_review(client):
    """Test getting a review that doesn't exist"""
    headers = {"Authorization": "Bearer test-api-key"}
    response = client.get("/api/reviews/99999", headers=headers)
    assert response.status_code == 404

def test_analytics(client):
    """Test analytics endpoint"""
    headers = {"Authorization": "Bearer test-api-key"}
    response = client.get("/api/analytics", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "sentiment_counts" in data
    assert "topic_counts" in data
    assert "total_reviews" in data
    assert "avg_rating" in data

def test_search_reviews(client):
    """Test search functionality"""
    headers = {"Authorization": "Bearer test-api-key"}
    
    response = client.get("/api/search?q=service", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "query" in data
    assert data["query"] == "service"