# Routes API pour la gestion des paiements KKiapay
# Fournit les infos au frontend et vérifie les transactions

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.payment import Payment, PaymentProvider, PaymentStatus as DBPaymentStatus
from app.models.reservation import Reservation, PaymentStatus as ReservationPaymentStatus
from app.services.kkiapay_service import kkiapay_service
from uuid import UUID

router = APIRouter(prefix="/payments", tags=["Payments"])

class PaymentInfoRequest(BaseModel):
    reservation_id: UUID

class PaymentVerifyRequest(BaseModel):
    transaction_id: str
    reservation_id: UUID

@router.post("/kkiapay/create")
def get_payment_info(request: PaymentInfoRequest, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == request.reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    
    if reservation.payment_status == ReservationPaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cette réservation est déjà payée")
    
    amount = float(reservation.total_amount)
    
    db_payment = Payment(
        reservation_id=reservation.id,
        provider=PaymentProvider.KKIAPAY,
        amount=amount,
        status=DBPaymentStatus.PENDING
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    passenger_info = reservation.passenger_info
    
    return {
        "success": True,
        "payment_id": str(db_payment.id),
        "amount": int(amount),
        "public_key": kkiapay_service.public_key,
        "sandbox": kkiapay_service.base_url.startswith("https://api-sandbox"),
        "reservation_id": str(reservation.id),
        "phone": passenger_info.get("phone", ""),
        "name": passenger_info.get("name", "")
    }

@router.post("/kkiapay/verify")
def verify_payment(request: PaymentVerifyRequest, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == request.reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    
    result = kkiapay_service.verify_transaction(request.transaction_id)
    
    if result["success"]:
        status = result.get("status", "").upper()
        
        if status in ["SUCCESS", "SUCCESSFUL"]:
            payment = db.query(Payment).filter(Payment.reservation_id == reservation.id).first()
            if payment:
                payment.status = DBPaymentStatus.SUCCESS
                payment.transaction_id = request.transaction_id
            
            reservation.payment_status = ReservationPaymentStatus.COMPLETED
            db.commit()
            
            return {
                "success": True,
                "message": "Paiement confirmé avec succès",
                "status": status,
                "reservation_id": str(reservation.id)
            }
        elif status in ["FAILED", "CANCELLED"]:
            return {
                "success": False,
                "message": "Paiement échoué",
                "status": status
            }
        else:
            return {
                "success": False,
                "message": "Paiement en attente",
                "status": status
            }
    else:
        return {
            "success": False,
            "message": result.get("message")
        }