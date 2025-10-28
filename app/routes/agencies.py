# Routes API pour la gestion des agences
# Endpoints pour inscription, connexion et liste des agences

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, Numeric
from typing import List
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.agency_dependencies import get_current_active_agency
from app.models.agency import Agency, AgencyStatus
from app.models.route import Route
from app.models.schedule import Schedule
from app.models.reservation import Reservation, PaymentStatus
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
        email=agency_data.email,
        phone=agency_data.phone,
        password_hash=hashed_password
    )
    
    db.add(db_agency)
    db.commit()
    db.refresh(db_agency)
    return db_agency


@router.post("/login", response_model=AgencyToken)
def login_agency(login_data: AgencyLogin, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.email == login_data.email).first()
    
    if not agency or not AuthService.verify_password(login_data.password, agency.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    if agency.status != AgencyStatus.ACTIVE:
        agency.status = AgencyStatus.ACTIVE
        db.commit()
        db.refresh(agency)  
    
    access_token = AuthService.create_access_token(data={"sub": agency.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout_agency(current_agency: Agency = Depends(get_current_active_agency), db: Session = Depends(get_db)):
    return {
        "success": True,
        "message": "Déconnexion réussie",
        "agency_id": str(current_agency.id)
    }


@router.get("/me", response_model=AgencyResponse)
def get_agency_profile(current_agency: Agency = Depends(get_current_active_agency)):
    return current_agency


@router.get("/stats")
def get_agency_statistics(
    current_agency: Agency = Depends(get_current_active_agency),
    db: Session = Depends(get_db)
):
    active_trips = db.query(Schedule).join(Route).filter(
        Route.agency_id == current_agency.id,
        Schedule.departure_time > datetime.utcnow()
    ).count()
    
    total_passengers = db.query(Reservation).join(Schedule).join(Route).filter(
        Route.agency_id == current_agency.id,
        Reservation.payment_status == PaymentStatus.COMPLETED
    ).count()
    
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = first_day_of_month + timedelta(days=32)
    first_day_of_next_month = next_month.replace(day=1)
    
    monthly_revenue = db.query(
        func.sum(func.cast(Reservation.total_amount, Numeric))
    ).join(Schedule).join(Route).filter(
        Route.agency_id == current_agency.id,
        Reservation.payment_status == PaymentStatus.COMPLETED,
        Reservation.created_at >= first_day_of_month,
        Reservation.created_at < first_day_of_next_month
    ).scalar()
    
    monthly_revenue = float(monthly_revenue) if monthly_revenue else 0.0
    
    tickets_sold = db.query(Reservation).join(Schedule).join(Route).filter(
        Route.agency_id == current_agency.id,
        Reservation.payment_status == PaymentStatus.COMPLETED
    ).count()
    
    return {
        "agency_id": str(current_agency.id),
        "agency_name": current_agency.name,
        "active_trips": active_trips,
        "total_passengers": total_passengers,
        "monthly_revenue": round(monthly_revenue, 2),
        "tickets_sold": tickets_sold,
        "period": f"{first_day_of_month.strftime('%B %Y')}"
    }


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
