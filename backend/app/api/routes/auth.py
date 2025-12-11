from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
from github import Github, GithubException
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.api import deps
from datetime import timedelta

router = APIRouter()

@router.get("/login")
def login():
    """
    Redirects the user to the GitHub OAuth login page.
    """
    scope = "read:user user:email repo"
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri={settings.GITHUB_CALLBACK_URL}&scope={scope}"
    )

@router.get("/callback/github")
async def callback(code: str, state: str = None):
    """
    Handles the callback from GitHub.
    Exchanges the code for an access token, fetches user info, creates/updates the user,
    and returns a JWT token (via redirect to frontend).
    """
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        headers = {"Accept": "application/json"}
        data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_CALLBACK_URL,
        }
        response = await client.post("https://github.com/login/oauth/access_token", json=data, headers=headers)
        
        if response.status_code != 200:
             raise HTTPException(status_code=400, detail="Failed to retrieve access token from GitHub")
        
        token_data = response.json()
        error = token_data.get("error")
        if error:
             raise HTTPException(status_code=400, detail=f"GitHub Error: {token_data.get('error_description')}")
        
        access_token = token_data["access_token"]
        
        # Fetch user info using PyGithub
        try:
            g = Github(access_token)
            github_user = g.get_user()
            
            # Get primary email
            email = None
            if github_user.email:
                email = github_user.email
            else:
                # Iterate to find primary email if not public
                for e in github_user.get_emails():
                    if e["primary"]:
                        email = e["email"]
                        break
            
            # Check if user exists
            user = await User.find_one(User.github_user_id == github_user.id)
            if not user:
                # Create new user
                user = User(
                    github_user_id=github_user.id,
                    github_username=github_user.login,
                    email=email,
                    github_access_token=access_token,
                    avatar_url=github_user.avatar_url,
                    name=github_user.name
                )
                await user.insert()
            else:
                # Update existing user
                user.github_access_token = access_token
                user.github_username = github_user.login
                user.avatar_url = github_user.avatar_url
                user.name = github_user.name
                user.email = email
                await user.save()
            
            # Create JWT
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            jwt_token = create_access_token(
                subject=str(user.id), expires_delta=access_token_expires
            )
            
            # Redirect to frontend with token
            return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}")
            
        except GithubException as e:
            raise HTTPException(status_code=400, detail=f"GitHub API Error: {e}")

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(deps.get_current_user)):
    """
    Get current user.
    """
    return current_user
