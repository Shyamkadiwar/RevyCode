from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document, Link
from pydantic import BaseModel, Field
from .user import User
from .repository import Repository

class FileChange(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch_preview: Optional[str] = None

class AgentOutput(BaseModel):
    summary: Optional[str] = None
    new_features: List[str] = []
    security_enhancements: List[str] = []
    code_quality_issues: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    walkthrough: Optional[str] = None
    vulnerabilities: List[Dict[str, Any]] = []
    passed_checks: List[str] = []

class AgentExecution(Document):
    review_id: str  # Stored as string to avoid circular dependency issues if using Link
    repo_id: Link[Repository]
    user_id: Link[User]
    
    agent_name: str
    agent_version: str
    
    execution_metadata: Dict[str, Any] = {}
    resource_usage: Dict[str, Any] = {}
    tools_used: List[Dict[str, Any]] = []
    memory_snapshot: List[Any] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "agent_executions"
        indexes = [
            "review_id",
            "agent_name",
            "created_at"
        ]

class AgentResult(BaseModel):
    agent_name: str
    agent_version: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    
    output: AgentOutput = Field(default_factory=AgentOutput)
    
    tokens_used: Dict[str, int] = {}
    cost_usd: float = 0.0
    
    posted_to_github: bool = False
    github_comment_id: Optional[int] = None
    github_comment_url: Optional[str] = None

class InlineComment(Document):
    review_id: str
    repo_id: Link[Repository]
    pr_number: int
    
    file_path: str
    line_number: int
    position: Optional[int] = None
    
    comment_text: str
    agent_name: str
    comment_type: str
    severity: str
    
    code_snippet: Optional[str] = None
    suggested_fix: Optional[str] = None
    
    github_comment_id: Optional[int] = None
    github_comment_url: Optional[str] = None
    
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_comment: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "inline_comments"
        indexes = [
            "review_id",
            "resolved"
        ]

class Review(Document):
    repo_id: Link[Repository]
    user_id: Link[User]
    
    pr_number: int
    pr_title: str
    pr_description: Optional[str] = None
    pr_url: str
    pr_author: str
    pr_branch: str
    pr_base_branch: str
    
    commit_sha: str
    commit_message: str
    
    files_changed: List[FileChange] = []
    total_additions: int = 0
    total_deletions: int = 0
    total_files_changed: int = 0
    
    agent_results: List[AgentResult] = []
    
    overall_status: str = "pending"
    overall_score: Optional[float] = None
    issues_found: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    
    review_trigger: str = "webhook"
    review_mode: str = "automatic"
    processing_time_total_ms: Optional[float] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "reviews"
        indexes = [
            "repo_id",
            "pr_number",
            "overall_status",
            "user_id"
        ]