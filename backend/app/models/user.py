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
    auto_review_enabled : bool = True
    notifiacation_email : bool = True
    default_agents : List[str] = ["pr_analyzer, security"]
    verbosity_level : str = "detailed" 

class User(Document):
    github_user_id : int
    github_username : str
    github_email : Optional[EmailStr] = None
    github_encypted_token : str
    avatar_url : Optional[str] = None
    name : Optional[str] = None
    preferences : UserPreferences = Field(default_factory = UserPreferences)
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE

    is_active: bool = True
    created_at : datetime = Field(default_factory=datetime.utcnow)
    updated_at : datetime = Field(default_factory=datetime.utcnow)

class Setting:
    name = "users"
    indexes = [
        "github_username",
        "github_user_id"
    ]