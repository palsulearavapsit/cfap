import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from backend.core.db import get_db
from backend.api.routers.auth import get_current_user
from backend.models.models import User, Challenge, ChallengeProgress
from backend.schemas.schemas import ChallengeResponse, ChallengeProgressResponse, ChallengeJoinRequest

router = APIRouter(prefix="/challenges", tags=["challenges"])

@router.get("/", response_model=List[ChallengeResponse])
def get_challenges(db: Session = Depends(get_db)):
    return db.query(Challenge).order_by(Challenge.id.asc()).all()

@router.get("/active", response_model=List[ChallengeProgressResponse])
def get_active_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = db.query(ChallengeProgress).options(
        joinedload(ChallengeProgress.challenge)
    ).filter(
        ChallengeProgress.user_id == current_user.id
    ).order_by(ChallengeProgress.start_date.desc()).all()
    return progress

@router.post("/join", response_model=ChallengeProgressResponse, status_code=status.HTTP_201_CREATED)
def join_challenge(
    request: ChallengeJoinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if challenge exists
    challenge = db.query(Challenge).filter(Challenge.id == request.challenge_id).first()
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )
    
    # Check if user already joined this challenge and it is still in_progress
    existing_progress = db.query(ChallengeProgress).filter(
        ChallengeProgress.user_id == current_user.id,
        ChallengeProgress.challenge_id == request.challenge_id,
        ChallengeProgress.completion_status == "in_progress"
    ).first()
    
    if existing_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already participating in this challenge"
        )
    
    # Set challenge duration (e.g., 7 days)
    start_time = datetime.datetime.utcnow()
    end_time = start_time + datetime.timedelta(days=7)
    
    new_progress = ChallengeProgress(
        user_id=current_user.id,
        challenge_id=request.challenge_id,
        start_date=start_time,
        end_date=end_time,
        completion_status="in_progress",
        points_earned=0
    )
    
    db.add(new_progress)
    db.commit()
    db.refresh(new_progress)
    return new_progress

@router.post("/{progress_id}/complete", response_model=ChallengeProgressResponse)
def complete_challenge(
    progress_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = db.query(ChallengeProgress).filter(
        ChallengeProgress.id == progress_id,
        ChallengeProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge progress record not found"
        )
    
    if progress.completion_status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Challenge is already {progress.completion_status}"
        )
        
    progress.completion_status = "completed"
    progress.points_earned = progress.challenge.points
    db.commit()
    db.refresh(progress)
    return progress
