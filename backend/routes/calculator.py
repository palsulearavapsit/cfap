import hashlib
import json
import logging
from typing import Any

from flask import Blueprint, Response, request

from backend.constants import (
    AC_KW,
    APPLIANCE_KW,
    BIKE_FACTOR,
    CAR_FACTOR,
    CLOTHING_FACTOR,
    ELECTRICITY_FACTOR,
    ELECTRONICS_FACTOR,
    FLIGHT_FACTOR,
    FOOD_FACTORS,
    LIMIT_AC_HOURS,
    LIMIT_APPLIANCE_HOURS,
    LIMIT_BIKE_KM,
    LIMIT_CAR_KM,
    LIMIT_CLOTHING_ITEMS,
    LIMIT_ELECTRICITY,
    LIMIT_ELECTRONICS_DEVICES,
    LIMIT_FLIGHT_KM,
    LIMIT_PUBLIC_KM,
    PLASTIC_FACTORS,
    PUBLIC_FACTOR,
    RECYCLING_FACTORS,
)
from backend.enums import DietPreference, PlasticWasteLevel, RecyclingFrequency
from backend.exceptions import ValidationError
from backend.models import CarbonEntry, Recommendation, RecommendationCache, db
from backend.routes.auth import login_required
from backend.services.calculation_service import CalculationService
from backend.services.gemini_service import generate_recommendations_gemini
from backend.utils import send_response

logger = logging.getLogger("ecotrack.calculator")

calculator_bp = Blueprint("calculator", __name__, url_prefix="/calculator")


@calculator_bp.route("/submit", methods=["POST"])
@login_required
def submit_calculator() -> Response:
    """Submits monthly lifestyle survey responses, calculating emissions and recommendations."""
    user = request.current_user  # type: ignore
    data: dict = request.get_json() or {}

    from backend.schemas import CalculatorInputSchema

    validated_data = CalculatorInputSchema.validate(data)

    total_emissions: float = CalculationService.calculate_emissions(validated_data)

    try:
        # Save carbon entry to database
        new_entry = CarbonEntry(
            user_id=user.id,
            transportation_car=validated_data["transportation_car"],
            transportation_bike=validated_data["transportation_bike"],
            transportation_public=validated_data["transportation_public"],
            transportation_flights=validated_data["transportation_flights"],
            energy_electricity=validated_data["energy_electricity"],
            energy_ac=validated_data["energy_ac"],
            energy_appliance=validated_data["energy_appliance"],
            food_preference=validated_data["food_preference"],
            shopping_clothing=validated_data["shopping_clothing"],
            shopping_electronics=validated_data["shopping_electronics"],
            waste_recycling=validated_data["waste_recycling"],
            waste_plastic=validated_data["waste_plastic"],
            total_emissions=total_emissions,
        )
        db.session.add(new_entry)

        # Delete previous INCOMPLETE recommendations
        Recommendation.query.filter_by(user_id=user.id, is_completed=False).delete()

        # Action 7: Calculate footprint hash & check cached recommendations to optimize Gemini cost
        hash_data = {
            "transportation_car": validated_data["transportation_car"],
            "transportation_bike": validated_data["transportation_bike"],
            "transportation_public": validated_data["transportation_public"],
            "transportation_flights": validated_data["transportation_flights"],
            "energy_electricity": validated_data["energy_electricity"],
            "energy_ac": validated_data["energy_ac"],
            "energy_appliance": validated_data["energy_appliance"],
            "food_preference": validated_data["food_preference"],
            "shopping_clothing": validated_data["shopping_clothing"],
            "shopping_electronics": validated_data["shopping_electronics"],
            "waste_recycling": validated_data["waste_recycling"],
            "waste_plastic": validated_data["waste_plastic"],
        }
        hash_str: str = json.dumps(hash_data, sort_keys=True)
        footprint_hash: str = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

        cached_rec_record = RecommendationCache.query.filter_by(
            footprint_hash=footprint_hash
        ).first()

        if cached_rec_record:
            recommendations_list = json.loads(cached_rec_record.recommendations_json)
        else:
            recommendations_list = generate_recommendations_gemini(validated_data)
            # Save new suggestions block to cache
            new_cache = RecommendationCache(
                footprint_hash=footprint_hash,
                recommendations_json=json.dumps(recommendations_list),
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
                is_completed=False,
            )
            db.session.add(db_rec)

        db.session.commit()

        # Action 3: Return entry serialized data using to_dict() model representation
        return send_response(new_entry.to_dict(), 201)

    except Exception as db_err:
        db.session.rollback()
        logger.error(f"Calculator database commit failed: {str(db_err)}", exc_info=True)
        return send_response(
            {"detail": "Database operation failed. Please try again later."}, 500
        )
