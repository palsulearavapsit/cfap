from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User profile database model representation."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """Unique auto-incrementing integer identifier for the user."""

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    """Unique string email address representing the login username."""

    password_hash = db.Column(db.String(255), nullable=False)
    """Hashed user password string using Bcrypt encryption."""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    """Timestamp indicating when the user account was registered."""

    # Relationships
    carbon_entries = db.relationship("CarbonEntry", backref="user", cascade="all, delete-orphan", lazy=True)
    recommendations = db.relationship("Recommendation", backref="user", cascade="all, delete-orphan", lazy=True)
    challenge_progresses = db.relationship("ChallengeProgress", backref="user", cascade="all, delete-orphan", lazy=True)

    def to_dict(self) -> dict:
        """Serializes user record fields to dictionary mapping."""
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat()
        }


class CarbonEntry(db.Model):
    """Monthly carbon footprint calculation entry model representation."""
    __tablename__ = 'carbon_entries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """Unique auto-incrementing identifier for the carbon footprint entry."""

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    """Foreign key relation referencing the user who submitted the questionnaire."""
    
    # Inputs
    transportation_car = db.Column(db.Float, default=0.0, nullable=False)
    """Distance driven by car in kilometers during the month."""

    transportation_bike = db.Column(db.Float, default=0.0, nullable=False)
    """Distance ridden by bike in kilometers during the month."""

    transportation_public = db.Column(db.Float, default=0.0, nullable=False)
    """Distance traveled via public transit in kilometers during the month."""

    transportation_flights = db.Column(db.Float, default=0.0, nullable=False)
    """Distance traveled via flights in kilometers during the month."""
    
    energy_electricity = db.Column(db.Float, default=0.0, nullable=False)
    """Electricity consumed at home in kilowatt-hours (kWh) during the month."""

    energy_ac = db.Column(db.Float, default=0.0, nullable=False)
    """Air conditioning running time in hours during the month."""

    energy_appliance = db.Column(db.Float, default=0.0, nullable=False)
    """Home appliances running time in hours during the month."""
    
    food_preference = db.Column(db.String(50), default="non-vegetarian", nullable=False)
    """User dietary preference category (vegan, vegetarian, or non-vegetarian)."""
    
    shopping_clothing = db.Column(db.Float, default=0.0, nullable=False)
    """Number of new clothing items purchased during the month."""

    shopping_electronics = db.Column(db.Float, default=0.0, nullable=False)
    """Number of new electronic devices purchased during the month."""
    
    waste_recycling = db.Column(db.String(50), default="rarely", nullable=False)
    """Recycling frequency category (rarely, sometimes, or always)."""

    waste_plastic = db.Column(db.String(50), default="average", nullable=False)
    """Plastic waste generation level category (low, average, or high)."""
    
    # Calculated Output
    total_emissions = db.Column(db.Float, nullable=False)
    """Calculated total greenhouse gas emissions in kilograms of CO2 equivalent (kg CO2e)."""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    """Timestamp indicating when the carbon entry was calculated and recorded."""

    def to_dict(self) -> dict:
        """Serializes carbon entry record fields to dictionary mapping."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "transportation_car": self.transportation_car,
            "transportation_bike": self.transportation_bike,
            "transportation_public": self.transportation_public,
            "transportation_flights": self.transportation_flights,
            "energy_electricity": self.energy_electricity,
            "energy_ac": self.energy_ac,
            "energy_appliance": self.energy_appliance,
            "food_preference": self.food_preference,
            "shopping_clothing": self.shopping_clothing,
            "shopping_electronics": self.shopping_electronics,
            "waste_recycling": self.waste_recycling,
            "waste_plastic": self.waste_plastic,
            "total_emissions": self.total_emissions,
            "created_at": self.created_at.isoformat()
        }


