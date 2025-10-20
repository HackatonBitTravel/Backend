# Schémas Pydantic pour la validation des données des réservations
# Définit la structure des données entrantes et sortantes de l'API

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Dict, Any

class PassengerInfo(BaseModel):
    name: str
    phone: str
    email: str = None

class ReservationCreate(BaseModel):
    schedule_id: UUID
    passenger_info: PassengerInfo

class ReservationResponse(BaseModel):
    id: UUID
    schedule_id: UUID
    passenger_info: Dict[str, Any]
    payment_status: str
    total_amount: str
    created_at: datetime

    class Config:
        from_attributes = True