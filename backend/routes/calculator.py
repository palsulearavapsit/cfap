from flask import Blueprint, request, jsonify, Response
import hashlib
import json
from backend.models import db, CarbonEntry, Recommendation, RecommendationCache
from backend.routes.auth import login_required
from backend.services.gemini_service import generate_recommendations_gemini
from backend.constants import (
    CAR_FACTOR, BIKE_FACTOR, PUBLIC_FACTOR, FLIGHT_FACTOR,
    ELECTRICITY_FACTOR, AC_KW, APPLIANCE_KW, FOOD_FACTORS,
    CLOTHING_FACTOR, ELECTRONICS_FACTOR, RECYCLING_FACTORS, PLASTIC_FACTORS
)
from typing import Any

calculator_bp = Blueprint('calculator', __name__, url_prefix='/calculator')

def calculate_emissions(data: dict) -> float:
    """Calculates carbon emissions in kg CO2/month based on lifestyle data."""
    # 1. Transportation
    transport_car: float = float(data.get("transportation_car", 0)) * CAR_FACTOR
    transport_bike: float = float(data.get("transportation_bike", 0)) * BIKE_FACTOR
    transport_public: float = float(data.get("transportation_public", 0)) * PUBLIC_FACTOR
    transport_flights: float = float(data.get("transportation_flights", 0)) * FLIGHT_FACTOR
    transport_total: float = transport_car + transport_bike + transport_public + transport_flights

    # 2. Energy
    energy_electricity: float = float(data.get("energy_electricity", 0)) * ELECTRICITY_FACTOR
    energy_ac: float = float(data.get("energy_ac", 0)) * AC_KW * ELECTRICITY_FACTOR
    energy_appliance: float = float(data.get("energy_appliance", 0)) * APPLIANCE_KW * ELECTRICITY_FACTOR
    energy_total: float = energy_electricity + energy_ac + energy_appliance

    # 3. Food
    food_total: float = FOOD_FACTORS.get(str(data.get("food_preference", "non-vegetarian")).lower(), 300.0)

    # 4. Shopping
    shopping_clothing: float = float(data.get("shopping_clothing", 0)) * CLOTHING_FACTOR
    shopping_electronics: float = float(data.get("shopping_electronics", 0)) * ELECTRONICS_FACTOR
    shopping_total: float = shopping_clothing + shopping_electronics

    # 5. Waste
    waste_recycling: float = RECYCLING_FACTORS.get(str(data.get("waste_recycling", "sometimes")).lower(), 30.0)
    waste_plastic: float = PLASTIC_FACTORS.get(str(data.get("waste_plastic", "average")).lower(), 25.0)
    waste_total: float = waste_recycling + waste_plastic

    # 6. Total
    total: float = transport_total + energy_total + food_total + shopping_total + waste_total
    return round(total, 2)

@calculator_bp.route('/submit', methods=['POST'])
@login_required
def submit_calculator() -> Response:
    """Submits monthly lifestyle survey responses, calculating emissions and recommendations."""
    user = request.current_user # type: ignore
    data: dict = request.get_json() or {}

    # 1. Validate numeric inputs (Security/Robustness)
    numeric_fields = [
        "transportation_car", "transportation_bike", "transportation_public", "transportation_flights",
        "energy_electricity", "energy_ac", "energy_appliance",
        "shopping_clothing", "shopping_electronics"
    ]
    for field in numeric_fields:
        val: Any = data.get(field)
        if val is not None:
            # Action 6: Enforce strict scalar type checking (reject boolean, list, dict)
            if isinstance(val, (list, dict)) or type(val) is bool:
                return jsonify({"detail": f"{field} must be a valid numeric value"}), 400
            try:
                float_val: float = float(val)
                if float_val < 0:
                    return jsonify({"detail": f"{field} must be a non-negative value"}), 400
            except (ValueError, TypeError):
                return jsonify({"detail": f"{field} must be a valid numeric value"}), 400

    # 2. Validate categorical inputs (Security/Robustness)
    food_preference_raw: Any = data.get("food_preference", "non-vegetarian")
    waste_recycling_raw: Any = data.get("waste_recycling", "sometimes")
    waste_plastic_raw: Any = data.get("waste_plastic", "average")

    if not isinstance(food_preference_raw, str) or not isinstance(waste_recycling_raw, str) or not isinstance(waste_plastic_raw, str):
        return jsonify({"detail": "Categorical inputs must be string types"}), 400

    food_preference: str = str(food_preference_raw).lower()
    if food_preference not in ["vegan", "vegetarian", "non-vegetarian"]:
        return jsonify({"detail": "Invalid food_preference option"}), 400

    waste_recycling: str = str(waste_recycling_raw).lower()
    if waste_recycling not in ["rarely", "sometimes", "always"]:
        return jsonify({"detail": "Invalid waste_recycling option"}), 400

    waste_plastic: str = str(waste_plastic_raw).lower()
    if waste_plastic not in ["low", "average", "high"]:
        return jsonify({"detail": "Invalid waste_plastic option"}), 400

    # Update data dictionary with normalized strings to ensure consistency
    data["food_preference"] = food_preference
    data["waste_recycling"] = waste_recycling
    data["waste_plastic"] = waste_plastic

    total_emissions: float = calculate_emissions(data)

    try:
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
            food_preference=food_preference,
            shopping_clothing=float(data.get("shopping_clothing", 0)),
            shopping_electronics=float(data.get("shopping_electronics", 0)),
            waste_recycling=waste_recycling,
            waste_plastic=waste_plastic,
            total_emissions=total_emissions
        )
        db.session.add(new_entry)

        # Delete previous INCOMPLETE recommendations
        Recommendation.query.filter_by(user_id=user.id, is_completed=False).delete()

        # Action 7: Calculate footprint hash & check cached recommendations to optimize Gemini cost
        hash_data = {
            "transportation_car": float(data.get("transportation_car", 0)),
            "transportation_bike": float(data.get("transportation_bike", 0)),
            "transportation_public": float(data.get("transportation_public", 0)),
            "transportation_flights": float(data.get("transportation_flights", 0)),
            "energy_electricity": float(data.get("energy_electricity", 0)),
            "energy_ac": float(data.get("energy_ac", 0)),
            "energy_appliance": float(data.get("energy_appliance", 0)),
            "food_preference": food_preference,
            "shopping_clothing": float(data.get("shopping_clothing", 0)),
            "shopping_electronics": float(data.get("shopping_electronics", 0)),
            "waste_recycling": waste_recycling,
            "waste_plastic": waste_plastic
        }
        hash_str: str = json.dumps(hash_data, sort_keys=True)
        footprint_hash: str = hashlib.sha256(hash_str.encode('utf-8')).hexdigest()

        cached_rec_record = RecommendationCache.query.filter_by(footprint_hash=footprint_hash).first()
        
        if cached_rec_record:
            recommendations_list = json.loads(cached_rec_record.recommendations_json)
        else:
            recommendations_list = generate_recommendations_gemini(data)
            # Save new suggestions block to cache
            new_cache = RecommendationCache(
                footprint_hash=footprint_hash,
                recommendations_json=json.dumps(recommendations_list)
            )
            db.session.add(new_cache)
        
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

        # Action 3: Return entry serialized data using to_dict() model representation
        return jsonify(new_entry.to_dict()), 201

    except Exception as db_err:
        db.session.rollback()
        return jsonify({"detail": f"Database operation failed: {str(db_err)}"}), 500
