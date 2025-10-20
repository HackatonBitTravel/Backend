# Modèle de données pour les réservations
# Représente une réservation de ticket par un passager

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("schedules.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    passenger_info = Column(JSON, nullable=False)
    seat_number = Column(Integer, nullable=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    total_amount = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    schedule = relationship("Schedule", backref="reservations")
    user = relationship("User", backref="reservations")