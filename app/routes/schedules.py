# Routes API pour la gestion des horaires
# Endpoints pour créer et lister les programmes de voyage

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.schedule import Schedule
from app.models.route import Route
from app.schemas.schedule import ScheduleCreate, ScheduleResponse
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.agency_dependencies import get_current_active_agency
from app.models.schedule import Schedule
from app.models.route import Route
from app.models.agency import Agency
from app.schemas.schedule import ScheduleCreate, ScheduleResponse
from datetime import datetime
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
def list_schedules(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    now = datetime.now()
    schedules = (
        db.query(Schedule)
        .filter(Schedule.departure_time >= now)  # Ne garder que les horaires futurs
        .order_by(Schedule.departure_time)       # Optionnel : trier par date
        .offset(skip)
        .limit(limit)
        .all()
    )
    return schedules
@router.get("/agency_schedules", response_model=List[dict])
def list_schedules(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_agency: Agency = Depends(get_current_active_agency)
):
    """Liste les horaires à venir de l'agence connectée"""
    now = datetime.utcnow()
    schedules = (
        db.query(Schedule, Route)
        .join(Route, Schedule.route_id == Route.id)
        .filter(
            Route.agency_id == current_agency.id,
            Schedule.departure_time >= now
        )
        .order_by(Schedule.departure_time)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": str(schedule.id),
            "route_id": str(schedule.route_id),
            "departure_time": schedule.departure_time.isoformat(),
            "price": float(schedule.price),
            "seats": schedule.seats,
            "available_seats": schedule.available_seats,
            "route": {
                "id": str(route.id),
                "origin": route.origin,
                "destination": route.destination,
                "duration": route.duration
            }
        }
        for schedule, route in schedules
    ]
@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Horaire non trouvé")
    return schedule