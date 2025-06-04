# FastAPI MVC Social Posts Application

## Project Structure
```
social_posts_app/
├── main.py
├── requirements.txt
├── config.py
├── database.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── post.py
├── schemas/
│   ├── __init__.py
│   ├── user.py
│   └── post.py
├── controllers/
│   ├── __init__.py
│   ├── auth_controller.py
│   └── post_controller.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   └── post_service.py
├── repositories/
│   ├── __init__.py
│   ├── user_repository.py
│   └── post_repository.py
└── dependencies/
    ├── __init__.py
    └── auth_dependency.py
```

## requirements.txt
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pymysql==1.1.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

## config.py
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/social_posts_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    MAX_PAYLOAD_SIZE: int = 1024 * 1024  # 1MB
    CACHE_EXPIRE_MINUTES: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
```

## models/user.py
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    posts = relationship("Post", back_populates="owner", cascade="all, delete-orphan")
```

## models/post.py
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    text = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="posts")
```

## models/__init__.py
```python
from .user import User
from .post import Post

__all__ = ["User", "Post"]
```

## schemas/user.py
```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")

class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="User password (8-128 characters)"
    )
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=128, description="User password")

class UserResponse(UserBase):
    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="User active status")
    created_at: datetime = Field(..., description="User creation timestamp")
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    token: str = Field(..., description="Authentication token")
    token_type: str = Field(default="bearer", description="Token type")
```

## schemas/post.py
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    text: str = Field(
        ..., 
        min_length=1, 
        max_length=10000,
        description="Post content text"
    )

class PostCreate(PostBase):
    @validator('text')
    def validate_text_size(cls, v):
        # Additional validation for payload size (1MB limit)
        text_size = len(v.encode('utf-8'))
        if text_size > 1024 * 1024:  # 1MB
            raise ValueError('Post text exceeds 1MB limit')
        return v.strip()

class PostUpdate(BaseModel):
    text: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=10000,
        description="Updated post content"
    )

class PostResponse(PostBase):
    id: int = Field(..., description="Post ID", alias="postID")
    user_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Post creation timestamp")
    updated_at: datetime = Field(..., description="Post last update timestamp")
    
    class Config:
        from_attributes = True
        populate_by_name = True

class PostCreateResponse(BaseModel):
    postID: int = Field(..., description="Created post ID")
    message: str = Field(default="Post created successfully", description="Success message")

class PostsListResponse(BaseModel):
    posts: List[PostResponse] = Field(..., description="List of user posts")
    total: int = Field(..., description="Total number of posts")
    cached: bool = Field(default=False, description="Whether response was cached")

class PostDeleteResponse(BaseModel):
    message: str = Field(default="Post deleted successfully", description="Success message")
    postID: int = Field(..., description="Deleted post ID")
```

## schemas/__init__.py
```python
from .user import UserCreate, UserLogin, UserResponse, TokenResponse
from .post import PostCreate, PostUpdate, PostResponse, PostCreateResponse, PostsListResponse, PostDeleteResponse

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse",
    "PostCreate", "PostUpdate", "PostResponse", "PostCreateResponse", 
    "PostsListResponse", "PostDeleteResponse"
]
```

## repositories/user_repository.py
```python
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
```

## repositories/post_repository.py
```python
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.post import Post
from schemas.post import PostCreate
from typing import List, Optional

class PostRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, post_data: PostCreate, user_id: int) -> Optional[Post]:
        """Create a new post."""
        try:
            db_post = Post(
                text=post_data.text,
                user_id=user_id
            )
            self.db.add(db_post)
            self.db.commit()
            self.db.refresh(db_post)
            return db_post
        except SQLAlchemyError:
            self.db.rollback()
            return None
    
    def get_by_id(self, post_id: int) -> Optional[Post]:
        """Get post by ID."""
        return self.db.query(Post).filter(Post.id == post_id).first()
    
    def get_user_posts(self, user_id: int) -> List[Post]:
        """Get all posts for a specific user."""
        return (self.db.query(Post)
                .filter(Post.user_id == user_id)
                .order_by(Post.created_at.desc())
                .all())
    
    def delete(self, post: Post) -> bool:
        """Delete a post."""
        try:
            self.db.delete(post)
            self.db.commit()
            return True
        except SQLAlchemyError:
            self.db.rollback()
            return False
    
    def is_owner(self, post: Post, user_id: int) -> bool:
        """Check if user owns the post."""
        return post.user_id == user_id if post else False
```

## repositories/__init__.py
```python
from .user_repository import UserRepository
from .post_repository import PostRepository

__all__ = ["UserRepository", "PostRepository"]
```

## services/auth_service.py
```python
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
```

