"""
Webhook Routes - Handle GitHub webhook events
"""
import hmac
import hashlib
from typing import Any, Dict
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.core.config import settings
from app.models.user import User
from app.models.repository import Repository
from app.services.review_service import ReviewService

router = APIRouter()

def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Verify GitHub webhook signature
    
    Args:
        payload_body: Raw request body
        signature_header: X-Hub-Signature-256 header value
        
    Returns:
        True if signature is valid
    """
    if not signature_header:
        return False
    
    # GitHub sends signature as 'sha256=<hash>'
    hash_algorithm, github_signature = signature_header.split('=')
    
    # Calculate expected signature
    secret = settings.GITHUB_WEBHOOK_SECRET.encode()
    expected_signature = hmac.new(secret, payload_body, hashlib.sha256).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, github_signature)

async def process_pr_event(payload: Dict[str, Any]):
    """
    Process PR webhook event in background
    
    Args:
        payload: GitHub webhook payload
    """
    try:
        action = payload.get('action')
        pr_data = payload.get('pull_request', {})
        repo_data = payload.get('repository', {})
        
        # Only process opened, synchronize, and reopened events
        if action not in ['opened', 'synchronize', 'reopened']:
            print(f"Ignoring PR action: {action}")
            return
        
        pr_number = pr_data.get('number')
        repo_full_name = repo_data.get('full_name')
        
        print(f"Processing PR #{pr_number} in {repo_full_name} (action: {action})")
        
        # Find repository in database
        repo = await Repository.find_one(Repository.repo_full_name == repo_full_name)
        if not repo:
            print(f"Repository {repo_full_name} not found in database")
            return
        
        # Get repository owner (user)
        user = await User.get(repo.user.ref.id)
        if not user:
            print(f"User not found for repository {repo_full_name}")
            return
        
        # Check if auto-review is enabled
        if not repo.settings.auto_review_on_pr:
            print(f"Auto-review disabled for {repo_full_name}")
            return
        
        # Trigger review
        review_service = ReviewService()
        review = await review_service.trigger_review(
            repo=repo,
            pr_number=pr_number,
            user=user,
            post_to_github=True
        )
        
        print(f"Review completed: {review.id}")
        
    except Exception as e:
        print(f"Error processing PR event: {e}")
        import traceback
        traceback.print_exc()

@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle GitHub webhook events
    
    Endpoint: POST /webhook/github
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not verify_github_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    payload = await request.json()
    
    # Get event type
    event_type = request.headers.get('X-GitHub-Event', '')
    
    # Handle different event types
    if event_type == 'ping':
        return {"message": "pong"}
    
    elif event_type == 'pull_request':
        # Process PR event in background
        background_tasks.add_task(process_pr_event, payload)
        return {"message": "PR event received"}
    
    else:
        return {"message": f"Event {event_type} received but not processed"}

@router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhook route is working"""
    return {"status": "Webhook endpoint is active"}
