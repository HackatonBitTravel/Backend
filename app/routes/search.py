# Routes API pour la recherche de trajets
# Endpoint pour rechercher des trajets selon différents critères

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.schedule import Schedule
from app.models.route import Route
from app.models.agency import Agency
from app.schemas.search import SearchResult

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/", response_model=List[SearchResult])
def search_trips(
    origin: Optional[str] = Query(None, description="Ville de départ"),
    destination: Optional[str] = Query(None, description="Ville d'arrivée"),
    date: Optional[str] = Query(None, description="Date de départ (YYYY-MM-DD)"),
    min_price: Optional[float] = Query(None, description="Prix minimum"),
    max_price: Optional[float] = Query(None, description="Prix maximum"),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(
        Schedule.id.label("schedule_id"),
        Route.id.label("route_id"),
        Agency.id.label("agency_id"),
        Agency.name.label("agency_name"),
        Agency.rating.label("agency_rating"),
        Route.origin,
        Route.destination,
        Schedule.departure_time,
        Route.duration,
        Schedule.price,
        Schedule.available_seats
    ).join(Route, Schedule.route_id == Route.id
    ).join(Agency, Route.agency_id == Agency.id)

    filters = []
    
    if origin:
        filters.append(Route.origin.ilike(f"%{origin}%"))
    
    if destination:
        filters.append(Route.destination.ilike(f"%{destination}%"))
    
    if date:
        try:
            search_date = datetime.strptime(date, "%Y-%m-%d")
            next_day = search_date + timedelta(days=1)
            filters.append(and_(
                Schedule.departure_time >= search_date,
                Schedule.departure_time < next_day
            ))
        except ValueError:
            pass
    
    if min_price is not None:
        filters.append(Schedule.price >= min_price)
    
    if max_price is not None:
        filters.append(Schedule.price <= max_price)
    
    filters.append(Schedule.available_seats > 0)
    
    if filters:
        query = query.filter(and_(*filters))
    
    results = query.order_by(Schedule.departure_time).offset(skip).limit(limit).all()
    
    return [
        SearchResult(
            schedule_id=r.schedule_id,
            route_id=r.route_id,
            agency_id=r.agency_id,
            agency_name=r.agency_name,
            agency_rating=r.agency_rating,
            origin=r.origin,
            destination=r.destination,
            departure_time=r.departure_time,
            duration=r.duration,
            price=r.price,
            available_seats=r.available_seats
        )
        for r in results
    ]