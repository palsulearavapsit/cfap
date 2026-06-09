from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    carbon_entries = db.relationship("CarbonEntry", backref="user", cascade="all, delete-orphan", lazy=True)
    recommendations = db.relationship("Recommendation", backref="user", cascade="all, delete-orphan", lazy=True)
    challenge_progresses = db.relationship("ChallengeProgress", backref="user", cascade="all, delete-orphan", lazy=True)


class CarbonEntry(db.Model):
    __tablename__ = 'carbon_entries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
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


class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False) # Beginner, Intermediate, Advanced, Expert
    expected_reduction = db.Column(db.Float, nullable=False) # kg CO2
    estimated_savings = db.Column(db.Float, nullable=False) # USD
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Challenge(db.Model):
    __tablename__ = 'challenges'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(1000), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False) # Beginner, Intermediate, Advanced, Expert
    points = db.Column(db.Integer, default=0, nullable=False)

    # Relationships
    progresses = db.relationship("ChallengeProgress", backref="challenge", cascade="all, delete-orphan", lazy=True)


class ChallengeProgress(db.Model):
    __tablename__ = 'challenge_progress'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    completion_status = db.Column(db.String(50), default="in_progress", nullable=False) # in_progress, completed, failed
    points_earned = db.Column(db.Integer, default=0, nullable=False)
