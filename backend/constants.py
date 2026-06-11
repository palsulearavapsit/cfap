# Centralized Carbon Emission Factors and Constants

# Transportation emission factors (kg CO2 per km)
CAR_FACTOR = 0.171
BIKE_FACTOR = 0.005
PUBLIC_FACTOR = 0.041
FLIGHT_FACTOR = 0.115

# Home energy emission factors (kg CO2 per kWh)
ELECTRICITY_FACTOR = 0.45
AC_KW = 1.5
APPLIANCE_KW = 0.5

# Food preference emission factors (kg CO2 per month)
FOOD_FACTORS = {
    "vegan": 100.0,
    "vegetarian": 150.0,
    "non-vegetarian": 300.0
}

# Shopping emission factors (kg CO2 per item/device)
CLOTHING_FACTOR = 15.0
ELECTRONICS_FACTOR = 80.0

# Waste and recycling emission factors (kg CO2 per month)
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
