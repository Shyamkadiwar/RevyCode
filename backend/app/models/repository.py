from datetime import datetime
from typing import Optional, List, Dict
from beanie import Document, Link
from pydantic import Field
from .user import User


class Repository(Document):
    user: Link[User]
    
    repo_github_id: int
    repo_full_name: str
    repo_name: str
    repo_owner: str
    
    default_branch: str = "main"
    language_primary: Optional[str] = None
    languages_detected: List[str] = []
    
    webhook_id: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "repositories"
        indexes = [
            "repo_full_name",
            "repo_github_id",
        ]