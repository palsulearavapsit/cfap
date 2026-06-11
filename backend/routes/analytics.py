from flask import Blueprint, request, jsonify, Response
from backend.models import CarbonEntry, Recommendation, ChallengeProgress
from backend.routes.auth import login_required
from typing import Any, List, Dict

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/summary', methods=['GET'])
@login_required
def get_summary() -> Response:
    """Returns a carbon footprint summary, category breakdown, and sustainability score."""
    user = request.current_user # type: ignore
    
    # Query carbon entries desc (limit to 2 most recent for summary metrics)
    entries: List[CarbonEntry] = CarbonEntry.query.filter_by(user_id=user.id).order_by(CarbonEntry.created_at.desc()).limit(2).all()
    
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

    current_entry: CarbonEntry = entries[0]
    previous_entry: Any = entries[1] if len(entries) > 1 else None
    
    current_emissions: float = current_entry.total_emissions
    previous_emissions: float = previous_entry.total_emissions if previous_entry else 0.0
    
    reduction_percentage: float = 0.0
    if previous_emissions > 0:
        reduction_percentage = ((previous_emissions - current_emissions) / previous_emissions) * 100
        reduction_percentage = round(reduction_percentage, 1)

    # Compute breakdown detail using conversion constants
    from backend.routes.calculator import CAR_FACTOR, BIKE_FACTOR, PUBLIC_FACTOR, FLIGHT_FACTOR, \
                                         ELECTRICITY_FACTOR, AC_KW, APPLIANCE_KW, FOOD_FACTORS, \
                                         CLOTHING_FACTOR, ELECTRONICS_FACTOR, RECYCLING_FACTORS, PLASTIC_FACTORS

    t_car: float = current_entry.transportation_car * CAR_FACTOR
    t_bike: float = current_entry.transportation_bike * BIKE_FACTOR
    t_public: float = current_entry.transportation_public * PUBLIC_FACTOR
    t_flights: float = current_entry.transportation_flights * FLIGHT_FACTOR
    transport_total: float = t_car + t_bike + t_public + t_flights

    e_elec: float = current_entry.energy_electricity * ELECTRICITY_FACTOR
    e_ac: float = current_entry.energy_ac * AC_KW * ELECTRICITY_FACTOR
    e_app: float = current_entry.energy_appliance * APPLIANCE_KW * ELECTRICITY_FACTOR
    energy_total: float = e_elec + e_ac + e_app

    food_total: float = FOOD_FACTORS.get(current_entry.food_preference.lower(), 300.0)
    shopping_total: float = (current_entry.shopping_clothing * CLOTHING_FACTOR) + (current_entry.shopping_electronics * ELECTRONICS_FACTOR)
    waste_total: float = RECYCLING_FACTORS.get(current_entry.waste_recycling.lower(), 30.0) + PLASTIC_FACTORS.get(current_entry.waste_plastic.lower(), 25.0)

    total: float = transport_total + energy_total + food_total + shopping_total + waste_total

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

    # Calculate Sustainability Score
    base_score: int = 80
    if current_emissions > 100:
        penalty: int = int((current_emissions - 100) // 10)
        base_score -= penalty

    completed_challenges: int = ChallengeProgress.query.filter_by(
        user_id=user.id,
        completion_status="completed"
    ).count()
    base_score += (completed_challenges * 5)

    completed_recs: int = Recommendation.query.filter_by(
        user_id=user.id,
        is_completed=True
    ).count()
    base_score += (completed_recs * 3)

    sustainability_score: int = max(10, min(100, base_score))

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
def get_history_analytics() -> Response:
    """Returns chronologically ordered monthly emission records filtered by time window."""
    user = request.current_user # type: ignore
    time_filter: str = request.args.get('filter', '6m').lower()

    if time_filter not in ['3m', '6m', 'ytd']:
        time_filter = '6m' # Safe default fallback

    query = CarbonEntry.query.filter_by(user_id=user.id)

    if time_filter == 'ytd':
        from datetime import datetime
        current_year_start: datetime = datetime(datetime.utcnow().year, 1, 1)
        query = query.filter(CarbonEntry.created_at >= current_year_start)
        entries: List[CarbonEntry] = query.order_by(CarbonEntry.created_at.asc()).all()
    elif time_filter == '3m':
        entries = query.order_by(CarbonEntry.created_at.desc()).limit(3).all()
        entries.reverse()
    elif time_filter == '6m':
        entries = query.order_by(CarbonEntry.created_at.desc()).limit(6).all()
        entries.reverse()
    else:
        entries = query.order_by(CarbonEntry.created_at.asc()).all()

    trends: List[Dict[str, Any]] = []
    if not entries:
        return jsonify({"trends": []}), 200

    for entry in entries:
        label: str = entry.created_at.strftime("%b %d")
        trends.append({
            "label": label,
            "emissions": round(entry.total_emissions, 2)
        })
        
    return jsonify({"trends": trends}), 200
