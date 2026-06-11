import os
import json
import re
import google.generativeai as genai
from abc import ABC, abstractmethod
from backend.constants import (
    CAR_FACTOR, FLIGHT_FACTOR, ELECTRICITY_FACTOR, AC_KW,
    CLOTHING_FACTOR, ELECTRONICS_FACTOR
)
from typing import List, Dict, Any, Optional

class BaseAIService(ABC):
    """Abstract interface defining the AI recommendation generation structure."""
    
    @abstractmethod
    def generate_recommendations(self, data: dict) -> List[Dict[str, Any]]:
        """Generates 3 personalized recommendations based on footprint variables."""
        pass


_api_configured_cache: Optional[bool] = None

def is_gemini_configured() -> bool:
    """Checks and caches whether the Gemini API key is properly configured on the server (Item 52)."""
    global _api_configured_cache
    if _api_configured_cache is None:
        api_key = os.getenv("GEMINI_API_KEY")
        _api_configured_cache = bool(api_key and api_key != "YOUR_GEMINI_API_KEY")
    return _api_configured_cache


def get_fallback_recommendations(data: dict) -> List[Dict[str, Any]]:
    """Generates standard rules-based carbon footprint recommendations as fallback."""
    recommendations: List[Dict[str, Any]] = []
    
    # 1. Transportation
    car_emissions: float = data.get("transportation_car", 0) * CAR_FACTOR
    flights_emissions: float = data.get("transportation_flights", 0) * FLIGHT_FACTOR
    
    if car_emissions > 100 or flights_emissions > 150:
        recommendations.append({
            "title": "Switch to Public Transit",
            "description": "Replace 50% of your solo car drives with bus or train commutes. Public transit significantly cuts per-passenger emissions.",
            "difficulty": "Intermediate",
            "expected_reduction": 65.0,
            "estimated_savings": 50.0
        })
        recommendations.append({
            "title": "Active Commuting (Cycling/Walking)",
            "description": "Cycle or walk for short trips under 5km. It has zero emissions and improves cardiovascular health.",
            "difficulty": "Beginner",
            "expected_reduction": 35.0,
            "estimated_savings": 20.0
        })
    
    if flights_emissions > 200:
        recommendations.append({
            "title": "Offset Flight Emissions & Reduce Trips",
            "description": "Combine business trips or opt for high-speed rail instead of short-haul flights. Purchase gold-standard carbon offsets for necessary flights.",
            "difficulty": "Advanced",
            "expected_reduction": 120.0,
            "estimated_savings": 150.0
        })

    # 2. Energy
    elec_emissions: float = data.get("energy_electricity", 0) * ELECTRICITY_FACTOR
    ac_emissions: float = data.get("energy_ac", 0) * AC_KW * ELECTRICITY_FACTOR
    
    if elec_emissions > 80:
        recommendations.append({
            "title": "Upgrade to LED Lighting",
            "description": "Replace all incandescent bulbs with ENERGY STAR certified LEDs. They use up to 75% less energy and last 25x longer.",
            "difficulty": "Beginner",
            "expected_reduction": 12.0,
            "estimated_savings": 8.0
        })
        recommendations.append({
            "title": "Smart Thermostat & Efficient Appliances",
            "description": "Install a smart programmable thermostat and unplug idle electronics. Ensure new appliances are rated A+++ or ENERGY STAR.",
            "difficulty": "Intermediate",
            "expected_reduction": 40.0,
            "estimated_savings": 25.0
        })
        
    if ac_emissions > 50:
        recommendations.append({
            "title": "Reduce AC Usage & Thermostat Settings",
            "description": "Set your AC to 24-26°C (75-78°F) rather than lower. Use ceiling fans to circulate air and close blinds during peak sunlight.",
            "difficulty": "Beginner",
            "expected_reduction": 25.0,
            "estimated_savings": 18.0
        })

    # 3. Food
    food_pref: str = str(data.get("food_preference", "non-vegetarian")).lower()
    if food_pref == "non-vegetarian":
        recommendations.append({
            "title": "Integrate Meat-Free Days",
            "description": "Try replacing red meat and dairy with plant-based alternatives on select days (e.g., Meat-Free Mondays). Raising livestock generates massive methane emissions.",
            "difficulty": "Beginner",
            "expected_reduction": 45.0,
            "estimated_savings": 30.0
        })
    elif food_pref == "vegetarian":
        recommendations.append({
            "title": "Transition towards Plant-Based Diet",
            "description": "Reduce cheese, butter, and milk consumption. Source foods locally to reduce food miles and packaging waste.",
            "difficulty": "Intermediate",
            "expected_reduction": 15.0,
            "estimated_savings": 10.0
        })

    # 4. Shopping
    clothing_emissions: float = data.get("shopping_clothing", 0) * CLOTHING_FACTOR
    electronics_emissions: float = data.get("shopping_electronics", 0) * ELECTRONICS_FACTOR
    
    if clothing_emissions > 30:
        recommendations.append({
            "title": "Choose Sustainable & Second-Hand Fashion",
            "description": "Avoid fast fashion. Buy high-quality, durable garments or explore thrift stores. Extend your clothes' lifetime by washing at lower temperatures.",
            "difficulty": "Beginner",
            "expected_reduction": 20.0,
            "estimated_savings": 40.0
        })
    if electronics_emissions > 70:
        recommendations.append({
            "title": "Extend Electronics Lifecycle & Repair",
            "description": "Instead of upgrading devices yearly, repair existing ones and buy refurbished electronics when replacement is necessary. Recycle old devices safely.",
            "difficulty": "Intermediate",
            "expected_reduction": 75.0,
            "estimated_savings": 120.0
        })

    # 5. Waste
    if str(data.get("waste_recycling", "sometimes")).lower() == "rarely":
        recommendations.append({
            "title": "Set Up Household Recycling Station",
            "description": "Separate paper, cardboard, glass, and metal from general landfill waste. Check local guidelines for recyclable plastics.",
            "difficulty": "Beginner",
            "expected_reduction": 15.0,
            "estimated_savings": 0.0
        })
    if str(data.get("waste_plastic", "average")).lower() in ["average", "high"]:
        recommendations.append({
            "title": "Adopt Zero-Waste Shopping Habits",
            "description": "Carry reusable canvas bags, purchase items in bulk, and refuse single-use plastic water bottles. Bring containers for bulk food.",
            "difficulty": "Beginner",
            "expected_reduction": 10.0,
            "estimated_savings": 15.0
        })

    # Catch-all
    if not recommendations:
        recommendations.append({
            "title": "Compost Organic Waste",
            "description": "Start composting your kitchen scraps and garden clippings. This prevents organic matter from producing landfill methane.",
            "difficulty": "Intermediate",
            "expected_reduction": 12.0,
            "estimated_savings": 5.0
        })
        recommendations.append({
            "title": "Mindful Consumption Check",
            "description": "Before making any purchase, wait 48 hours to determine if it is a necessity or impulse buy.",
            "difficulty": "Beginner",
            "expected_reduction": 15.0,
            "estimated_savings": 50.0
        })

    return recommendations[:3]


