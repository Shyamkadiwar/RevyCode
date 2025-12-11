"""
GitHub Service - Handles all GitHub API interactions
"""
from typing import List, Dict, Any, Optional
from github import Github, GithubException
from app.core.config import settings

class GitHubService:
    """Service for interacting with GitHub API"""
    
    def __init__(self, access_token: str):
        """Initialize with user's GitHub access token"""
        self.github = Github(access_token)
        self.user = self.github.get_user()
    
    def get_pr_details(self, repo_full_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Get PR metadata
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: PR number
            
        Returns:
            Dict with PR details
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            return {
                "pr_number": pr.number,
                "pr_title": pr.title,
                "pr_description": pr.body or "",
                "pr_url": pr.html_url,
                "pr_author": pr.user.login,
                "pr_branch": pr.head.ref,
                "pr_base_branch": pr.base.ref,
                "commit_sha": pr.head.sha,
                "commit_message": pr.title,
                "state": pr.state,
                "created_at": pr.created_at,
                "updated_at": pr.updated_at
            }
        except GithubException as e:
            raise Exception(f"Failed to fetch PR details: {e}")
    
    def get_pr_files(self, repo_full_name: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Get all files changed in a PR
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: PR number
            
        Returns:
            List of file changes with patches
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            files = []
            for file in pr.get_files():
                files.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch if hasattr(file, 'patch') else None,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url
                })
            
            return files
        except GithubException as e:
            raise Exception(f"Failed to fetch PR files: {e}")
    
    def post_review_comment(
        self, 
        repo_full_name: str, 
        pr_number: int, 
        comment_body: str
    ) -> Dict[str, Any]:
        """
        Post a review comment on a PR
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: PR number
            comment_body: Comment text (supports markdown)
            
        Returns:
            Dict with comment details
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            # Post as issue comment (appears at bottom of PR)
            comment = pr.as_issue().create_comment(comment_body)
            
            return {
                "comment_id": comment.id,
                "comment_url": comment.html_url,
                "created_at": comment.created_at
            }
        except GithubException as e:
            raise Exception(f"Failed to post comment: {e}")
    
    def post_inline_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        commit_sha: str,
        file_path: str,
        line_number: int,
        comment_body: str
    ) -> Dict[str, Any]:
        """
        Post an inline comment on a specific line
        
        Args:
            repo_full_name: Repository full name
            pr_number: PR number
            commit_sha: Commit SHA
            file_path: File path
            line_number: Line number
            comment_body: Comment text
            
        Returns:
            Dict with comment details
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            # Create review comment on specific line
            comment = pr.create_review_comment(
                body=comment_body,
                commit=repo.get_commit(commit_sha),
                path=file_path,
                line=line_number
            )
            
            return {
                "comment_id": comment.id,
                "comment_url": comment.html_url,
                "created_at": comment.created_at
            }
        except GithubException as e:
            raise Exception(f"Failed to post inline comment: {e}")
    
    def get_repository_info(self, repo_full_name: str) -> Dict[str, Any]:
        """
        Get repository information
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            
        Returns:
            Dict with repository details
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            
            return {
                "repo_id": repo.id,
                "repo_name": repo.name,
                "repo_full_name": repo.full_name,
                "repo_owner": repo.owner.login,
                "default_branch": repo.default_branch,
                "language": repo.language,
                "description": repo.description,
                "private": repo.private,
                "url": repo.html_url
            }
        except GithubException as e:
            raise Exception(f"Failed to fetch repository info: {e}")
