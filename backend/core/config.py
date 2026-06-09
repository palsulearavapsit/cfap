import os
from pydantic import BaseModel, Field, field_validator

class Settings(BaseModel):
    SECRET_KEY: str = Field("ecotrack_ai_super_secret_development_key_987654321")
    ALGORITHM: str = Field("HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7)
    DATABASE_URL: str = Field("postgresql://postgres:postgres@localhost:5432/ecotrack")

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql://") and not v.startswith("postgres://") and not v.startswith("sqlite:///"):
            raise ValueError("DATABASE_URL must start with postgresql://, postgres:// or sqlite:///")
        return v

# Instantiate settings with environment variables or defaults
settings = Settings(
    SECRET_KEY=os.getenv("SECRET_KEY", "ecotrack_ai_super_secret_development_key_987654321"),
    ALGORITHM=os.getenv("ALGORITHM", "HS256"),
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    REFRESH_TOKEN_EXPIRE_DAYS=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
    DATABASE_URL=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ecotrack")
)

def verify_environment():
    """Verify vital environmental variables on startup."""
    print("📋 Verifying application environment configurations...")
    if settings.SECRET_KEY == "ecotrack_ai_super_secret_development_key_987654321":
        print("⚠️ WARNING: Default SECRET_KEY is active. Please customize SECRET_KEY in production.")
    print("✅ Environment configuration verification complete.")
