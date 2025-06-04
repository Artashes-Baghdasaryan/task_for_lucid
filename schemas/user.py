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