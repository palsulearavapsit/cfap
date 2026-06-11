from flask import Blueprint, request, jsonify
from backend.models import db, CarbonEntry, Recommendation, ChallengeProgress
from backend.routes.auth import login_required
from backend.routes.calculator import calculate_emissions

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/summary', methods=['GET'])
@login_required
def get_summary():
    user = request.current_user
    
    # Query carbon entries desc
    entries = CarbonEntry.query.filter_by(user_id=user.id).order_by(CarbonEntry.created_at.desc()).all()
    
    if not entries:
        return jsonify({
            "current_month_emissions": 0.0,
            "previous_month_emissions": 0.0,
            "reduction_percentage": 0.0,
            "sustainability_score": 100,
            "national_average": 1300.0,
            "global_average": 350.0,
            "category_breakdown_percentages": {
                "transportation": 0.0,
                "energy": 0.0,
                "food": 0.0,
                "shopping": 0.0,
                "waste": 0.0
            },
            "category_breakdown_values": {
                "transportation": 0.0,
                "energy": 0.0,
                "food": 0.0,
                "shopping": 0.0,
                "waste": 0.0
            }
        }), 200

    current_entry = entries[0]
    previous_entry = entries[1] if len(entries) > 1 else None
    
    current_emissions = current_entry.total_emissions
    previous_emissions = previous_entry.total_emissions if previous_entry else 0.0
    
    reduction_percentage = 0.0
    if previous_emissions > 0:
        reduction_percentage = ((previous_emissions - current_emissions) / previous_emissions) * 100
        reduction_percentage = round(reduction_percentage, 1)

    # Use calculate_emissions algorithm logic to get percentages
    # Mock parameters matching calculate_emissions dict requirements
    calc_data = {
        "transportation_car": current_entry.transportation_car,
        "transportation_bike": current_entry.transportation_bike,
        "transportation_public": current_entry.transportation_public,
        "transportation_flights": current_entry.transportation_flights,
        "energy_electricity": current_entry.energy_electricity,
        "energy_ac": current_entry.energy_ac,
        "energy_appliance": current_entry.energy_appliance,
        "food_preference": current_entry.food_preference,
        "shopping_clothing": current_entry.shopping_clothing,
        "shopping_electronics": current_entry.shopping_electronics,
        "waste_recycling": current_entry.waste_recycling,
        "waste_plastic": current_entry.waste_plastic
    }
    
    # Compute breakdown detail
    from backend.routes.calculator import CAR_FACTOR, BIKE_FACTOR, PUBLIC_FACTOR, FLIGHT_FACTOR, \
                                         ELECTRICITY_FACTOR, AC_KW, APPLIANCE_KW, FOOD_FACTORS, \
                                         CLOTHING_FACTOR, ELECTRONICS_FACTOR, RECYCLING_FACTORS, PLASTIC_FACTORS

    t_car = current_entry.transportation_car * CAR_FACTOR
    t_bike = current_entry.transportation_bike * BIKE_FACTOR
    t_public = current_entry.transportation_public * PUBLIC_FACTOR
    t_flights = current_entry.transportation_flights * FLIGHT_FACTOR
    transport_total = t_car + t_bike + t_public + t_flights

    e_elec = current_entry.energy_electricity * ELECTRICITY_FACTOR
    e_ac = current_entry.energy_ac * AC_KW * ELECTRICITY_FACTOR
    e_app = current_entry.energy_appliance * APPLIANCE_KW * ELECTRICITY_FACTOR
    energy_total = e_elec + e_ac + e_app

    food_total = FOOD_FACTORS.get(current_entry.food_preference.lower(), 300.0)
    shopping_total = (current_entry.shopping_clothing * CLOTHING_FACTOR) + (current_entry.shopping_electronics * ELECTRONICS_FACTOR)
    waste_total = RECYCLING_FACTORS.get(current_entry.waste_recycling.lower(), 30.0) + PLASTIC_FACTORS.get(current_entry.waste_plastic.lower(), 25.0)

    total = transport_total + energy_total + food_total + shopping_total + waste_total

    if total > 0:
        transport_pct = round((transport_total / total) * 100, 1)
        energy_pct = round((energy_total / total) * 100, 1)
        food_pct = round((food_total / total) * 100, 1)
        shopping_pct = round((shopping_total / total) * 100, 1)
        waste_pct = round((waste_total / total) * 100, 1)
    else:
        transport_pct = energy_pct = food_pct = shopping_pct = waste_pct = 0.0

    # Calculate Sustainability Score
    base_score = 80
    if current_emissions > 100:
        penalty = int((current_emissions - 100) // 10)
        base_score -= penalty

    completed_challenges = ChallengeProgress.query.filter_by(
        user_id=user.id,
        completion_status="completed"
    ).count()
    base_score += (completed_challenges * 5)

    completed_recs = Recommendation.query.filter_by(
        user_id=user.id,
        is_completed=True
    ).count()
    base_score += (completed_recs * 3)

    sustainability_score = max(10, min(100, base_score))

    return jsonify({
        "current_month_emissions": round(current_emissions, 2),
        "previous_month_emissions": round(previous_emissions, 2),
        "reduction_percentage": reduction_percentage,
        "sustainability_score": sustainability_score,
        "national_average": 1300.0,
        "global_average": 350.0,
        "category_breakdown_percentages": {
            "transportation": transport_pct,
            "energy": energy_pct,
            "food": food_pct,
            "shopping": shopping_pct,
            "waste": waste_pct
        },
        "category_breakdown_values": {
            "transportation": round(transport_total, 2),
            "energy": round(energy_total, 2),
            "food": round(food_total, 2),
            "shopping": round(shopping_total, 2),
            "waste": round(waste_total, 2)
        }
    }), 200

@analytics_bp.route('/history', methods=['GET'])
@login_required
def get_history_analytics():
    user = request.current_user
    time_filter = request.args.get('filter', '6m').lower()

    query = CarbonEntry.query.filter_by(user_id=user.id)

    if time_filter == 'ytd':
        from datetime import datetime
        current_year_start = datetime(datetime.utcnow().year, 1, 1)
        query = query.filter(CarbonEntry.created_at >= current_year_start)

    entries = query.order_by(CarbonEntry.created_at.asc()).all()

    if time_filter == '3m':
        entries = entries[-3:]
    elif time_filter == '6m':
        entries = entries[-6:]

    trends = []
    # If empty, return empty trends
    if not entries:
        return jsonify({"trends": []}), 200

    for entry in entries:
        label = entry.created_at.strftime("%b %d")
        trends.append({
            "label": label,
            "emissions": round(entry.total_emissions, 2)
        })
        
    return jsonify({"trends": trends}), 200
