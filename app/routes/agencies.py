# Routes API pour la gestion des agences
# Endpoints pour inscription, connexion et liste des agences

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.agency_dependencies import get_current_active_agency
from app.models.agency import Agency, AgencyStatus
from app.schemas.agency import AgencyRegister, AgencyLogin, AgencyResponse, AgencyToken
from app.services.auth import AuthService

router = APIRouter(prefix="/agencies", tags=["Agencies"])

@router.post("/register", response_model=AgencyResponse, status_code=201)
def register_agency(agency_data: AgencyRegister, db: Session = Depends(get_db)):
    existing_agency = db.query(Agency).filter(Agency.email == agency_data.email).first()
    if existing_agency:
        raise HTTPException(
            status_code=400,
            detail="Une agence avec cet email existe déjà"
        )
    
    hashed_password = AuthService.get_password_hash(agency_data.password)
    
    db_agency = Agency(
        name=agency_data.name,
        # contact=agency_data.contact,
        email=agency_data.email,
        phone=agency_data.phone,
        password_hash=hashed_password
    )
    
    db.add(db_agency)
    db.commit()
    db.refresh(db_agency)
    return db_agency


# router = APIRouter()

@router.post("/login", response_model=AgencyToken)
def login_agency(login_data: AgencyLogin, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.email == login_data.email).first()
    
    if not agency or not AuthService.verify_password(login_data.password, agency.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    # Mettre à jour le statut à ACTIVE si ce n'est pas déjà le cas
    if agency.status != AgencyStatus.ACTIVE:
        agency.status = AgencyStatus.ACTIVE
        db.commit()
        db.refresh(agency)  
    
    # Création du token
    access_token = AuthService.create_access_token(data={"sub": agency.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=AgencyResponse)
def get_agency_profile(current_agency: Agency = Depends(get_current_active_agency)):
    return current_agency

@router.get("/", response_model=List[AgencyResponse])
def list_agencies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    agencies = db.query(Agency).offset(skip).limit(limit).all()
    return agencies

@router.get("/{agency_id}", response_model=AgencyResponse)
def get_agency(agency_id: str, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agence non trouvée")
    return agency