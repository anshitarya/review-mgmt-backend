from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from .database import create_tables
from .routers import reviews
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Review Management System",
    description="A comprehensive review management API with AI-powered insights (Cohere-enhanced)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
allow_origins_list = [
    "http://localhost:3000",  # Local development
    "http://localhost:8888",  # Local backend
    "https://review-management-frontend-7jrt6zxmo-anshits-projects-38a258a5.vercel.app",  # Your Vercel frontend
]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url and frontend_url not in allow_origins_list:
    allow_origins_list.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reviews.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    create_tables()

@app.get("/")
async def root():
    """Redirect root to API docs"""
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)