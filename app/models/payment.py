# Modèle de données pour les paiements
# Trace toutes les transactions de paiement

from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class PaymentProvider(str, enum.Enum):
    KKIAPAY = "kkiapay"
    BITCOIN = "bitcoin"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=False)
    provider = Column(Enum(PaymentProvider), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_id = Column(String(255), nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reservation = relationship("Reservation", backref="payments")