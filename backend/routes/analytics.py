from typing import Any, Dict, List

from flask import Blueprint, Response, request
from sqlalchemy.orm import joinedload

from backend.models import CarbonEntry, ChallengeProgress, Recommendation
from backend.routes.auth import login_required
from backend.utils import send_response

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("/summary", methods=["GET"])
@login_required
def get_summary() -> Response:
    """Returns a carbon footprint summary, category breakdown, and sustainability score."""
    user = request.current_user  # type: ignore

    # Query carbon entries desc with eager loading of user relationship (Item 41)
    entries: List[CarbonEntry] = (
        CarbonEntry.query.filter_by(user_id=user.id)
        .options(joinedload(CarbonEntry.user))
        .order_by(CarbonEntry.created_at.desc())
        .limit(2)
        .all()
    )

    if not entries:
        return send_response(
            {
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
                    "waste": 0.0,
                },
                "category_breakdown_values": {
                    "transportation": 0.0,
                    "energy": 0.0,
                    "food": 0.0,
                    "shopping": 0.0,
                    "waste": 0.0,
                },
            },
            200,
        )

    current_entry: CarbonEntry = entries[0]
    previous_entry: Any = entries[1] if len(entries) > 1 else None

    current_emissions: float = current_entry.total_emissions
    previous_emissions: float = (
        previous_entry.total_emissions if previous_entry else 0.0
    )

    reduction_percentage: float = 0.0
    if previous_emissions > 0:
        reduction_percentage = (
            (previous_emissions - current_emissions) / previous_emissions
        ) * 100
        reduction_percentage = round(reduction_percentage, 1)

    # Compute breakdown detail using calculation service
    from backend.services.calculation_service import CalculationService

    breakdown = CalculationService.get_category_breakdown(current_entry)
    transport_total = breakdown["values"]["transportation"]
    energy_total = breakdown["values"]["energy"]
    food_total = breakdown["values"]["food"]
    shopping_total = breakdown["values"]["shopping"]
    waste_total = breakdown["values"]["waste"]

    transport_pct = breakdown["percentages"]["transportation"]
    energy_pct = breakdown["percentages"]["energy"]
    food_pct = breakdown["percentages"]["food"]
    shopping_pct = breakdown["percentages"]["shopping"]
    waste_pct = breakdown["percentages"]["waste"]

    # Calculate Sustainability Score
    sustainability_score = CalculationService.calculate_sustainability_score(
        user.id, current_emissions
    )

    return send_response(
        {
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
                "waste": waste_pct,
            },
            "category_breakdown_values": {
                "transportation": round(transport_total, 2),
                "energy": round(energy_total, 2),
                "food": round(food_total, 2),
                "shopping": round(shopping_total, 2),
                "waste": round(waste_total, 2),
            },
        },
        200,
    )


@analytics_bp.route("/history", methods=["GET"])
@login_required
def get_history_analytics() -> Response:
    """Returns chronologically ordered monthly emission records filtered by time window."""
    user = request.current_user  # type: ignore
    time_filter: str = request.args.get("filter", "6m").lower()

    if time_filter not in ["3m", "6m", "ytd"]:
        time_filter = "6m"  # Safe default fallback

    query = CarbonEntry.query.filter_by(user_id=user.id)

    if time_filter == "ytd":
        from datetime import datetime

        current_year_start: datetime = datetime(datetime.utcnow().year, 1, 1)
        query = query.filter(CarbonEntry.created_at >= current_year_start)
        entries: List[CarbonEntry] = query.order_by(CarbonEntry.created_at.asc()).all()
    elif time_filter == "3m":
        entries = query.order_by(CarbonEntry.created_at.desc()).limit(3).all()
        entries.reverse()
    elif time_filter == "6m":
        entries = query.order_by(CarbonEntry.created_at.desc()).limit(6).all()
        entries.reverse()
    else:
        entries = query.order_by(CarbonEntry.created_at.asc()).all()

    trends: List[Dict[str, Any]] = []
    if not entries:
        return send_response({"trends": []}, 200)

    for entry in entries:
        label: str = entry.created_at.strftime("%b %d")
        trends.append({"label": label, "emissions": round(entry.total_emissions, 2)})

    return send_response({"trends": trends}, 200)
