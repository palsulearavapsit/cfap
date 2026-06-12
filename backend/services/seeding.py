import logging

from backend.models import Challenge, db

logger = logging.getLogger("ecotrack.seeding")


def seed_challenges() -> None:
    """Seeds default sustainability challenges if they don't already exist in the database."""
    try:
        # Optimized lookup check using .first()
        if Challenge.query.first() is None:
            challenges = [
                Challenge(
                    id=1,
                    title="No Plastic Day",
                    description="Avoid single-use plastics for an entire day.\n\nRules & Habits:\n1. Carry a reusable water bottle instead of buying bottled beverages.\n2. Bring a reusable cloth tote bag for shopping.\n3. Refuse plastic straws, cutlery, and containers.",
                    difficulty="Beginner",
                    points=50,
                ),
                Challenge(
                    id=2,
                    title="Meat-Free Monday",
                    description="Eat only plant-based meals today.\n\nRules & Habits:\n1. Exclude all meat, poultry, and fish from all meals.\n2. Experiment with dairy-free alternatives like oat or soy milk.\n3. Build satisfying meals around grains, legumes, and fresh vegetables.",
                    difficulty="Intermediate",
                    points=100,
                ),
                Challenge(
                    id=3,
                    title="Public Transport Week",
                    description="Commute using only public transit or active transit (walk/bike) for 5 days.\n\nRules & Habits:\n1. Leave your car at home for your daily commutes.\n2. Walk, run, bicycle, or ride buses, subways, or light rails.\n3. Combine errands to minimize extra trips.",
                    difficulty="Advanced",
                    points=250,
                ),
                Challenge(
                    id=4,
                    title="Zero Waste Weekend",
                    description="Generate absolutely zero landfill waste from Friday night to Monday morning.\n\nRules & Habits:\n1. Avoid buying goods packaged in non-recyclable materials.\n2. Compost all food scraps and organic waste.\n3. Maximize sorting for standard paper, metal, and glass recycling.",
                    difficulty="Expert",
                    points=500,
                ),
            ]
            db.session.bulk_save_objects(challenges)
            db.session.commit()
            import backend.routes.challenges as rc

            rc.challenges_cache = None
            logger.info("Successfully seeded default sustainability challenges.")
    except Exception as err:
        db.session.rollback()
        logger.error(f"Failed to seed challenges: {str(err)}", exc_info=True)
