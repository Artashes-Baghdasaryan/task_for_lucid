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