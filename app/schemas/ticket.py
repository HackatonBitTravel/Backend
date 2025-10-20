# Schémas Pydantic pour la validation des données des tickets
# Définit la structure des données entrantes et sortantes de l'API

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Dict, Any

class TicketGenerate(BaseModel):
    reservation_id: UUID

class TicketResponse(BaseModel):
    id: UUID
    reservation_id: UUID
    payload: str
    signature: str
    public_key: str
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class TicketVerifyRequest(BaseModel):
    ticket_id: UUID
    payload: Dict[str, Any]
    signature: str
    public_key: str

class TicketVerifyResponse(BaseModel):
    valid: bool
    status: str
    message: str