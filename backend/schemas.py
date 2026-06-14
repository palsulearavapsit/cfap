from typing import Any, Dict

from backend.constants import (
    LIMIT_AC_HOURS,
    LIMIT_APPLIANCE_HOURS,
    LIMIT_BIKE_KM,
    LIMIT_CAR_KM,
    LIMIT_CLOTHING_ITEMS,
    LIMIT_ELECTRICITY,
    LIMIT_ELECTRONICS_DEVICES,
    LIMIT_FLIGHT_KM,
    LIMIT_PUBLIC_KM,
)
from backend.enums import DietPreference, PlasticWasteLevel, RecyclingFrequency
from backend.exceptions import ValidationError


class CalculatorInputSchema:
    """Schema validator class for carbon calculator questionnaire fields."""

    NUMERIC_FIELDS = [
        "transportation_car",
        "transportation_bike",
        "transportation_public",
        "transportation_flights",
        "energy_electricity",
        "energy_ac",
        "energy_appliance",
        "shopping_clothing",
        "shopping_electronics",
    ]

    LIMITS = {
        "transportation_car": LIMIT_CAR_KM,
        "transportation_bike": LIMIT_BIKE_KM,
        "transportation_public": LIMIT_PUBLIC_KM,
        "transportation_flights": LIMIT_FLIGHT_KM,
        "energy_electricity": LIMIT_ELECTRICITY,
        "energy_ac": LIMIT_AC_HOURS,
        "energy_appliance": LIMIT_APPLIANCE_HOURS,
        "shopping_clothing": LIMIT_CLOTHING_ITEMS,
        "shopping_electronics": LIMIT_ELECTRONICS_DEVICES,
    }

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validates incoming questionnaire parameters and returns normalized variables."""
        validated: Dict[str, Any] = {}
        for field in cls.NUMERIC_FIELDS:
            val = data.get(field)
            if val is not None:
                if isinstance(val, (list, dict)) or type(val) is bool:
                    raise ValidationError(f"{field} must be a valid numeric value")
                try:
                    float_val = float(val)
                    if float_val < 0:
                        raise ValidationError(f"{field} must be a non-negative value")
                    max_limit = cls.LIMITS.get(field, 100000.0)
                    if float_val > max_limit:
                        raise ValidationError(
                            f"{field} exceeds maximum allowed value of {max_limit}"
                        )
                    validated[field] = float_val
                except (ValueError, TypeError):
                    raise ValidationError(f"{field} must be a valid numeric value")
            else:
                validated[field] = 0.0

        # Validate categorical inputs using Enums
        food_preference_raw = data.get("food_preference", "non-vegetarian")
        waste_recycling_raw = data.get("waste_recycling", "sometimes")
        waste_plastic_raw = data.get("waste_plastic", "average")

        if (
            not isinstance(food_preference_raw, str)
            or not isinstance(waste_recycling_raw, str)
            or not isinstance(waste_plastic_raw, str)
        ):
            raise ValidationError("Categorical inputs must be string types")

        food_pref = food_preference_raw.lower().strip()
        if food_pref not in [e.value for e in DietPreference]:
            raise ValidationError("Invalid food_preference option")
        validated["food_preference"] = food_pref

        waste_rec = waste_recycling_raw.lower().strip()
        if waste_rec not in [e.value for e in RecyclingFrequency]:
            raise ValidationError("Invalid waste_recycling option")
        validated["waste_recycling"] = waste_rec

        waste_plas = waste_plastic_raw.lower().strip()
        if waste_plas not in [e.value for e in PlasticWasteLevel]:
            raise ValidationError("Invalid waste_plastic option")
        validated["waste_plastic"] = waste_plas

        return validated
