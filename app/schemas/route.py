# Schémas Pydantic pour la validation des données des itinéraires
# Définit la structure des données entrantes et sortantes de l'API

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class RouteCreate(BaseModel):
    # agency_id: UUID
    origin: str
    destination: str
    duration: int

class RouteResponse(BaseModel):
    id: UUID
    agency_id: UUID
    origin: str
    destination: str
    duration: int
    created_at: datetime

    class Config:
        from_attributes = True