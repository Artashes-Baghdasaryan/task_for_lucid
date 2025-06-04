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