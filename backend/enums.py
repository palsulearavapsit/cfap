from enum import Enum

class DietPreference(str, Enum):
    """Enumeration of food preference options."""
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    NON_VEGETARIAN = "non-vegetarian"

class RecyclingFrequency(str, Enum):
    """Enumeration of waste recycling frequency options."""
    RARELY = "rarely"
    SOMETIMES = "sometimes"
    ALWAYS = "always"

class PlasticWasteLevel(str, Enum):
    """Enumeration of plastic consumption/waste levels."""
    LOW = "low"
    AVERAGE = "average"
    HIGH = "high"
