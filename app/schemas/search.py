# Schémas Pydantic pour la recherche de trajets
# Définit les paramètres et réponses de recherche

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class SearchParams(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[datetime] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

class SearchResult(BaseModel):
    schedule_id: UUID
    route_id: UUID
    agency_id: UUID
    agency_name: str
    agency_rating: float
    origin: str
    destination: str
    departure_time: datetime
    duration: int
    price: float
    available_seats: int

    class Config:
        from_attributes = True