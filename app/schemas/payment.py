# Schémas Pydantic pour les paiements
# Définit la structure des données de paiement

from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class PaymentInitiate(BaseModel):
    reservation_id: UUID

class PaymentResponse(BaseModel):
    success: bool
    message: str
    payment_url: Optional[str] = None
    request_id: Optional[str] = None

class PaymentVerify(BaseModel):
    transaction_id: str

class PaymentWebhook(BaseModel):
    transactionId: str
    status: str
    amount: float