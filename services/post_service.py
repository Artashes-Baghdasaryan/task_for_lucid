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