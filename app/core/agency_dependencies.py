# Dépendances pour l'authentification des agences
# Récupère l'agence connectée via le token JWT

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.agency import Agency
from app.services.auth import AuthService

security = HTTPBearer()

async def get_current_agency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Agency:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants de l'agence"
    )
    
    token = credentials.credentials
    payload = AuthService.verify_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    agency = db.query(Agency).filter(Agency.email == email).first()
    if agency is None:
        raise credentials_exception
    
    return agency

async def get_current_active_agency(
    current_agency: Agency = Depends(get_current_agency)
) -> Agency:
    if current_agency.status != "active":
        raise HTTPException(status_code=400, detail="Agence inactive ou suspendue")
    return current_agency