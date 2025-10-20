# Modèle de données pour les itinéraires de transport
# Représente un trajet entre deux villes proposé par une agence

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id"), nullable=False)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agency = relationship("Agency", backref="routes")