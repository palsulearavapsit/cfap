from backend.services.calculator import calculate_emissions
from backend.schemas.schemas import CarbonEntryCreate

def test_calculate_emissions_zero():
    # Test zero emissions case
    entry = CarbonEntryCreate(
        transportation_car=0.0,
        transportation_bike=0.0,
        transportation_public=0.0,
        transportation_flights=0.0,
        energy_electricity=0.0,
        energy_ac=0.0,
        energy_appliance=0.0,
        food_preference="vegan",
        shopping_clothing=0.0,
        shopping_electronics=0.0,
        waste_recycling="always",
        waste_plastic="low"
    )
    result = calculate_emissions(entry)
    
    # Vegan (100) + Recycling Always (10) + Plastic Low (10) = 120 kg CO2/month
    assert result["total_emissions"] == 120.0
    assert result["breakdown"]["food"] == 100.0
    assert result["breakdown"]["waste"] == 20.0
    assert result["breakdown"]["transportation"] == 0.0
    assert result["percentages"]["food"] == 83.3 # 100 / 120 * 100
    assert result["percentages"]["waste"] == 16.7

def test_calculate_emissions_typical():
    # Test typical emissions case
    entry = CarbonEntryCreate(
        transportation_car=500.0,    # 500 * 0.171 = 85.5
        transportation_bike=10.0,    # 10 * 0.005 = 0.05
        transportation_public=100.0, # 100 * 0.041 = 4.1
        transportation_flights=1000.0,# 1000 * 0.115 = 115.0
        # Transportation sum = 85.5 + 0.05 + 4.1 + 115 = 204.65
        
        energy_electricity=200.0,    # 200 * 0.45 = 90.0
        energy_ac=30.0,              # 30 * 1.5 * 0.45 = 20.25
        energy_appliance=20.0,       # 20 * 0.5 * 0.45 = 4.5
        # Energy sum = 90.0 + 20.25 + 4.5 = 114.75
        
        food_preference="non-vegetarian", # 300.0
        
        shopping_clothing=2.0,       # 2 * 15 = 30.0
        shopping_electronics=1.0,    # 1 * 80 = 80.0
        # Shopping sum = 110.0
        
        waste_recycling="rarely",    # 50.0
        waste_plastic="high"         # 50.0
        # Waste sum = 100.0
    )
    # Total expected: 204.65 + 114.75 + 300.0 + 110.0 + 100.0 = 829.4
    
    result = calculate_emissions(entry)
    assert result["total_emissions"] == 829.4
    assert result["breakdown"]["transportation"] == 204.65
    assert result["breakdown"]["energy"] == 114.75
    assert result["breakdown"]["food"] == 300.0
    assert result["breakdown"]["shopping"] == 110.0
    assert result["breakdown"]["waste"] == 100.0
