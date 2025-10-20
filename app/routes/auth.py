# Routes API pour l'authentification des utilisateurs
# Endpoints pour inscription, connexion et profil utilisateur

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister, UserResponse, Token, UserLogin
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    hashed_password = AuthService.get_password_hash(user_data.password)
    
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        password_hash=hashed_password,
        role=UserRole.USER
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not AuthService.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    access_token = AuthService.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user