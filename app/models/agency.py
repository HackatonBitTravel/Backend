
from sqlalchemy import Column, String, Float, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class AgencyStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"

class Agency(Base):
    __tablename__ = "agencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    # contact = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    rating = Column(Float, default=0.0)
    public_key = Column(String(255), nullable=True)
    private_key = Column(String(255), nullable=True)
    status = Column(Enum(AgencyStatus), default=AgencyStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)