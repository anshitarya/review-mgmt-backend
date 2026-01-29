"""WSGI entry point for Render/production deployment."""
from app.main import app

if __name__ == "__main__":
    app.run()
