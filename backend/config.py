import os
import urllib.parse
from typing import Any, Dict, Optional, Type

from dotenv import load_dotenv

# Load environment variables from .env file at the root of the project
load_dotenv()


class DatabaseURLParser:
    """Specialized configuration parser class for validating and normalizing database URLs (Item 5)."""

    @classmethod
    def parse_and_normalize(cls, db_url: Optional[str]) -> Optional[str]:
        """Validates database credentials strength and normalizes connection URIs (Item 29)."""
        if not db_url:
            return None

        # Perform password strength checks to alert on weak database setup configs (Item 29)
        try:
            if "://" in db_url:
                _, rest = db_url.split("://", 1)
                if "@" in rest:
                    user_pass, _ = rest.rsplit("@", 1)
                    if ":" in user_pass:
                        _, password = user_pass.split(":", 1)
                        decoded = urllib.parse.unquote(password)
                        if not decoded or decoded.lower() in [
                            "password",
                            "123456",
                            "root",
                            "admin",
                            "123",
                            "postgres",
                        ]:
                            print(
                                f"[WARNING] Database URL password '{decoded}' is extremely weak (Item 29)!"
                            )
        except Exception:
            pass

        # Normalize scheme postgres:// to postgresql://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        # Extract and URL-encode the password if it contains special characters
        try:
            url_parts = db_url.split("?", 1)
            base_url = url_parts[0]
            query_params = "?" + url_parts[1] if len(url_parts) > 1 else ""

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
            print(
                f"[WARNING] Could not auto-parse/fix DATABASE_URL password: {parse_err}"
            )

        # Remove pgbouncer query parameter as it is unsupported by psycopg2
        if "pgbouncer=true" in db_url:
            db_url = db_url.replace("?pgbouncer=true", "").replace(
                "&pgbouncer=true", ""
            )
        return db_url


class Config:
    """Base configuration parameters type-annotated definitions (Item 7)."""

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "ecotrack_flask_secret_development_key_12345"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    BCRYPT_LOG_ROUNDS: int = 12

    # Configure default connection pool recycled timers (Item 35)
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = {
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }


class DevelopmentConfig(Config):
    """Development profile configurations."""

    DEBUG: bool = True
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///ecotrack.db")
    SQLALCHEMY_DATABASE_URI: Optional[str] = DatabaseURLParser.parse_and_normalize(
        DATABASE_URL
    )


class TestingConfig(Config):
    """Testing profile configurations."""

    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    GEMINI_API_KEY: Optional[str] = None
    BCRYPT_LOG_ROUNDS: int = 4


class ProductionConfig(Config):
    """Production profile configurations, enforcing environment checks (Item 19, 38)."""

    DEBUG: bool = False
    TESTING: bool = False
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI: Optional[str] = DatabaseURLParser.parse_and_normalize(
        DATABASE_URL
    )

    # Specialize connection pool options for PostgreSQL in production (Item 35)
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        }

    # Warn if default development secret key is used in production (Item 38)
    if Config.SECRET_KEY == "ecotrack_flask_secret_development_key_12345":
        print(
            "[WARNING] Insecure SECRET_KEY deployed to Production configuration environment (Item 38)!"
        )


config_by_name: Dict[str, Type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
