from datetime import datetime
from typing import Optional, List
from beanie import Document, Link
from pydantic import Field, BaseModel
from enum import Enum
from .user import User
from .repository import Repository


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class FileChange(BaseModel):
    filename: str
    status: str
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = None


class AgentResult(BaseModel):
    agent_name: str
    status: str
    execution_time_ms: int = 0
    output: Dict = {}
    posted_to_github: bool = False


class Review(Document):
    user: Link[User]
    repository: Link[Repository]
    
    pr_number: int
    pr_title: str
    pr_url: str
    pr_author: str
    pr_branch: str
    
    commit_sha: str
    
    files_changed: List[FileChange] = []
    agent_results: List[AgentResult] = []
    
    overall_status: ReviewStatus = ReviewStatus.PENDING
    issues_found: int = 0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "reviews"
        indexes = [
            "pr_number",
            "overall_status",
        ]