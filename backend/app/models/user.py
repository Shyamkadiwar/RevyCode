from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import BaseModel, Field, EmailStr
from enum import Enum

class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class UserPreferences(BaseModel):
    auto_review_enabled: bool = True
    notification_email: bool = True
    notification_github: bool = True
    default_agents: List[str] = ["pr_analyzer", "security", "code_quality"]
    review_language: str = "english"
    verbosity_level: str = "detailed"

class UserSubscription(BaseModel):
    tier: SubscriptionTier = SubscriptionTier.FREE
    reviews_used: int = 0
    reviews_limit: int = 200
    reset_date: datetime = Field(default_factory=datetime.utcnow)

class User(Document):
    github_user_id: int
    github_username: str
    email: Optional[EmailStr] = None
    github_access_token: str
    avatar_url: Optional[str] = None
    name: Optional[str] = None
    
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    subscription: UserSubscription = Field(default_factory=UserSubscription)
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            "github_username",
            "github_user_id",
            "email"
        ]