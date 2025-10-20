# Routes API pour la gestion des réservations
# Endpoints pour créer et gérer les réservations de tickets

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.reservation import Reservation, PaymentStatus
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationResponse

router = APIRouter(prefix="/reservations", tags=["Reservations"])

@router.post("/", response_model=ReservationResponse, status_code=201)
async def create_reservation(
    reservation: ReservationCreate,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    schedule = db.query(Schedule).filter(Schedule.id == reservation.schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Horaire non trouvé")
    
    if schedule.available_seats <= 0:
        raise HTTPException(status_code=400, detail="Plus de places disponibles")
    
    user_id = None
    final_price = schedule.price
    
    if authorization and authorization.startswith("Bearer "):
        from app.services.auth import AuthService
        token = authorization.replace("Bearer ", "")
        payload = AuthService.verify_token(token)
        if payload:
            email = payload.get("sub")
            user = db.query(User).filter(User.email == email).first()
            if user:
                user_id = user.id
                final_price = schedule.price * 0.9
    
    seat_number = schedule.seats - schedule.available_seats + 1
    
    db_reservation = Reservation(
        schedule_id=reservation.schedule_id,
        user_id=user_id,
        passenger_info=reservation.passenger_info.model_dump(),
        seat_number=seat_number,
        payment_status=PaymentStatus.PENDING,
        total_amount=str(final_price)
    )
    
    schedule.available_seats -= 1
    
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

@router.get("/", response_model=List[ReservationResponse])
def list_reservations(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    reservations = db.query(Reservation).offset(skip).limit(limit).all()
    return reservations

@router.get("/my-reservations", response_model=List[ReservationResponse])
def get_my_reservations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    reservations = db.query(Reservation).filter(
        Reservation.user_id == current_user.id
    ).order_by(Reservation.created_at.desc()).all()
    return reservations

@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(reservation_id: str, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    return reservation