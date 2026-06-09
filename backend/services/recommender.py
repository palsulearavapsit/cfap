from sqlalchemy.orm import Session
from backend.models.models import Recommendation, CarbonEntry
from typing import List

def generate_recommendations(db: Session, user_id: int, entry: CarbonEntry) -> List[Recommendation]:
    # Delete previous recommendations that are NOT completed to keep dashboard clean and relevant
    db.query(Recommendation).filter(
        Recommendation.user_id == user_id,
        Recommendation.is_completed == False
    ).delete()
    
    recommendations_to_add = []

    # 1. Transportation Recommendations
    # Calculate car + flights emissions
    car_emissions = entry.transportation_car * 0.171
    flights_emissions = entry.transportation_flights * 0.115
    public_emissions = entry.transportation_public * 0.041
    
    if car_emissions > 100 or flights_emissions > 150:
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Switch to Public Transit",
                description="Replace 50% of your solo car drives with bus or train commutes. Public transit significantly cuts per-passenger emissions.",
                difficulty="Intermediate",
                expected_reduction=65.0, # kg CO2 / month
                estimated_savings=50.0,   # USD / month
                is_completed=False
            )
        )
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Active Commuting (Cycling/Walking)",
                description="Cycle or walk for short trips under 5km. It has zero emissions and improves cardiovascular health.",
                difficulty="Beginner",
                expected_reduction=35.0,
                estimated_savings=20.0,
                is_completed=False
            )
        )
    if flights_emissions > 200:
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Offset Flight Emissions & Reduce Trips",
                description="Combine business trips or opt for high-speed rail instead of short-haul flights. Purchase gold-standard carbon offsets for necessary flights.",
                difficulty="Advanced",
                expected_reduction=120.0,
                estimated_savings=150.0,
                is_completed=False
            )
        )

    # 2. Energy Recommendations
    elec_emissions = entry.energy_electricity * 0.45
    ac_emissions = entry.energy_ac * 1.5 * 0.45
    
    if elec_emissions > 80:
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Upgrade to LED Lighting",
                description="Replace all incandescent bulbs with ENERGY STAR certified LEDs. They use up to 75% less energy and last 25x longer.",
                difficulty="Beginner",
                expected_reduction=12.0,
                estimated_savings=8.0,
                is_completed=False
            )
        )
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Smart Thermostat & Efficient Appliances",
                description="Install a smart programmable thermostat and unplug idle electronics. Ensure new appliances are rated A+++ or ENERGY STAR.",
                difficulty="Intermediate",
                expected_reduction=40.0,
                estimated_savings=25.0,
                is_completed=False
            )
        )
    if ac_emissions > 50:
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Reduce AC Usage & Thermostat Settings",
                description="Set your AC to 24-26°C (75-78°F) rather than lower. Use ceiling fans to circulate air and close blinds during peak sunlight.",
                difficulty="Beginner",
                expected_reduction=25.0,
                estimated_savings=18.0,
                is_completed=False
            )
        )

    # 3. Food Recommendations
    if entry.food_preference.lower() == "non-vegetarian":
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Integrate Meat-Free Days",
                description="Try replacing red meat and dairy with plant-based alternatives on select days (e.g., Meat-Free Mondays). Raising livestock generates massive methane emissions.",
                difficulty="Beginner",
                expected_reduction=45.0,
                estimated_savings=30.0,
                is_completed=False
            )
        )
    elif entry.food_preference.lower() == "vegetarian":
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Transition towards Plant-Based Diet",
                description="Reduce cheese, butter, and milk consumption. Source foods locally to reduce food miles and packaging waste.",
                difficulty="Intermediate",
                expected_reduction=15.0,
                estimated_savings=10.0,
                is_completed=False
            )
        )

    # 4. Shopping Recommendations
    clothing_emissions = entry.shopping_clothing * 15.0
    electronics_emissions = entry.shopping_electronics * 80.0
    
    if clothing_emissions > 30:
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Choose Sustainable & Second-Hand Fashion",
                description="Avoid fast fashion. Buy high-quality, durable garments or explore thrift stores. Extend your clothes' lifetime by washing at lower temperatures.",
                difficulty="Beginner",
                expected_reduction=20.0,
                estimated_savings=40.0,
                is_completed=False
            )
        )
    if electronics_emissions > 70:
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Extend Electronics Lifecycle & Repair",
                description="Instead of upgrading devices yearly, repair existing ones and buy refurbished electronics when replacement is necessary. Recycle old devices safely.",
                difficulty="Intermediate",
                expected_reduction=75.0,
                estimated_savings=120.0,
                is_completed=False
            )
        )

    # 5. Waste Recommendations
    if entry.waste_recycling.lower() == "rarely":
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Set Up Household Recycling Station",
                description="Separate paper, cardboard, glass, and metal from general landfill waste. Check local guidelines for recyclable plastics.",
                difficulty="Beginner",
                expected_reduction=15.0,
                estimated_savings=0.0,
                is_completed=False
            )
        )
    if entry.waste_plastic.lower() in ["average", "high"]:
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Adopt Zero-Waste Shopping Habits",
                description="Carry reusable canvas bags, purchase items in bulk, and refuse single-use plastic water bottles. Bring containers for bulk food.",
                difficulty="Beginner",
                expected_reduction=10.0,
                estimated_savings=15.0,
                is_completed=False
            )
        )

    # If no specific triggers, add generic high-value items
    if not recommendations_to_add:
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Compost Organic Waste",
                description="Start composting your kitchen scraps and garden clippings. This prevents organic matter from producing methane in landfills.",
                difficulty="Intermediate",
                expected_reduction=12.0,
                estimated_savings=5.0,
                is_completed=False
            )
        )
        recommendations_to_add.append(
            Recommendation(
                user_id=user_id,
                title="Mindful Consumption Check",
                description="Before making any purchase, wait 48 hours to determine if it is a necessity or impulse buy.",
                difficulty="Beginner",
                expected_reduction=15.0,
                estimated_savings=50.0,
                is_completed=False
            )
        )

    db.add_all(recommendations_to_add)
    db.commit()
    return recommendations_to_add
