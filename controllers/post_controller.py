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