class Recommendation(db.Model):
    """Personalized carbon reduction recommendations model representation."""
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """Unique auto-incrementing identifier for the recommendation."""

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    """Foreign key relation referencing the target user for the recommendation."""

    title = db.Column(db.String(255), nullable=False)
    """Brief headline describing the proposed action item."""

    description = db.Column(db.String(1000), nullable=False)
    """Detailed instruction explaining how the user can fulfill this recommendation."""

    difficulty = db.Column(db.String(50), nullable=False)
    """Assigned action difficulty tier (Beginner, Intermediate, Advanced, Expert)."""

    expected_reduction = db.Column(db.Float, nullable=False)
    """Projected greenhouse gas emission savings in kilograms of CO2 per month."""

    estimated_savings = db.Column(db.Float, nullable=False)
    """Projected monetary financial savings in USD per month."""

    is_completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    """Boolean flag indicating whether the user has adopted this recommendation."""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    """Timestamp indicating when the recommendation was generated."""

    def to_dict(self) -> dict:
        """Serializes recommendation record fields to dictionary mapping."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "expected_reduction": self.expected_reduction,
            "estimated_savings": self.estimated_savings,
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat()
        }


class Challenge(db.Model):
    """Seeded sustainability challenge definition model representation."""
    __tablename__ = 'challenges'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """Unique auto-incrementing identifier for the challenge."""

    title = db.Column(db.String(255), nullable=False, unique=True)
    """Unique name title of the sustainability challenge."""

    description = db.Column(db.String(1000), nullable=False)
    """Detailed prompt, rules, and guidelines for completing this challenge."""

    difficulty = db.Column(db.String(50), nullable=False)
    """Assigned completion difficulty (Beginner, Intermediate, Advanced, Expert)."""

    points = db.Column(db.Integer, default=0, nullable=False)
    """Score points awarded to the user upon successful completion."""

    # Relationships
    progresses = db.relationship("ChallengeProgress", backref="challenge", cascade="all, delete-orphan", lazy=True)

    def to_dict(self) -> dict:
        """Serializes challenge record fields to dictionary mapping."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "points": self.points
        }


class ChallengeProgress(db.Model):
    """User challenge enrollment and tracking progress model representation."""
    __tablename__ = 'challenge_progress'
    
    # Composite Index for optimized lookups (user_id, challenge_id, status)
    __table_args__ = (
        db.Index('idx_progress_lookup', 'user_id', 'challenge_id', 'completion_status'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """Unique auto-incrementing identifier tracking enrollment progress."""

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    """Foreign key relation referencing the user participating in the challenge."""

    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False)
    """Foreign key relation referencing the target sustainability challenge."""

    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    """Timestamp indicating when the user enrolled in the challenge."""

    end_date = db.Column(db.DateTime, nullable=False)
    """Timestamp representing the deadline for completing the challenge."""

    completion_status = db.Column(db.String(50), default="in_progress", nullable=False)
    """Current completion state (in_progress, completed, or failed)."""

    points_earned = db.Column(db.Integer, default=0, nullable=False)
    """Number of reward points awarded (only non-zero if status is completed)."""

    proof_text = db.Column(db.String(1000), nullable=True)
    """Textual statement/description submitted by the user verifying compliance."""

    def to_dict(self) -> dict:
        """Serializes progress record fields to dictionary mapping."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "challenge_id": self.challenge_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "completion_status": self.completion_status,
            "points_earned": self.points_earned,
            "proof_text": self.proof_text,
            "challenge": self.challenge.to_dict() if self.challenge else None
        }


class RecommendationCache(db.Model):
    """API recommendations cache for carbon footprint query hashes."""
    __tablename__ = 'recommendation_caches'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """Unique auto-incrementing identifier for the cached recommendation payload."""

    footprint_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    """SHA-256 hash of the lifestyle questionnaire metrics matching this cache."""

    recommendations_json = db.Column(db.Text, nullable=False)
    """Serialized JSON string mapping the generated recommendation response."""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    """Timestamp indicating when this cached entry was recorded."""

    def to_dict(self) -> dict:
        """Serializes cache record fields to dictionary mapping."""
        return {
            "id": self.id,
            "footprint_hash": self.footprint_hash,
            "recommendations_json": self.recommendations_json,
            "created_at": self.created_at.isoformat()
        }
