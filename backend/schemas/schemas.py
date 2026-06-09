import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

# --- Auth Schemas ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one numeric digit")
        special_chars = "@$!%*?&+-=()[]{}#_\\|:;\"'<>,./?"
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str


# --- Carbon Footprint Calculator ---
class CarbonEntryCreate(BaseModel):
    transportation_car: float = Field(0.0, ge=0.0)
    transportation_bike: float = Field(0.0, ge=0.0)
    transportation_public: float = Field(0.0, ge=0.0)
    transportation_flights: float = Field(0.0, ge=0.0)
    
    energy_electricity: float = Field(0.0, ge=0.0)
    energy_ac: float = Field(0.0, ge=0.0)
    energy_appliance: float = Field(0.0, ge=0.0)
    
    food_preference: str = Field("non-vegetarian")
    
    shopping_clothing: float = Field(0.0, ge=0.0)
    shopping_electronics: float = Field(0.0, ge=0.0)
    
    waste_recycling: str = Field("rarely")
    waste_plastic: str = Field("average")

    @field_validator('food_preference')
    @classmethod
    def validate_food(cls, v: str) -> str:
        valid = ["vegan", "vegetarian", "non-vegetarian"]
        if v.lower() not in valid:
            raise ValueError(f"food_preference must be one of {valid}")
        return v.lower()

    @field_validator('waste_recycling')
    @classmethod
    def validate_recycling(cls, v: str) -> str:
        valid = ["rarely", "sometimes", "always"]
        if v.lower() not in valid:
            raise ValueError(f"waste_recycling must be one of {valid}")
        return v.lower()

    @field_validator('waste_plastic')
    @classmethod
    def validate_plastic(cls, v: str) -> str:
        valid = ["low", "average", "high"]
        if v.lower() not in valid:
            raise ValueError(f"waste_plastic must be one of {valid}")
        return v.lower()

class CarbonEntryResponse(CarbonEntryCreate):
    id: int
    user_id: int
    total_emissions: float
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- Recommendations ---
class RecommendationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    difficulty: str
    expected_reduction: float
    estimated_savings: float
    is_completed: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- Sustainability Challenges ---
class ChallengeResponse(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    points: int

    class Config:
        from_attributes = True

class ChallengeProgressResponse(BaseModel):
    id: int
    user_id: int
    challenge_id: int
    start_date: datetime.datetime
    end_date: datetime.datetime
    completion_status: str
    points_earned: int
    challenge: ChallengeResponse

    class Config:
        from_attributes = True

class ChallengeJoinRequest(BaseModel):
    challenge_id: int


# --- Dashboard / Analytics ---
class CategoryBreakdown(BaseModel):
    transportation: float
    energy: float
    food: float
    shopping: float
    waste: float

class AnalyticsSummary(BaseModel):
    current_month_emissions: float
    previous_month_emissions: float
    reduction_percentage: float
    sustainability_score: int
    category_breakdown_percentages: CategoryBreakdown

class TrendPoint(BaseModel):
    label: str  # e.g., "Jan", "Week 1"
    emissions: float

class HistoryAnalytics(BaseModel):
    trends: List[TrendPoint]
