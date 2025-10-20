# Modèle de données pour les utilisateurs
# Représente un utilisateur de la plateforme avec authentification

from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    USER = "user"
    AGENCY = "agency"
    CONTROLLER = "controller"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)