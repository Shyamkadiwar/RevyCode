"""
Review Routes - API endpoints for managing PR reviews
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from beanie import PydanticObjectId
from app.api import deps
from app.models.user import User
from app.models.repository import Repository
from app.models.review import Review
from app.services.review_service import ReviewService

router = APIRouter()

class TriggerReviewRequest(BaseModel):
    """Request to trigger a PR review"""
    repository_id: str
    pr_number: int
    post_to_github: bool = True

class ReviewResponse(BaseModel):
    """Review response model"""
    id: str
    pr_number: int
    pr_title: str
    pr_url: str
    overall_status: str
    issues_found: int
    high_issues: int
    medium_issues: int
    low_issues: int
    created_at: str
    completed_at: Optional[str] = None

@router.post("/analyze", response_model=ReviewResponse)
async def trigger_review(
    request: TriggerReviewRequest,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Manually trigger a PR review
    
    Endpoint: POST /reviews/analyze
    Auth: Required (JWT)
    """
    # Get repository
    try:
        repo = await Repository.get(PydanticObjectId(request.repository_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Verify user owns the repository
    if str(repo.user.ref.id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to review this repository")
    
    # Trigger review
    review_service = ReviewService()
    try:
        review = await review_service.trigger_review(
            repo=repo,
            pr_number=request.pr_number,
            user=current_user,
            post_to_github=request.post_to_github
        )
        
        return ReviewResponse(
            id=str(review.id),
            pr_number=review.pr_number,
            pr_title=review.pr_title,
            pr_url=review.pr_url,
            overall_status=review.overall_status,
            issues_found=review.issues_found,
            high_issues=review.high_issues,
            medium_issues=review.medium_issues,
            low_issues=review.low_issues,
            created_at=review.created_at.isoformat(),
            completed_at=review.completed_at.isoformat() if review.completed_at else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger review: {str(e)}")

@router.get("/{review_id}", response_model=dict)
async def get_review(
    review_id: str,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get review details by ID
    
    Endpoint: GET /reviews/{review_id}
    Auth: Required (JWT)
    """
    try:
        review = await Review.get(PydanticObjectId(review_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Verify user owns the review
    if str(review.user_id.ref.id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this review")
    
    # Return full review data
    return {
        "id": str(review.id),
        "pr_number": review.pr_number,
        "pr_title": review.pr_title,
        "pr_description": review.pr_description,
        "pr_url": review.pr_url,
        "pr_author": review.pr_author,
        "overall_status": review.overall_status,
        "issues_found": review.issues_found,
        "high_issues": review.high_issues,
        "medium_issues": review.medium_issues,
        "low_issues": review.low_issues,
        "files_changed": [
            {
                "filename": f.filename,
                "status": f.status,
                "additions": f.additions,
                "deletions": f.deletions
            }
            for f in review.files_changed
        ],
        "agent_results": [
            {
                "agent_name": ar.agent_name,
                "status": ar.status,
                "execution_time_ms": ar.execution_time_ms,
                "output": {
                    "summary": ar.output.summary,
                    "issues": ar.output.code_quality_issues[:20]  # Limit to 20 issues
                }
            }
            for ar in review.agent_results
        ],
        "created_at": review.created_at.isoformat(),
        "completed_at": review.completed_at.isoformat() if review.completed_at else None
    }

@router.get("", response_model=List[ReviewResponse])
async def list_reviews(
    repository_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List reviews for the current user
    
    Endpoint: GET /reviews
    Auth: Required (JWT)
    Query params:
        - repository_id: Filter by repository
        - limit: Number of results (default 10, max 100)
        - skip: Number of results to skip (pagination)
    """
    # Build query
    query = Review.find(Review.user_id.ref.id == current_user.id)
    
    # Filter by repository if provided
    if repository_id:
        try:
            repo = await Repository.get(PydanticObjectId(repository_id))
            query = query.find(Review.repo_id.ref.id == repo.id)
        except Exception:
            raise HTTPException(status_code=404, detail="Repository not found")
    
    # Execute query with pagination
    reviews = await query.sort(-Review.created_at).skip(skip).limit(limit).to_list()
    
    return [
        ReviewResponse(
            id=str(r.id),
            pr_number=r.pr_number,
            pr_title=r.pr_title,
            pr_url=r.pr_url,
            overall_status=r.overall_status,
            issues_found=r.issues_found,
            high_issues=r.high_issues,
            medium_issues=r.medium_issues,
            low_issues=r.low_issues,
            created_at=r.created_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None
        )
        for r in reviews
    ]

@router.get("/repository/{repo_id}", response_model=List[ReviewResponse])
async def get_repository_reviews(
    repo_id: str,
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get all reviews for a specific repository
    
    Endpoint: GET /reviews/repository/{repo_id}
    Auth: Required (JWT)
    """
    # Get repository
    try:
        repo = await Repository.get(PydanticObjectId(repo_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Verify user owns the repository
    if str(repo.user.ref.id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get reviews
    reviews = await Review.find(
        Review.repo_id.ref.id == repo.id
    ).sort(-Review.created_at).limit(limit).to_list()
    
    return [
        ReviewResponse(
            id=str(r.id),
            pr_number=r.pr_number,
            pr_title=r.pr_title,
            pr_url=r.pr_url,
            overall_status=r.overall_status,
            issues_found=r.issues_found,
            high_issues=r.high_issues,
            medium_issues=r.medium_issues,
            low_issues=r.low_issues,
            created_at=r.created_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None
        )
        for r in reviews
    ]
