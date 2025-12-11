import google.generativeai as genai
from app.core.config import settings
from typing import Optional

class LLMService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use a widely available stable model to avoid availability issues
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def generate_content(self, prompt: str) -> str:
        try:
            # Use synchronous call for broader SDK compatibility
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating content from Gemini: {e}")
            return ""

    async def analyze_pr(self, pr_diff: str, pr_title: str, pr_description: str) -> str:
        prompt = f"""
        You are an expert code reviewer. Analyze the following Pull Request.
        
        Title: {pr_title}
        Description: {pr_description}
        
        Diff:
        {pr_diff[:30000]}  # Truncate to avoid token limits if necessary
        
        Provide a detailed review in JSON format with the following structure:
        {{
            "summary": "Brief summary of changes",
            "new_features": ["List of new features"],
            "security_enhancements": ["List of security improvements"],
            "code_quality_issues": [
                {{"severity": "high/medium/low", "file": "filename", "line": line_number, "message": "Issue description"}}
            ],
            "recommendations": ["List of recommendations"],
            "walkthrough": "Detailed walkthrough of changes",
            "vulnerabilities": [
                 {{"severity": "critical/high", "type": "type", "file": "filename", "line": line_number, "description": "desc"}}
            ],
            "passed_checks": ["List of checks passed"]
        }}
        
        Ensure the output is valid JSON. Do not include markdown formatting like ```json.
        """
        return await self.generate_content(prompt)
