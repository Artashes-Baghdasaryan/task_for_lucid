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