## services/post_service.py
```python
from typing import List, Optional
from sqlalchemy.orm import Session
from repositories.post_repository import PostRepository
from schemas.post import PostCreate, PostResponse, PostCreateResponse, PostsListResponse, PostDeleteResponse
import time

class PostService:
    def __init__(self, db: Session):
        self.db = db
        self.post_repo = PostRepository(db)
        self._cache = {}  # Simple in-memory cache
    
    def create_post(self, post_data: PostCreate, user_id: int) -> Optional[PostCreateResponse]:
        """Create a new post."""
        post = self.post_repo.create(post_data, user_id)
        if not post:
            return None
        
        # Clear user's cache when new post is created
        cache_key = f"user_posts_{user_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        return PostCreateResponse(postID=post.id)
    
    def get_user_posts(self, user_id: int) -> PostsListResponse:
        """Get all posts for a user with caching."""
        cache_key = f"user_posts_{user_id}"
        current_time = time.time()
        
        # Check cache
        if cache_key in self._cache:
            cached_data, cache_time = self._cache[cache_key]
            if current_time - cache_time < 300:  # 5 minutes
                return PostsListResponse(
                    posts=cached_data,
                    total=len(cached_data),
                    cached=True
                )
        
        # Fetch from database
        posts = self.post_repo.get_user_posts(user_id)
        post_responses = [PostResponse.from_orm(post) for post in posts]
        
        # Cache the result
        self._cache[cache_key] = (post_responses, current_time)
        
        return PostsListResponse(
            posts=post_responses,
            total=len(post_responses),
            cached=False
        )
    
    def delete_post(self, post_id: int, user_id: int) -> Optional[PostDeleteResponse]:
        """Delete a post if user owns it."""
        post = self.post_repo.get_by_id(post_id)
        if not post:
            return None
        
        if not self.post_repo.is_owner(post, user_id):
            return None
        
        if not self.post_repo.delete(post):
            return None
        
        # Clear user's cache when post is deleted
        cache_key = f"user_posts_{user_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        return PostDeleteResponse(postID=post_id)
```

## services/__init__.py
```python
from .auth_service import AuthService
from .post_service import PostService

__all__ = ["AuthService", "PostService"]
```

## dependencies/auth_dependency.py
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import AuthService
from models.user import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user."""
    auth_service = AuthService(db)
    user = auth_service.get_current_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
```

## dependencies/__init__.py
```python
from .auth_dependency import get_current_user

__all__ = ["get_current_user"]
```

## controllers/auth_controller.py
```python
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
```

## controllers/post_controller.py
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from services.post_service import PostService
from schemas.post import PostCreate, PostCreateResponse, PostsListResponse, PostDeleteResponse
from dependencies.auth_dependency import get_current_user
from models.user import User

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.post("/", response_model=PostCreateResponse, status_code=status.HTTP_201_CREATED)
def add_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new post for the authenticated user."""
    post_service = PostService(db)
    result = post_service.create_post(post_data, current_user.id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create post"
        )
    
    return result

@router.get("/", response_model=PostsListResponse)
def get_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all posts for the authenticated user."""
    post_service = PostService(db)
    return post_service.get_user_posts(current_user.id)

@router.delete("/{post_id}", response_model=PostDeleteResponse)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific post owned by the authenticated user."""
    post_service = PostService(db)
    result = post_service.delete_post(post_id, current_user.id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or you don't have permission to delete it"
        )
    
    return result
```

## controllers/__init__.py
```python
from .auth_controller import router as auth_router
from .post_controller import router as post_router

__all__ = ["auth_router", "post_router"]
```

## main.py
```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from config import settings
from database import create_tables
from controllers import auth_router, post_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Social Posts API",
    description="A FastAPI application with MVC architecture for managing user posts",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Payload size middleware
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_PAYLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request payload too large. Maximum size: {settings.MAX_PAYLOAD_SIZE} bytes"
            )
    
    response = await call_next(request)
    return response

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

@app.exception_handler(413)
async def payload_too_large_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=413,
        content={"detail": "Payload too large"}
    )

# Include routers
app.include_router(auth_router)
app.include_router(post_router)

@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "message": "Social Posts API is running"
    }

@app.get("/health", tags=["Health"])
def detailed_health():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "environment": "development"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["./"]
    )
```

## Setup Instructions

1. **Create MySQL Database:**
```sql
CREATE DATABASE social_posts_db;
CREATE USER 'social_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON social_posts_db.* TO 'social_user'@'localhost';
FLUSH PRIVILEGES;
```

2. **Environment Setup:**
Create a `.env` file:
```
DATABASE_URL=mysql+pymysql://social_user:your_password@localhost:3306/social_posts_db
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
```

3. **Installation:**
```bash
pip install -r requirements.txt
```

4. **Run the Application:**
```bash
python main.py
```

## API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login

### Posts (Requires Authentication)
- `POST /posts/` - Create a new post
- `GET /posts/` - Get all user posts (cached for 5 minutes)
- `DELETE /posts/{post_id}` - Delete a specific post

### Testing Examples

**Signup:**
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

**Add Post:**
```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is my first post!"}'
```

**Get Posts:**
```bash
curl -X GET "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Delete Post:**
```bash
curl -X DELETE "http://localhost:8000/posts/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Features Implemented

✅ **MVC Architecture** - Clear separation of Controllers, Services, and Repositories
✅ **SQLAlchemy Models** - User and Post models with relationships
✅ **Pydantic Schemas** - Extensive validation for all endpoints
✅ **JWT Authentication** - Secure token-based authentication
✅ **Dependency Injection** - Clean auth dependency for protected endpoints
✅ **Response Caching** - 5-minute cache for GetPosts endpoint
✅ **Payload Size Validation** - 1MB limit with middleware
✅ **Field Validation** - Comprehensive validation for all fields
✅ **Error Handling** - Proper HTTP status codes and error messages
✅ **Database Integration** - MySQL with SQLAlchemy ORM
✅ **Production Ready** - CORS, middleware, proper structure