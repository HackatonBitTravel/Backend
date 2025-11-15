# Routes API pour la gestion des itinéraires
# Endpoints pour créer et lister les trajets proposés par les agences

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.agency_dependencies import get_current_active_agency
from app.models.route import Route
from app.models.agency import Agency
from app.schemas.route import RouteCreate, RouteResponse

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/", response_model=RouteResponse, status_code=201)
def create_route(
    route: RouteCreate,
    db: Session = Depends(get_db),
    current_agency: Agency = Depends(get_current_active_agency)
):
    db_route = Route(
        agency_id=current_agency.id,
        origin=route.origin,
        destination=route.destination,
        duration=route.duration
    )
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route

@router.get("/", response_model=List[RouteResponse])
def list_routes(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    routes = db.query(Route).offset(skip).limit(limit).all()
    return routes

@router.get("/popular")
def get_popular_routes(limit: int = 5, db: Session = Depends(get_db)):
    routes = db.query(
        Route.id,
        Route.origin,
        Route.destination,
        Route.duration,
        Agency.name.label("agency_name")
    ).join(Agency, Route.agency_id == Agency.id
    ).limit(limit).all()
    
    return [
        {
            "id": str(r.id),
            "origin": r.origin,
            "destination": r.destination,
            "duration": r.duration,
            "agency_name": r.agency_name
        }
        for r in routes
    ]