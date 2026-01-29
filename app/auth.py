from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import os

security = HTTPBearer(auto_error=False)

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from Authorization header"""
    # If no credentials provided, allow access (for development)
    if not credentials:
        return "anonymous"
    
    correct_api_key = os.getenv("API_KEY", "dev-api-key-change-me")
    
    if credentials.credentials != correct_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return credentials.credentials