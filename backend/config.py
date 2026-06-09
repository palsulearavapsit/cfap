import os
from dotenv import load_dotenv

# Load environment variables from .env file at the root of the project
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "ecotrack_flask_secret_development_key_12345")
    
    # Database URL configuration
    # Primarily expects MySQL, fallback to SQLite if not configured (useful for unit tests)
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Fallback to local SQLite for tests/fallback
        DATABASE_URL = "sqlite:///ecotrack.db"
    
    # Ensure DATABASE_URL is properly formatted for SQLAlchemy
    # (e.g. replacing postgres:// with postgresql:// if any, but we focus on mysql)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini API Configurations
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
