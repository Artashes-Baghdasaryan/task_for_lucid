from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.user import User
from schemas.user import UserCreate
from typing import Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create(self, user_data: UserCreate, hashed_password: str) -> Optional[User]:
        """Create a new user."""
        try:
            db_user = User(
                email=user_data.email,
                hashed_password=hashed_password
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            return None
    
    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active if user else False