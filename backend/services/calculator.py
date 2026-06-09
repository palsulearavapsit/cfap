from typing import Dict, Any
from backend.schemas.schemas import CarbonEntryCreate

# Emission factors (kg CO2 per unit)
CAR_FACTOR = 0.171        # per km
BIKE_FACTOR = 0.005       # per km
PUBLIC_FACTOR = 0.041     # per km
FLIGHT_FACTOR = 0.115     # per km

ELECTRICITY_FACTOR = 0.45  # per kWh
AC_KW = 1.5               # Average AC power draw in kW
APPLIANCE_KW = 0.5        # Average appliance power draw in kW

FOOD_FACTORS = {
    "vegan": 100.0,       # kg CO2/month
    "vegetarian": 150.0,
    "non-vegetarian": 300.0
}

CLOTHING_FACTOR = 15.0    # kg CO2/item
ELECTRONICS_FACTOR = 80.0  # kg CO2/item

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

def calculate_emissions(entry: CarbonEntryCreate) -> Dict[str, Any]:
    # 1. Transportation
    transport_car = entry.transportation_car * CAR_FACTOR
    transport_bike = entry.transportation_bike * BIKE_FACTOR
    transport_public = entry.transportation_public * PUBLIC_FACTOR
    transport_flights = entry.transportation_flights * FLIGHT_FACTOR
    transport_total = transport_car + transport_bike + transport_public + transport_flights

    # 2. Energy
    energy_electricity = entry.energy_electricity * ELECTRICITY_FACTOR
    energy_ac = entry.energy_ac * AC_KW * ELECTRICITY_FACTOR
    energy_appliance = entry.energy_appliance * APPLIANCE_KW * ELECTRICITY_FACTOR
    energy_total = energy_electricity + energy_ac + energy_appliance

    # 3. Food
    food_total = FOOD_FACTORS.get(entry.food_preference.lower(), 300.0)

    # 4. Shopping
    shopping_clothing = entry.shopping_clothing * CLOTHING_FACTOR
    shopping_electronics = entry.shopping_electronics * ELECTRONICS_FACTOR
    shopping_total = shopping_clothing + shopping_electronics

    # 5. Waste
    waste_recycling = RECYCLING_FACTORS.get(entry.waste_recycling.lower(), 30.0)
    waste_plastic = PLASTIC_FACTORS.get(entry.waste_plastic.lower(), 25.0)
    waste_total = waste_recycling + waste_plastic

    # 6. Total
    total = transport_total + energy_total + food_total + shopping_total + waste_total

    # Percentages
    if total > 0:
        transport_pct = (transport_total / total) * 100
        energy_pct = (energy_total / total) * 100
        food_pct = (food_total / total) * 100
        shopping_pct = (shopping_total / total) * 100
        waste_pct = (waste_total / total) * 100
    else:
        transport_pct = energy_pct = food_pct = shopping_pct = waste_pct = 0.0

    return {
        "total_emissions": round(total, 2),
        "breakdown": {
            "transportation": round(transport_total, 2),
            "energy": round(energy_total, 2),
            "food": round(food_total, 2),
            "shopping": round(shopping_total, 2),
            "waste": round(waste_total, 2),
        },
        "percentages": {
            "transportation": round(transport_pct, 1),
            "energy": round(energy_pct, 1),
            "food": round(food_pct, 1),
            "shopping": round(shopping_pct, 1),
            "waste": round(waste_pct, 1),
        }
    }
