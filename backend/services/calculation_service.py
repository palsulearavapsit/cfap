from typing import Any, Dict

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
    PLASTIC_FACTORS,
    PUBLIC_FACTOR,
    RECYCLING_FACTORS,
)
from backend.models import ChallengeProgress, Recommendation


class CalculationService:
    """Service to handle carbon emissions and sustainability score calculations."""

    @staticmethod
    def calculate_emissions(data: Dict[str, Any]) -> float:
        """Calculates total carbon emissions in kg CO2/month based on lifestyle data."""
        # 1. Transportation
        transport_car: float = float(data.get("transportation_car", 0)) * CAR_FACTOR
        transport_bike: float = float(data.get("transportation_bike", 0)) * BIKE_FACTOR
        transport_public: float = (
            float(data.get("transportation_public", 0)) * PUBLIC_FACTOR
        )
        transport_flights: float = (
            float(data.get("transportation_flights", 0)) * FLIGHT_FACTOR
        )
        transport_total: float = (
            transport_car + transport_bike + transport_public + transport_flights
        )

        # 2. Energy
        energy_electricity: float = (
            float(data.get("energy_electricity", 0)) * ELECTRICITY_FACTOR
        )
        energy_ac: float = float(data.get("energy_ac", 0)) * AC_KW * ELECTRICITY_FACTOR
        energy_appliance: float = (
            float(data.get("energy_appliance", 0)) * APPLIANCE_KW * ELECTRICITY_FACTOR
        )
        energy_total: float = energy_electricity + energy_ac + energy_appliance

        # 3. Food
        food_total: float = FOOD_FACTORS.get(
            str(data.get("food_preference", "non-vegetarian")).lower(), 300.0
        )

        # 4. Shopping
        shopping_clothing: float = (
            float(data.get("shopping_clothing", 0)) * CLOTHING_FACTOR
        )
        shopping_electronics: float = (
            float(data.get("shopping_electronics", 0)) * ELECTRONICS_FACTOR
        )
        shopping_total: float = shopping_clothing + shopping_electronics

        # 5. Waste
        waste_recycling: float = RECYCLING_FACTORS.get(
            str(data.get("waste_recycling", "sometimes")).lower(), 30.0
        )
        waste_plastic: float = PLASTIC_FACTORS.get(
            str(data.get("waste_plastic", "average")).lower(), 25.0
        )
        waste_total: float = waste_recycling + waste_plastic

        # 6. Total
        total: float = (
            transport_total + energy_total + food_total + shopping_total + waste_total
        )
        return round(total, 2)

    @staticmethod
    def get_category_breakdown(entry: Any) -> Dict[str, Dict[str, float]]:
        """Returns values and percentages breakdown by category for a carbon entry."""
        t_car: float = entry.transportation_car * CAR_FACTOR
        t_bike: float = entry.transportation_bike * BIKE_FACTOR
        t_public: float = entry.transportation_public * PUBLIC_FACTOR
        t_flights: float = entry.transportation_flights * FLIGHT_FACTOR
        transport_total: float = t_car + t_bike + t_public + t_flights

        e_elec: float = entry.energy_electricity * ELECTRICITY_FACTOR
        e_ac: float = entry.energy_ac * AC_KW * ELECTRICITY_FACTOR
        e_app: float = entry.energy_appliance * APPLIANCE_KW * ELECTRICITY_FACTOR
        energy_total: float = e_elec + e_ac + e_app

        food_total: float = FOOD_FACTORS.get(entry.food_preference.lower(), 300.0)
        shopping_total: float = (entry.shopping_clothing * CLOTHING_FACTOR) + (
            entry.shopping_electronics * ELECTRONICS_FACTOR
        )
        waste_total: float = RECYCLING_FACTORS.get(
            entry.waste_recycling.lower(), 30.0
        ) + PLASTIC_FACTORS.get(entry.waste_plastic.lower(), 25.0)

        total: float = (
            transport_total + energy_total + food_total + shopping_total + waste_total
        )

        transport_pct: float = 0.0
        energy_pct: float = 0.0
        food_pct: float = 0.0
        shopping_pct: float = 0.0
        waste_pct: float = 0.0

        if total > 0:
            transport_pct = round((transport_total / total) * 100, 1)
            energy_pct = round((energy_total / total) * 100, 1)
            food_pct = round((food_total / total) * 100, 1)
            shopping_pct = round((shopping_total / total) * 100, 1)
            waste_pct = round((waste_total / total) * 100, 1)

        return {
            "percentages": {
                "transportation": transport_pct,
                "energy": energy_pct,
                "food": food_pct,
                "shopping": shopping_pct,
                "waste": waste_pct,
            },
            "values": {
                "transportation": round(transport_total, 2),
                "energy": round(energy_total, 2),
                "food": round(food_total, 2),
                "shopping": round(shopping_total, 2),
                "waste": round(waste_total, 2),
            },
        }

    @staticmethod
    def calculate_sustainability_score(user_id: int, current_emissions: float) -> int:
        """Calculates sustainability score (10 to 100) based on emissions, challenges, and recommendations."""
        base_score: int = 80
        if current_emissions > 100:
            penalty: int = int((current_emissions - 100) // 10)
            base_score -= penalty

        completed_challenges: int = ChallengeProgress.query.filter_by(
            user_id=user_id, completion_status="completed"
        ).count()
        base_score += completed_challenges * 5

        completed_recs: int = Recommendation.query.filter_by(
            user_id=user_id, is_completed=True
        ).count()
        base_score += completed_recs * 3

        return max(10, min(100, base_score))
