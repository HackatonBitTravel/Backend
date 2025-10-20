# Modèle de données pour les horaires de départ
# Représente un programme de voyage avec heure, prix et places disponibles

from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    route = relationship("Route", backref="schedules")