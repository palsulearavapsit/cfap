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

# Maximum input safety limits to prevent overflows and layout issues
LIMIT_CAR_KM = 100000.0
LIMIT_BIKE_KM = 10000.0
LIMIT_PUBLIC_KM = 100000.0
LIMIT_FLIGHT_KM = 100000.0
LIMIT_ELECTRICITY = 50000.0
LIMIT_AC_HOURS = 744.0
LIMIT_APPLIANCE_HOURS = 744.0
LIMIT_CLOTHING_ITEMS = 1000.0
LIMIT_ELECTRONICS_DEVICES = 100.0

# Centralized Error and Warning Messages (Item 12)
ERROR_MALFORMED_JSON = "Malformed request body. Please provide a valid JSON payload."
ERROR_DB_OPERATION = "Database operation failed. Please try again later."
ERROR_UNAUTHORIZED = "Authentication credentials were not provided."
ERROR_INVALID_TOKEN = "Signature has expired or is invalid."
ERROR_INVALID_INPUTS = "Invalid input formats"
ERROR_EMAIL_TAKEN = "Email address already registered"
ERROR_LOCKOUT = "Too many failed login attempts. Account temporarily locked. Try again in 15 minutes."

# Dynamic Challenge Duration Constraints (Item 17) — configurable durations per difficulty level
CHALLENGE_DURATION_DAYS = {
    "Beginner": 7,
    "Intermediate": 14,
    "Advanced": 21,
    "Expert": 30,
}
DEFAULT_CHALLENGE_DURATION_DAYS = 7

# Valid Environment Profile Names (Item 19) — used to detect profile mismatches
VALID_PROFILES = ("development", "testing", "production")

# Allowed HTTP Request Header Names for sanitization (Item 15)
ALLOWED_HEADERS_WHITELIST = frozenset([
    "authorization",
    "content-type",
    "x-requested-with",
    "x-csrf-token",
    "x-forwarded-for",
    "accept",
    "accept-language",
    "cache-control",
])
