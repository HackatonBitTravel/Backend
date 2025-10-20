# Modèle de données pour les tickets
# Représente un ticket signé numériquement pour un voyage

from sqlalchemy import Column, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class TicketStatus(str, enum.Enum):
    VALID = "valid"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=False)
    payload = Column(Text, nullable=False)
    signature = Column(String(255), nullable=False)
    public_key = Column(String(255), nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.VALID)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reservation = relationship("Reservation", backref="tickets")