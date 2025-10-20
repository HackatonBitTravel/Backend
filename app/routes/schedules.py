# Routes API pour la gestion des horaires
# Endpoints pour créer et lister les programmes de voyage

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.schedule import Schedule
from app.models.route import Route
from app.schemas.schedule import ScheduleCreate, ScheduleResponse

router = APIRouter(prefix="/schedules", tags=["Schedules"])

@router.post("/", response_model=ScheduleResponse, status_code=201)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.id == schedule.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Itinéraire non trouvé")
    
    db_schedule = Schedule(
        route_id=schedule.route_id,
        departure_time=schedule.departure_time,
        price=schedule.price,
        seats=schedule.seats,
        available_seats=schedule.seats
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.get("/", response_model=List[ScheduleResponse])
def list_schedules(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    schedules = db.query(Schedule).offset(skip).limit(limit).all()
    return schedules

@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Horaire non trouvé")
    return schedule