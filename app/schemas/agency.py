# Schémas Pydantic pour la validation des données des agences
# Définit la structure des données entrantes et sortantes de l'API

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class AgencyRegister(BaseModel):
    name: str
    # contact: str
    email: EmailStr
    phone: str
    password: str

class AgencyLogin(BaseModel):
    email: EmailStr
    password: str

class AgencyResponse(BaseModel):
    id: UUID
    name: str
    # contact: str
    email: str
    phone: str
    rating: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AgencyToken(BaseModel):
    access_token: str
    token_type: str