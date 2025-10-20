# Schémas Pydantic pour la validation des données des horaires
# Définit la structure des données entrantes et sortantes de l'API

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class ScheduleCreate(BaseModel):
    route_id: UUID
    departure_time: datetime
    price: float
    seats: int

class ScheduleResponse(BaseModel):
    id: UUID
    route_id: UUID
    departure_time: datetime
    price: float
    seats: int
    available_seats: int
    created_at: datetime

    class Config:
        from_attributes = True