from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import AuthService
from schemas.user import UserCreate, UserLogin, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user and return authentication token."""
    auth_service = AuthService(db)
    token = auth_service.signup(user_data)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered or registration failed"
        )
    
    return token

@router.post("/login", response_model=TokenResponse)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user and return authentication token."""
    auth_service = AuthService(db)
    token = auth_service.login(login_data)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return token