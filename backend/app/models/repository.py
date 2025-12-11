from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document, Link
from pydantic import BaseModel, Field
from .user import User

class AgentSettings(BaseModel):
    enabled: bool = True
    auto_comment: bool = True
    min_confidence: Optional[float] = None
    severity_threshold: Optional[str] = None
    complexity_threshold: Optional[int] = None
    coverage_threshold: Optional[float] = None

class RepositorySettings(BaseModel):
    auto_review_on_pr: bool = True
    auto_review_on_commit: bool = False
    review_on_draft: bool = False
    agents_enabled: Dict[str, AgentSettings] = {
        "pr_analyzer": AgentSettings(enabled=True, auto_comment=True, min_confidence=0.7),
        "security": AgentSettings(enabled=True, auto_comment=True, severity_threshold="medium"),
        "code_quality": AgentSettings(enabled=True, auto_comment=False, complexity_threshold=10),
        "test_coverage": AgentSettings(enabled=True, coverage_threshold=80.0),
        "documentation": AgentSettings(enabled=False)
    }
    ignore_paths: List[str] = ["node_modules/**", "*.min.js", "dist/**"]
    comment_style: str = "detailed"

class RepositoryStatistics(BaseModel):
    total_reviews: int = 0
    total_comments: int = 0
    issues_found: int = 0
    issues_resolved: int = 0
    avg_review_time_seconds: float = 0.0

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
    
    settings: RepositorySettings = Field(default_factory=RepositorySettings)
    statistics: RepositoryStatistics = Field(default_factory=RepositoryStatistics)
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_review: Optional[datetime] = None
    
    class Settings:
        name = "repositories"
        indexes = [
            "repo_full_name",
            "repo_github_id",
            "is_active"
        ]