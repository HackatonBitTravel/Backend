# Routes API pour les paiements Lightning Network
# Endpoints pour créer et vérifier les factures Lightning

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.payment import Payment, PaymentProvider, PaymentStatus as DBPaymentStatus
from app.models.reservation import Reservation, PaymentStatus as ReservationPaymentStatus
from app.services.lightning_service import lightning_service
from uuid import UUID

router = APIRouter(prefix="/payments/lightning", tags=["Lightning Payments"])

class LightningInvoiceRequest(BaseModel):
    reservation_id: UUID

class LightningVerifyRequest(BaseModel):
    payment_hash: str
    reservation_id: UUID

@router.post("/create-invoice")
def create_lightning_invoice(request: LightningInvoiceRequest, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == request.reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    
    if reservation.payment_status == ReservationPaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cette réservation est déjà payée")
    
    amount_fcfa = float(reservation.total_amount)
    memo = f"Ticket BitTravel #{str(reservation.id)[:8]}"
    
    result = lightning_service.create_invoice(amount_fcfa, memo)
    
    if result["success"]:
        db_payment = Payment(
            reservation_id=reservation.id,
            provider=PaymentProvider.BITCOIN,
            amount=amount_fcfa,
            transaction_id=result.get("invoice_id"),
            status=DBPaymentStatus.PENDING
        )
        db.add(db_payment)
        db.commit()
        
        return {
            "success": True,
            "message": "Facture Lightning créée",
            "invoice": result.get("invoice"),
            "invoice_id": result.get("invoice_id"),
            "checkout_link": result.get("checkout_link"),
            "amount_fcfa": amount_fcfa,
            "amount_usd": result.get("amount_usd"),
            "qr_code": result.get("qr_code"),
            "payment_id": str(db_payment.id)
        }
    else:
        return {
            "success": False,
            "message": result.get("message")
        }
from fastapi import Request

@router.post("/webhook")
async def lightning_webhook(request: Request, db: Session = Depends(get_db)):

    payload = await request.json()

    payment_hash = payload.get("payment_hash")
    status = payload.get("status")  

    if not payment_hash:
        raise HTTPException(status_code=400, detail="payment_hash manquant")

 
    payment = db.query(Payment).filter(Payment.transaction_id == payment_hash).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")

    if status == "paid":
        payment.status = DBPaymentStatus.SUCCESS
        reservation = db.query(Reservation).filter(Reservation.id == payment.reservation_id).first()
        if reservation:
            reservation.payment_status = ReservationPaymentStatus.COMPLETED

        db.commit()
        return {"success": True, "message": "Paiement confirmé via webhook"}

    elif status == "expired":
        payment.status = DBPaymentStatus.FAILED
        db.commit()
        return {"success": True, "message": "Facture expirée"}

    else:
        return {"success": True, "message": f"Statut reçu : {status}"}

@router.post("/verify")
def verify_lightning_payment(request: LightningVerifyRequest, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == request.reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    
    result = lightning_service.check_invoice(request.payment_hash)
    
    if result["success"]:
        if result.get("paid"):
            payment = db.query(Payment).filter(Payment.reservation_id == reservation.id, Payment.provider == PaymentProvider.BITCOIN).first()
            if payment:
                payment.status = DBPaymentStatus.SUCCESS
                payment.transaction_id = request.payment_hash
            
            reservation.payment_status = ReservationPaymentStatus.COMPLETED
            db.commit()
            
            return {
                "success": True,
                "message": "Paiement Lightning confirmé",
                "paid": True,
                "reservation_id": str(reservation.id)
            }
        else:
            return {
                "success": True,
                "message": "Facture non encore payée",
                "paid": False,
                "status": result.get("status")
            }
    else:
        return {
            "success": False,
            "message": result.get("message")
        }

@router.get("/check/{payment_hash}")
def check_lightning_status(payment_hash: str):
    result = lightning_service.check_invoice(payment_hash)
    
    if result["success"]:
        return {
            "success": True,
            "paid": result.get("paid"),
            "amount": result.get("amount")
        }
    else:
        return {
            "success": False,
            "message": result.get("message")
        }