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
    # Supabase / Heroku often supply postgres:// but SQLAlchemy requires postgresql://
    if DATABASE_URL:
        # 1. Normalize scheme postgres:// to postgresql://
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

        # 2. Extract and URL-encode the password if it contains special characters like '@'
        try:
            url_parts = DATABASE_URL.split('?', 1)
            base_url = url_parts[0]
            query_params = '?' + url_parts[1] if len(url_parts) > 1 else ''
            
            if "://" in base_url:
                scheme, rest = base_url.split("://", 1)
                if "/" in rest:
                    authority, db_path = rest.split("/", 1)
                else:
                    authority = rest
                    db_path = ""
                    
                if "@" in authority:
                    user_pass, host_port = authority.rsplit("@", 1)
                    if ":" in user_pass:
                        username, password = user_pass.split(":", 1)
                        import urllib.parse
                        # Unquote first to prevent double-encoding, then quote
                        unquoted_password = urllib.parse.unquote(password)
                        quoted_password = urllib.parse.quote_plus(unquoted_password)
                        user_pass = f"{username}:{quoted_password}"
                    authority = f"{user_pass}@{host_port}"
                
                if db_path:
                    base_url = f"{scheme}://{authority}/{db_path}"
                else:
                    base_url = f"{scheme}://{authority}"
            DATABASE_URL = base_url + query_params
        except Exception as parse_err:
            print(f"[WARNING] Could not auto-parse/fix DATABASE_URL password: {parse_err}")

        # 3. Remove pgbouncer query parameter as it is unsupported by psycopg2
        if "pgbouncer=true" in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini API Configurations
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
