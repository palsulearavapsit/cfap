from flask import Blueprint, request, jsonify
from backend.models import db, CarbonEntry, Recommendation
from backend.routes.auth import login_required
from backend.services.gemini_service import generate_recommendations_gemini

calculator_bp = Blueprint('calculator', __name__, url_prefix='/calculator')

# Emission factors (kg CO2 per unit)
CAR_FACTOR = 0.171
BIKE_FACTOR = 0.005
PUBLIC_FACTOR = 0.041
FLIGHT_FACTOR = 0.115

ELECTRICITY_FACTOR = 0.45
AC_KW = 1.5
APPLIANCE_KW = 0.5

FOOD_FACTORS = {
    "vegan": 100.0,
    "vegetarian": 150.0,
    "non-vegetarian": 300.0
}

CLOTHING_FACTOR = 15.0
ELECTRONICS_FACTOR = 80.0

RECYCLING_FACTORS = {
    "rarely": 50.0,
    "sometimes": 30.0,
    "always": 10.0
}

PLASTIC_FACTORS = {
    "low": 10.0,
    "average": 25.0,
    "high": 50.0
}

def calculate_emissions(data: dict) -> float:
    # 1. Transportation
    transport_car = float(data.get("transportation_car", 0)) * CAR_FACTOR
    transport_bike = float(data.get("transportation_bike", 0)) * BIKE_FACTOR
    transport_public = float(data.get("transportation_public", 0)) * PUBLIC_FACTOR
    transport_flights = float(data.get("transportation_flights", 0)) * FLIGHT_FACTOR
    transport_total = transport_car + transport_bike + transport_public + transport_flights

    # 2. Energy
    energy_electricity = float(data.get("energy_electricity", 0)) * ELECTRICITY_FACTOR
    energy_ac = float(data.get("energy_ac", 0)) * AC_KW * ELECTRICITY_FACTOR
    energy_appliance = float(data.get("energy_appliance", 0)) * APPLIANCE_KW * ELECTRICITY_FACTOR
    energy_total = energy_electricity + energy_ac + energy_appliance

    # 3. Food
    food_total = FOOD_FACTORS.get(str(data.get("food_preference", "non-vegetarian")).lower(), 300.0)

    # 4. Shopping
    shopping_clothing = float(data.get("shopping_clothing", 0)) * CLOTHING_FACTOR
    shopping_electronics = float(data.get("shopping_electronics", 0)) * ELECTRONICS_FACTOR
    shopping_total = shopping_clothing + shopping_electronics

    # 5. Waste
    waste_recycling = RECYCLING_FACTORS.get(str(data.get("waste_recycling", "sometimes")).lower(), 30.0)
    waste_plastic = PLASTIC_FACTORS.get(str(data.get("waste_plastic", "average")).lower(), 25.0)
    waste_total = waste_recycling + waste_plastic

    # 6. Total
    total = transport_total + energy_total + food_total + shopping_total + waste_total
    return round(total, 2)

@calculator_bp.route('/submit', methods=['POST'])
@login_required
def submit_calculator():
    user = request.current_user
    data = request.get_json() or {}

    total_emissions = calculate_emissions(data)

    # Save carbon entry to database
    new_entry = CarbonEntry(
        user_id=user.id,
        transportation_car=float(data.get("transportation_car", 0)),
        transportation_bike=float(data.get("transportation_bike", 0)),
        transportation_public=float(data.get("transportation_public", 0)),
        transportation_flights=float(data.get("transportation_flights", 0)),
        energy_electricity=float(data.get("energy_electricity", 0)),
        energy_ac=float(data.get("energy_ac", 0)),
        energy_appliance=float(data.get("energy_appliance", 0)),
        food_preference=str(data.get("food_preference", "non-vegetarian")),
        shopping_clothing=float(data.get("shopping_clothing", 0)),
        shopping_electronics=float(data.get("shopping_electronics", 0)),
        waste_recycling=str(data.get("waste_recycling", "sometimes")),
        waste_plastic=str(data.get("waste_plastic", "average")),
        total_emissions=total_emissions
    )
    
    db.session.add(new_entry)
    db.session.commit()

    # Delete previous INCOMPLETE recommendations
    Recommendation.query.filter_by(user_id=user.id, is_completed=False).delete()

    # Generate custom recommendations (calls Gemini API with rule-based fallback)
    recommendations_list = generate_recommendations_gemini(data)
    
    for rec in recommendations_list:
        db_rec = Recommendation(
            user_id=user.id,
            title=rec["title"],
            description=rec["description"],
            difficulty=rec["difficulty"],
            expected_reduction=rec["expected_reduction"],
            estimated_savings=rec["estimated_savings"],
            is_completed=False
        )
        db.session.add(db_rec)
    
    db.session.commit()

    return jsonify({
        "id": new_entry.id,
        "user_id": new_entry.user_id,
        "total_emissions": new_entry.total_emissions,
        "created_at": new_entry.created_at.isoformat()
    }), 201
