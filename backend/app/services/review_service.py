"""
Review Service - Orchestrates the PR review process
"""
from typing import Dict, Any
from datetime import datetime
from app.models.user import User
from app.models.repository import Repository
from app.models.review import Review, FileChange, AgentResult, AgentOutput
from app.services.github_service import GitHubService
from app.agents.pr_analyzer_agent import PRAnalyzerAgent

class ReviewService:
    """Service to orchestrate PR reviews"""
    
    async def trigger_review(
        self,
        repo: Repository,
        pr_number: int,
        user: User,
        post_to_github: bool = True
    ) -> Review:
        """
        Trigger a complete PR review
        
        Args:
            repo: Repository model
            pr_number: PR number
            user: User model
            post_to_github: Whether to post results to GitHub
            
        Returns:
            Review model with results
        """
        # Initialize GitHub service
        github_service = GitHubService(user.github_access_token)
        
        # Fetch PR details
        pr_details = github_service.get_pr_details(repo.repo_full_name, pr_number)
        pr_files = github_service.get_pr_files(repo.repo_full_name, pr_number)
        
        # Run agent analysis
        agent = PRAnalyzerAgent()
        start_time = datetime.utcnow()
        
        analysis_result = await agent.analyze(
            pr_files=pr_files,
            pr_details={
                "pr_number": pr_details["number"],
                "pr_title": pr_details["title"],
                "pr_description": pr_details["body"] or "",
                "pr_author": pr_details["user"],
                "pr_branch": pr_details["head"]["ref"],
                "pr_base_branch": pr_details["base"]["ref"],
                "commit_sha": pr_details["head"]["sha"],
                "commit_message": pr_details["title"]
            }
        )
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        # Parse analysis results
        analysis_results = analysis_result.get('analysis_results', [])
        all_issues = []
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        
        for file_result in analysis_results:
            for issue in file_result.get('issues', []):
                all_issues.append({
                    "file": file_result['filename'],
                    "line": issue.get('line'),
                    "severity": issue['severity'],
                    "category": issue['category'],
                    "message": issue['description']
                })
                severity = issue.get('severity', 'low')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Create agent output
        agent_output = AgentOutput(
            summary=analysis_result.get('final_review', '')[:500],
            code_quality_issues=all_issues,
            vulnerabilities=[i for i in all_issues if i['category'] == 'security'],
            recommendations=["Review all identified issues before merging"],
            passed_checks=[]
        )
        
        # Create agent result
        agent_result = AgentResult(
            agent_name="pr_analyzer",
            agent_version="1.0.0",
            status="completed",
            started_at=start_time,
            completed_at=end_time,
            execution_time_ms=execution_time,
            output=agent_output,
            posted_to_github=False
        )
        
        # Create file changes
        file_changes = [
            FileChange(
                filename=f['filename'],
                status=f['status'],
                additions=f['additions'],
                deletions=f['deletions'],
                changes=f['changes'],
                patch_preview=f.get('patch', '')[:200] if f.get('patch') else None
            )
            for f in pr_files
        ]
        
        # Create review document
        review = Review(
            repo_id=repo,
            user_id=user,
            pr_number=pr_details["number"],
            pr_title=pr_details["title"],
            pr_description=pr_details["body"] or "",
            pr_url=pr_details["html_url"],
            pr_author=pr_details["user"],
            pr_branch=pr_details["head"]["ref"],
            pr_base_branch=pr_details["base"]["ref"],
            commit_sha=pr_details["head"]["sha"],
            commit_message=pr_details["title"],
            files_changed=file_changes,
            total_additions=sum(f['additions'] for f in pr_files),
            total_deletions=sum(f['deletions'] for f in pr_files),
            total_files_changed=len(pr_files),
            agent_results=[agent_result],
            overall_status="completed",
            issues_found=len(all_issues),
            critical_issues=len([i for i in all_issues if i['severity'] == 'high' and i['category'] == 'security']),
            high_issues=severity_counts.get('high', 0),
            medium_issues=severity_counts.get('medium', 0),
            low_issues=severity_counts.get('low', 0),
            processing_time_total_ms=execution_time,
            completed_at=end_time
        )
        
        # Save review
        await review.insert()
        
        # Post to GitHub if requested
        if post_to_github:
            await self.post_review_to_github(review, github_service)
        
        return review
    
    async def post_review_to_github(self, review: Review, github_service: GitHubService) -> None:
        """
        Post review results to GitHub as a comment
        
        Args:
            review: Review model
            github_service: GitHub service instance
        """
        # Format review comment
        comment_body = self._format_review_comment(review)
        
        # Post comment
        try:
            result = github_service.post_comment(
                repo_full_name=review.repo_id.repo_full_name,
                pr_number=review.pr_number,
                body=comment_body
            )
            
            # Update review with GitHub comment info
            if review.agent_results:
                review.agent_results[0].posted_to_github = True
                review.agent_results[0].github_comment_id = result
                await review.save()
                
        except Exception as e:
            print(f"Failed to post review to GitHub: {e}")
    
    def _format_review_comment(self, review: Review) -> str:
        """Format review as GitHub markdown comment"""
        
        # Get agent output
        agent_output = review.agent_results[0].output if review.agent_results else None
        
        comment = f"""## 🤖 RevyCode AI Review

**PR:** #{review.pr_number} - {review.pr_title}

### 📊 Summary
{agent_output.summary if agent_output else 'No summary available'}

### 🔍 Issues Found: {review.issues_found}

"""
        
        if review.issues_found > 0:
            comment += f"""
**By Severity:**
- 🔴 High: {review.high_issues}
- 🟠 Medium: {review.medium_issues}
- 🟡 Low: {review.low_issues}
"""
            
            if agent_output and agent_output.code_quality_issues:
                comment += "\n### 📝 Detailed Issues\n\n"
                
                # Group by file
                issues_by_file = {}
                for issue in agent_output.code_quality_issues[:10]:  # Limit to 10 issues
                    file = issue.get('file', 'Unknown')
                    if file not in issues_by_file:
                        issues_by_file[file] = []
                    issues_by_file[file].append(issue)
                
                for file, issues in issues_by_file.items():
                    comment += f"\n**{file}**\n"
                    for issue in issues:
                        severity_emoji = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(issue.get('severity', 'low'), "⚪")
                        comment += f"- {severity_emoji} Line {issue.get('line', 'N/A')}: {issue.get('message', 'No description')}\n"
        else:
            comment += "\n✅ No major issues found!\n"
        
        comment += f"\n\n---\n*Analyzed in {review.processing_time_total_ms/1000:.2f}s by RevyCode AI*"
        
        return comment
