from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from backend.core.db import get_db
from backend.api.routers.auth import get_current_user
from backend.models.models import User, CarbonEntry
from backend.schemas.schemas import CarbonEntryCreate, CarbonEntryResponse
from backend.services.calculator import calculate_emissions
from backend.services.recommender import generate_recommendations

router = APIRouter(prefix="/calculator", tags=["calculator"])

@router.post("/submit", response_model=CarbonEntryResponse, status_code=status.HTTP_201_CREATED)
def submit_entry(
    entry_in: CarbonEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Calculate emissions
    results = calculate_emissions(entry_in)
    total_co2 = results["total_emissions"]
    
    # Save entry to DB
    new_entry = CarbonEntry(
        user_id=current_user.id,
        transportation_car=entry_in.transportation_car,
        transportation_bike=entry_in.transportation_bike,
        transportation_public=entry_in.transportation_public,
        transportation_flights=entry_in.transportation_flights,
        energy_electricity=entry_in.energy_electricity,
        energy_ac=entry_in.energy_ac,
        energy_appliance=entry_in.energy_appliance,
        food_preference=entry_in.food_preference,
        shopping_clothing=entry_in.shopping_clothing,
        shopping_electronics=entry_in.shopping_electronics,
        waste_recycling=entry_in.waste_recycling,
        waste_plastic=entry_in.waste_plastic,
        total_emissions=total_co2
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    
    # Generate recommendations based on this new questionnaire entry
    generate_recommendations(db, current_user.id, new_entry)
    
    return new_entry

@router.get("/history", response_model=List[CarbonEntryResponse])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entries = db.query(CarbonEntry).filter(
        CarbonEntry.user_id == current_user.id
    ).order_by(CarbonEntry.created_at.desc()).all()
    return entries
