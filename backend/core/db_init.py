import datetime
from backend.core.db import engine, SessionLocal
from backend.core.security import get_password_hash
from backend.models.models import Base, User, CarbonEntry, Recommendation, Challenge, ChallengeProgress

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Pre-seed challenges if they don't exist
        if db.query(Challenge).count() == 0:
            challenges = [
                Challenge(
                    id=1,
                    title="No Plastic Day",
                    description="Avoid single-use plastics for an entire day.",
                    difficulty="Beginner",
                    points=50
                ),
                Challenge(
                    id=2,
                    title="Meat-Free Monday",
                    description="Eat only plant-based meals today.",
                    difficulty="Intermediate",
                    points=100
                ),
                Challenge(
                    id=3,
                    title="Public Transport Week",
                    description="Commute using only public transit or active transit (walk/bike) for 5 days.",
                    difficulty="Advanced",
                    points=250
                ),
                Challenge(
                    id=4,
                    title="Zero Waste Weekend",
                    description="Generate absolutely zero landfill waste from Friday night to Monday morning.",
                    difficulty="Expert",
                    points=500
                )
            ]
            db.add_all(challenges)
            db.commit()
            print("Pre-seeded default challenges.")
            
        # 2. Pre-seed demo user if doesn't exist
        demo_email = "demo@ecotrack.ai"
        demo_user = db.query(User).filter(User.email == demo_email).first()
        if not demo_user:
            # Create demo user
            hashed_pwd = get_password_hash("demouser123")
            demo_user = User(email=demo_email, password_hash=hashed_pwd)
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print("Created demo user.")
            
            # Seed 3 months of carbon entries history
            now = datetime.datetime.utcnow()
            
            # Month 1: 60 days ago (high footprint)
            entry1 = CarbonEntry(
                user_id=demo_user.id,
                transportation_car=1200.0,
                transportation_bike=0.0,
                transportation_public=0.0,
                transportation_flights=2000.0,
                energy_electricity=450.0,
                energy_ac=120.0,
                energy_appliance=40.0,
                food_preference="non-vegetarian",
                shopping_clothing=8.0,
                shopping_electronics=3.0,
                waste_recycling="rarely",
                waste_plastic="high",
                total_emissions=980.50,
                created_at=now - datetime.timedelta(days=60)
            )
            
            # Month 2: 30 days ago (moderate footprint)
            entry2 = CarbonEntry(
                user_id=demo_user.id,
                transportation_car=700.0,
                transportation_bike=30.0,
                transportation_public=150.0,
                transportation_flights=0.0,
                energy_electricity=300.0,
                energy_ac=60.0,
                energy_appliance=25.0,
                food_preference="vegetarian",
                shopping_clothing=3.0,
                shopping_electronics=0.0,
                waste_recycling="sometimes",
                waste_plastic="average",
                total_emissions=495.20,
                created_at=now - datetime.timedelta(days=30)
            )
            
            # Month 3: Current (low footprint)
            entry3 = CarbonEntry(
                user_id=demo_user.id,
                transportation_car=250.0,
                transportation_bike=120.0,
                transportation_public=300.0,
                transportation_flights=0.0,
                energy_electricity=150.0,
                energy_ac=15.0,
                energy_appliance=15.0,
                food_preference="vegan",
                shopping_clothing=1.0,
                shopping_electronics=0.0,
                waste_recycling="always",
                waste_plastic="low",
                total_emissions=215.40,
                created_at=now
            )
            
            db.add_all([entry1, entry2, entry3])
            db.commit()
            print("Seeded carbon history entries for demo user.")

            # Seed recommendations
            rec1 = Recommendation(
                user_id=demo_user.id,
                title="Upgrade to LED Lighting",
                description="Replace all incandescent bulbs with ENERGY STAR certified LEDs. They use up to 75% less energy and last 25x longer.",
                difficulty="Beginner",
                expected_reduction=12.0,
                estimated_savings=8.0,
                is_completed=True,
                created_at=now - datetime.timedelta(days=3)
            )
            rec2 = Recommendation(
                user_id=demo_user.id,
                title="Switch to Public Transit",
                description="Replace 50% of your solo car drives with bus or train commutes. Public transit significantly cuts per-passenger emissions.",
                difficulty="Intermediate",
                expected_reduction=65.0,
                estimated_savings=50.0,
                is_completed=False,
                created_at=now
            )
            rec3 = Recommendation(
                user_id=demo_user.id,
                title="Integrate Meat-Free Days",
                description="Try replacing red meat and dairy with plant-based alternatives on select days (e.g., Meat-Free Mondays).",
                difficulty="Beginner",
                expected_reduction=45.0,
                estimated_savings=30.0,
                is_completed=False,
                created_at=now
            )
            
            db.add_all([rec1, rec2, rec3])
            db.commit()
            print("Seeded recommendations for demo user.")
            
            # Seed challenge progress
            # Completed: No Plastic Day
            prog1 = ChallengeProgress(
                user_id=demo_user.id,
                challenge_id=1,
                start_date=now - datetime.timedelta(days=10),
                end_date=now - datetime.timedelta(days=3),
                completion_status="completed",
                points_earned=50
            )
            # In progress: Meat-Free Monday
            prog2 = ChallengeProgress(
                user_id=demo_user.id,
                challenge_id=2,
                start_date=now - datetime.timedelta(days=1),
                end_date=now + datetime.timedelta(days=6),
                completion_status="in_progress",
                points_earned=0
            )
            
            db.add_all([prog1, prog2])
            db.commit()
            print("Seeded challenge progress for demo user.")
            
    except Exception as e:
        print("Error pre-seeding database elements:", e)
        db.rollback()
    finally:
        db.close()
