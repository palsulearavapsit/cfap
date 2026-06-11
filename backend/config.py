import os
from dotenv import load_dotenv

# Load environment variables from .env file at the root of the project
load_dotenv()

def normalize_database_url(db_url):
    if not db_url:
        return None
    # 1. Normalize scheme postgres:// to postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # 2. Extract and URL-encode the password if it contains special characters like '@'
    try:
        url_parts = db_url.split('?', 1)
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
        db_url = base_url + query_params
    except Exception as parse_err:
        print(f"[WARNING] Could not auto-parse/fix DATABASE_URL password: {parse_err}")

    # 3. Remove pgbouncer query parameter as it is unsupported by psycopg2
    if "pgbouncer=true" in db_url:
        db_url = db_url.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")
    return db_url

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "ecotrack_flask_secret_development_key_12345")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ecotrack.db")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(DATABASE_URL)

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    GEMINI_API_KEY = None

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    DATABASE_URL = os.getenv("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(DATABASE_URL)
    
    # Enable PostgreSQL connection pool settings for robust production usage
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        }

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}
