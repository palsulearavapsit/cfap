from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.core.db import get_db
from backend.api.routers.auth import get_current_user
from backend.models.models import User, Recommendation
from backend.schemas.schemas import RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/", response_model=List[RecommendationResponse])
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recs = db.query(Recommendation).filter(
        Recommendation.user_id == current_user.id
    ).order_by(Recommendation.is_completed.asc(), Recommendation.created_at.desc()).all()
    return recs

@router.patch("/{rec_id}/complete", response_model=RecommendationResponse)
def complete_recommendation(
    rec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.user_id == current_user.id
    ).first()
    
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    rec.is_completed = not rec.is_completed
    db.commit()
    db.refresh(rec)
    return rec
