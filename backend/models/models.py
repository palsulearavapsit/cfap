import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    carbon_entries = relationship("CarbonEntry", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    challenge_progresses = relationship("ChallengeProgress", back_populates="user", cascade="all, delete-orphan")


class CarbonEntry(Base):
    __tablename__ = 'carbon_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Inputs
    transportation_car = Column(Float, default=0.0, nullable=False)
    transportation_bike = Column(Float, default=0.0, nullable=False)
    transportation_public = Column(Float, default=0.0, nullable=False)
    transportation_flights = Column(Float, default=0.0, nullable=False)
    
    energy_electricity = Column(Float, default=0.0, nullable=False)
    energy_ac = Column(Float, default=0.0, nullable=False)
    energy_appliance = Column(Float, default=0.0, nullable=False)
    
    food_preference = Column(String(50), default="non-vegetarian", nullable=False)
    
    shopping_clothing = Column(Float, default=0.0, nullable=False)
    shopping_electronics = Column(Float, default=0.0, nullable=False)
    
    waste_recycling = Column(String(50), default="rarely", nullable=False)
    waste_plastic = Column(String(50), default="average", nullable=False)
    
    # Calculated Output
    total_emissions = Column(Float, nullable=False) # in kg CO2/month
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="carbon_entries")

    __table_args__ = (
        Index('idx_carbon_user_created', 'user_id', 'created_at'),
    )


class Recommendation(Base):
    __tablename__ = 'recommendations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=False)
    difficulty = Column(String(50), nullable=False) # Beginner, Intermediate, Advanced, Expert
    expected_reduction = Column(Float, nullable=False) # kg CO2
    estimated_savings = Column(Float, nullable=False) # USD
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="recommendations")

    __table_args__ = (
        Index('idx_recommendation_user_created', 'user_id', 'created_at'),
    )


class Challenge(Base):
    __tablename__ = 'challenges'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, unique=True)
    description = Column(String(1000), nullable=False)
    difficulty = Column(String(50), nullable=False) # Beginner, Intermediate, Advanced, Expert
    points = Column(Integer, default=0, nullable=False)

    # Relationships
    progresses = relationship("ChallengeProgress", back_populates="challenge", cascade="all, delete-orphan")


class ChallengeProgress(Base):
    __tablename__ = 'challenge_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    challenge_id = Column(Integer, ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False)
    start_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=False)
    completion_status = Column(String(50), default="in_progress", nullable=False) # in_progress, completed, failed
    points_earned = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="challenge_progresses")
    challenge = relationship("Challenge", back_populates="progresses")

    __table_args__ = (
        Index('idx_challenge_progress_user', 'user_id'),
        Index('idx_challenge_progress_challenge', 'challenge_id'),
    )
