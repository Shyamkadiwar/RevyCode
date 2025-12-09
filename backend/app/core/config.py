from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str
    DATABASE_NAME: str = "ai_code_review"
    
    # GitHub
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_CALLBACK_URL: str
    
    # Gemini
    GEMINI_API_KEY: str
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENCRYPTION_KEY: str
    
    # App
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"


settings = Settings()