class GeminiAIService(BaseAIService):
    """Implementation of BaseAIService using Google Gemini model API."""

    def generate_recommendations(self, data: dict) -> List[Dict[str, Any]]:
        """Generates 3 personalized recommendations using the Gemini API based on lifestyle survey."""
        if not is_gemini_configured():
            return get_fallback_recommendations(data)

        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt: str = f"""
            You are an expert environmental consultant and sustainability advisor.
            Analyze the following monthly lifestyle and carbon footprint parameters for a user and suggest exactly 3 highly personalized, concrete, actionable recommendations to reduce their footprint and save money.

            LIFESTYLE METRICS:
            - Transportation:
                * Car travel distance: {data.get('transportation_car', 0)} km/month
                * Bicycle distance: {data.get('transportation_bike', 0)} km/month
                * Public transit distance: {data.get('transportation_public', 0)} km/month
                * Flights distance: {data.get('transportation_flights', 0)} km/month
            - Home Energy & Diet:
                * Electricity usage: {data.get('energy_electricity', 0)} kWh/month
                * Air Conditioner usage: {data.get('energy_ac', 0)} hours/month
                * Major appliances usage: {data.get('energy_appliance', 0)} hours/month
                * Diet preference: {data.get('food_preference', 'non-vegetarian')}
            - Shopping & Waste habits:
                * New clothes purchased: {data.get('shopping_clothing', 0)} items/month
                * New electronics purchased: {data.get('shopping_electronics', 0)} devices/month
                * Recycling frequency: {data.get('waste_recycling', 'sometimes')}
                * Single-use plastic usage: {data.get('waste_plastic', 'average')}

            Return your advice as a strictly formatted JSON array of objects. Do not write any markdown code blocks, do not wrap it in ```json ... ```, and do not append conversational text.
            
            JSON Structure Example:
            [
              {{
                "title": "Upgrade to Smart Power Strips",
                "description": "Configure smart strips for home media and office setup. These eliminate phantom load draws from idle TVs and electronics, saving energy.",
                "difficulty": "Beginner",
                "expected_reduction": 15.5,
                "estimated_savings": 12.0
              }}
            ]
            
            Fields details:
            - "difficulty": String, must be exactly one of: "Beginner", "Intermediate", "Advanced", "Expert"
            - "expected_reduction": Float, estimated CO2 reduction in kg/month
            - "estimated_savings": Float, estimated monthly savings in USD
            """

            response = model.generate_content(prompt)
            text: str = response.text.strip()
            
            if "```" in text:
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
                if match:
                    text = match.group(1).strip()
                else:
                    text = text.replace("```json", "").replace("```", "").strip()

            parsed_json: list = json.loads(text)
            if isinstance(parsed_json, list) and len(parsed_json) > 0:
                normalized: List[Dict[str, Any]] = []
                for rec in parsed_json[:3]:
                    difficulty: str = rec.get("difficulty", "Beginner")
                    if difficulty not in ["Beginner", "Intermediate", "Advanced", "Expert"]:
                        difficulty = "Beginner"
                    
                    normalized.append({
                        "title": str(rec.get("title", "Reduce Energy Consumption")),
                        "description": str(rec.get("description", "Lower utility waste by turning off unused electronics.")),
                        "difficulty": difficulty,
                        "expected_reduction": float(rec.get("expected_reduction", 10.0)),
                        "estimated_savings": float(rec.get("estimated_savings", 5.0))
                    })
                return normalized

        except Exception as e:
            # Fall back safely
            pass
            
        return get_fallback_recommendations(data)


def generate_recommendations_gemini(data: dict) -> List[Dict[str, Any]]:
    """Helper wrapper function to resolve recommendations, maintaining backward-compatibility."""
    service = GeminiAIService()
    return service.generate_recommendations(data)
