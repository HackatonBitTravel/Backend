# Routes API pour les paiements Lightning Network
# Endpoints pour créer et vérifier les factures Lightning

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.core.database import get_db
from app.models.payment import Payment, PaymentProvider
from app.models.reservation import Reservation, PaymentStatus as ReservationPaymentStatus
from app.services.lightning_service import lightning_service
from uuid import UUID
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments/lightning", tags=["Lightning Payments"])

# SOLUTION : Fonction de mapping pour contourner le problème d'enum
def set_payment_status_raw(db: Session, payment_id: UUID, status: str):
    """
    Met à jour le statut d'un paiement en utilisant du SQL brut
    pour contourner les contraintes d'enum de SQLAlchemy
    """
    try:
        # Mapping : notre code Python -> valeur PostgreSQL
        status_mapping = {
            "SUCCESS": "success",    
            "COMPLETED": "success",
            "PENDING": "pending",
            "FAILED": "failed",
            "CANCELLED": "cancelled"
        }
        
        db_status = status_mapping.get(status.upper(), status.lower())
        
        query = text("""
            UPDATE payments 
            SET status = :status, updated_at = NOW() 
            WHERE id = :payment_id
        """)
        
        db.execute(query, {"status": db_status, "payment_id": str(payment_id)})
        db.commit()
        
        logger.info(f"Statut du paiement {payment_id} mis à jour vers '{db_status}'")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du statut: {str(e)}")
        db.rollback()
        return False

class LightningInvoiceRequest(BaseModel):
    reservation_id: UUID

class LightningVerifyRequest(BaseModel):
    payment_hash: str
    reservation_id: UUID

@router.post("/create-invoice")
def create_lightning_invoice(request: LightningInvoiceRequest, db: Session = Depends(get_db)):
    try:
        reservation = db.query(Reservation).filter(Reservation.id == request.reservation_id).first()
        if not reservation:
            raise HTTPException(status_code=404, detail="Réservation non trouvée")
        
        if reservation.payment_status == ReservationPaymentStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Cette réservation est déjà payée")
        
        amount_fcfa = float(reservation.total_amount)
        memo = f"Ticket BitTravel #{str(reservation.id)[:8]}"
        
        result = lightning_service.create_invoice(amount_fcfa, memo)
        
        if result["success"]:
            # Créer le paiement avec statut PENDING (celui-ci fonctionne)
            db_payment = Payment(
                reservation_id=reservation.id,
                provider=PaymentProvider.BITCOIN,
                amount=amount_fcfa,
                transaction_id=result.get("invoice_id")
            )
            # Le statut PENDING est défini par défaut, pas besoin de le spécifier
            
            db.add(db_payment)
            db.commit()
            db.refresh(db_payment)
            
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la création de la facture Lightning: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.post("/webhook")
async def lightning_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook appelé par le service Lightning lorsqu'une facture est payée
    """
    try:
        # Log de la requête entrante
        logger.info("Webhook Lightning reçu")
        
        # Récupération et validation du payload
        payload = await request.json()
        logger.info(f"Payload webhook: {payload}")
        
        payment_hash = payload.get("payment_hash")
        status = payload.get("status")
        
        # Validation des données requises
        if not payment_hash:
            logger.error("payment_hash manquant dans le webhook")
            raise HTTPException(status_code=400, detail="payment_hash manquant")
        
        if not status:
            logger.error("status manquant dans le webhook")
            raise HTTPException(status_code=400, detail="status manquant")
        
        # Recherche du paiement
        payment = db.query(Payment).filter(
            Payment.transaction_id == payment_hash
        ).first()
        
        if not payment:
            logger.warning(f"Paiement non trouvé pour payment_hash: {payment_hash}")
            raise HTTPException(status_code=404, detail="Paiement non trouvé")
        
        logger.info(f"Paiement trouvé: {payment.id}, statut actuel: {payment.status}")
        
        # Traitement selon le statut
        if status == "paid":
            # Utiliser la fonction de mapping pour mettre à jour le statut
            success = set_payment_status_raw(db, payment.id, "SUCCESS")
            
            if not success:
                raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du statut")
            
            # Mise à jour de la réservation
            reservation = db.query(Reservation).filter(
                Reservation.id == payment.reservation_id
            ).first()
            
            if reservation:
                reservation.payment_status = ReservationPaymentStatus.COMPLETED
                db.commit()
                logger.info(f"Réservation {reservation.id} marquée comme payée")
            else:
                logger.error(f"Réservation non trouvée pour payment_id: {payment.id}")
            
            logger.info(f"Paiement {payment.id} confirmé via webhook")
            
            return {
                "success": True,
                "message": "Paiement confirmé via webhook",
                "payment_id": str(payment.id),
                "reservation_id": str(payment.reservation_id)
            }
        
        elif status == "expired":
            # Utiliser la fonction de mapping
            set_payment_status_raw(db, payment.id, "FAILED")
            logger.info(f"Facture {payment_hash} expirée")
            
            return {
                "success": True,
                "message": "Facture expirée",
                "payment_id": str(payment.id)
            }
        
        else:
            logger.info(f"Statut webhook non géré: {status}")
            return {
                "success": True,
                "message": f"Statut reçu : {status}"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur dans le webhook Lightning: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.post("/verify")
def verify_lightning_payment(request: LightningVerifyRequest, db: Session = Depends(get_db)):
    try:
        reservation = db.query(Reservation).filter(Reservation.id == request.reservation_id).first()
        if not reservation:
            raise HTTPException(status_code=404, detail="Réservation non trouvée")
        
        result = lightning_service.check_invoice(request.payment_hash)
        
        if result["success"]:
            if result.get("paid"):
                payment = db.query(Payment).filter(
                    Payment.reservation_id == reservation.id,
                    Payment.provider == PaymentProvider.BITCOIN
                ).first()
                
                if payment:
                    # Utiliser la fonction de mapping
                    set_payment_status_raw(db, payment.id, "SUCCESS")
                    
                    # Mettre à jour le transaction_id si nécessaire
                    if payment.transaction_id != request.payment_hash:
                        query = text("""
                            UPDATE payments 
                            SET transaction_id = :tx_id 
                            WHERE id = :payment_id
                        """)
                        db.execute(query, {
                            "tx_id": request.payment_hash,
                            "payment_id": str(payment.id)
                        })
                
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du paiement: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/check/{payment_hash}")
def check_lightning_status(payment_hash: str):
    try:
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
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")