from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User profile database model representation."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Inputs
    transportation_car = db.Column(db.Float, default=0.0, nullable=False)
    transportation_bike = db.Column(db.Float, default=0.0, nullable=False)
    transportation_public = db.Column(db.Float, default=0.0, nullable=False)
    transportation_flights = db.Column(db.Float, default=0.0, nullable=False)
    
    energy_electricity = db.Column(db.Float, default=0.0, nullable=False)
    energy_ac = db.Column(db.Float, default=0.0, nullable=False)
    energy_appliance = db.Column(db.Float, default=0.0, nullable=False)
    
    food_preference = db.Column(db.String(50), default="non-vegetarian", nullable=False)
    
    shopping_clothing = db.Column(db.Float, default=0.0, nullable=False)
    shopping_electronics = db.Column(db.Float, default=0.0, nullable=False)
    
    waste_recycling = db.Column(db.String(50), default="rarely", nullable=False)
    waste_plastic = db.Column(db.String(50), default="average", nullable=False)
    
    # Calculated Output
    total_emissions = db.Column(db.Float, nullable=False) # in kg CO2/month
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False) # Beginner, Intermediate, Advanced, Expert
    expected_reduction = db.Column(db.Float, nullable=False) # kg CO2
    estimated_savings = db.Column(db.Float, nullable=False) # USD
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

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
    title = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(1000), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False) # Beginner, Intermediate, Advanced, Expert
    points = db.Column(db.Integer, default=0, nullable=False)

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    completion_status = db.Column(db.String(50), default="in_progress", nullable=False) # in_progress, completed, failed
    points_earned = db.Column(db.Integer, default=0, nullable=False)
    proof_text = db.Column(db.String(1000), nullable=True)

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
    footprint_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    recommendations_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        """Serializes cache record fields to dictionary mapping."""
        return {
            "id": self.id,
            "footprint_hash": self.footprint_hash,
            "recommendations_json": self.recommendations_json,
            "created_at": self.created_at.isoformat()
        }
