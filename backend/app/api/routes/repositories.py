from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.api import deps
from app.models.user import User
from app.models.repository import Repository
from app.services.github_service import GitHubService

router = APIRouter()

@router.get("/", response_model=List[Repository])
async def list_repositories(
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all repositories for the current user.
    """
    repos = await Repository.find(Repository.user.ref.id == current_user.id).to_list()
    return repos

@router.post("/sync")
async def sync_repositories(
    current_user: User = Depends(deps.get_current_user)
):
    """
    Sync repositories from GitHub.
    """
    try:
        service = GitHubService(current_user.github_access_token)
        github_repos = service.fetch_user_repositories()
        
        synced_count = 0
        for repo_data in github_repos:
            # Check if exists
            repo = await Repository.find_one(Repository.repo_github_id == repo_data["repo_github_id"])
            
            # Map fields that might differ or just pass kwargs if exact match
            # Repository model has 'user' field which needs to be the User object (or Link)
            
            if not repo:
                repo = Repository(
                    user=current_user,
                    repo_github_id=repo_data["repo_github_id"],
                    repo_full_name=repo_data["repo_full_name"],
                    repo_name=repo_data["repo_name"],
                    repo_owner=repo_data["repo_owner"],
                    default_branch=repo_data["default_branch"],
                    language_primary=repo_data["language_primary"],
                    # Add other fields if needed or ignore extra from repo_data
                )
                await repo.insert()
                synced_count += 1
            else:
                # Update details if needed
                repo.default_branch = repo_data["default_branch"]
                repo.language_primary = repo_data["language_primary"]
                await repo.save()
                
        return {"message": f"Synced repositories. Added {synced_count} new."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync repositories: {str(e)}")

@router.get("/{repo_id}", response_model=Repository)
async def get_repository(
    repo_id: str,
    current_user: User = Depends(deps.get_current_user)
):
    repo = await Repository.get(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if str(repo.user.ref.id) != str(current_user.id):
         raise HTTPException(status_code=403, detail="Not authorized")
    return repo
