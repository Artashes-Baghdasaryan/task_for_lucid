from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from config import settings
from repositories.user_repository import UserRepository
from schemas.user import UserCreate, UserLogin, TokenResponse
from models.user import User

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def signup(self, user_data: UserCreate) -> Optional[TokenResponse]:
        """Register a new user."""
        # Check if user already exists
        if self.user_repo.get_by_email(user_data.email):
            return None
        
        # Hash password and create user
        hashed_password = self.get_password_hash(user_data.password)
        user = self.user_repo.create(user_data, hashed_password)
        
        if not user:
            return None
        
        # Create token
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return TokenResponse(token=access_token)
    
    def login(self, login_data: UserLogin) -> Optional[TokenResponse]:
        """Authenticate user and return token."""
        user = self.user_repo.get_by_email(login_data.email)
        
        if not user or not self.user_repo.is_active(user):
            return None
        
        if not self.verify_password(login_data.password, user.hashed_password):
            return None
        
        # Create token
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return TokenResponse(token=access_token)
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token."""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = self.user_repo.get_by_id(int(user_id))
        if not user or not self.user_repo.is_active(user):
            return None
        
        return user