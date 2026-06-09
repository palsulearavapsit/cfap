import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.api.routers.auth import get_current_user
from backend.models.models import User, CarbonEntry, Recommendation, ChallengeProgress
from backend.schemas.schemas import AnalyticsSummary, CategoryBreakdown, HistoryAnalytics, TrendPoint
from backend.services.calculator import calculate_emissions

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch all entries for user ordered by created_at desc
    entries = db.query(CarbonEntry).filter(
        CarbonEntry.user_id == current_user.id
    ).order_by(CarbonEntry.created_at.desc()).all()
    
    if not entries:
        # If no entries, return empty summary
        return {
            "current_month_emissions": 0.0,
            "previous_month_emissions": 0.0,
            "reduction_percentage": 0.0,
            "sustainability_score": 100,
            "category_breakdown_percentages": {
                "transportation": 0.0,
                "energy": 0.0,
                "food": 0.0,
                "shopping": 0.0,
                "waste": 0.0
            }
        }
    
    current_entry = entries[0]
    previous_entry = entries[1] if len(entries) > 1 else None
    
    current_emissions = current_entry.total_emissions
    previous_emissions = previous_entry.total_emissions if previous_entry else 0.0
    
    # Calculate reduction percentage: ((previous - current) / previous) * 100
    reduction_percentage = 0.0
    if previous_emissions > 0:
        reduction_percentage = ((previous_emissions - current_emissions) / previous_emissions) * 100
        reduction_percentage = round(reduction_percentage, 1)

    # Compute category breakdown percentages for current entry
    calc_results = calculate_emissions(current_entry)
    percentages = calc_results["percentages"]
    
    # Calculate sustainability score out of 100
    # Start at 80, subtract based on emissions (higher than 150kg/month is penalized), add for accomplishments
    base_score = 80
    
    # Penalty: subtract 1 point for every 10kg above 100kg CO2/month
    if current_emissions > 100:
        penalty = int((current_emissions - 100) // 10)
        base_score -= penalty
        
    # Rewards:
    # +5 points for each completed challenge progress
    completed_challenges_count = db.query(ChallengeProgress).filter(
        ChallengeProgress.user_id == current_user.id,
        ChallengeProgress.completion_status == "completed"
    ).count()
    base_score += (completed_challenges_count * 5)
    
    # +3 points for each completed recommendation
    completed_recs_count = db.query(Recommendation).filter(
        Recommendation.user_id == current_user.id,
        Recommendation.is_completed == True
    ).count()
    base_score += (completed_recs_count * 3)
    
    # Cap score between 10 and 100
    sustainability_score = max(10, min(100, base_score))

    return {
        "current_month_emissions": round(current_emissions, 2),
        "previous_month_emissions": round(previous_emissions, 2),
        "reduction_percentage": reduction_percentage,
        "sustainability_score": sustainability_score,
        "category_breakdown_percentages": CategoryBreakdown(
            transportation=percentages["transportation"],
            energy=percentages["energy"],
            food=percentages["food"],
            shopping=percentages["shopping"],
            waste=percentages["waste"]
        )
    }

@router.get("/history", response_model=HistoryAnalytics)
def get_history_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get last 6 entries ordered by created_at asc for trend line chart
    entries = db.query(CarbonEntry).filter(
        CarbonEntry.user_id == current_user.id
    ).order_by(CarbonEntry.created_at.asc()).all()
    
    trends = []
    if not entries:
        # Return mock trend points for demonstration if empty
        return {"trends": []}
    
    # Group by created_at month/date label
    for entry in entries[-6:]: # Limit to last 6 entries
        label = entry.created_at.strftime("%b %d") # e.g. "Jun 09" or "May 12"
        trends.append(
            TrendPoint(
                label=label,
                emissions=round(entry.total_emissions, 2)
            )
        )
        
    return {"trends": trends}
