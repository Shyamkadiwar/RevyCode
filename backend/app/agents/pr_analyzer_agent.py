import google.generativeai as genai
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from app.core.config import settings

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

class AgentState(TypedDict):
    pr_files: List[Dict[str, Any]]
    pr_details: Dict[str, Any]
    analysis_results: List[Dict[str, Any]]
    final_review: str

class PRAnalyzerAgent:
    def __init__(self):
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("analyze_files", self.analyze_files)
        workflow.add_node("summarize_review", self.summarize_review)

        workflow.set_entry_point("analyze_files")
        workflow.add_edge("analyze_files", "summarize_review")
        workflow.add_edge("summarize_review", END)

        return workflow.compile()

    async def analyze_files(self, state: AgentState):
        files = state.get("pr_files", [])
        results = []
        
        for file in files:
            # Skip deleted files or images
            if file.get("status") == "removed" or not file.get("patch"):
                continue
                
            prompt = f"""
            You are an expert code reviewer. Analyze the following code change for bugs, security issues, and code quality improvements.
            
            File: {file.get('filename')}
            Patch:
            {file.get('patch')}
            
            Provide the review in JSON format with list of issues:
            {{
                "issues": [
                    {{
                        "line": <line_number>,
                        "severity": "low|medium|high",
                        "category": "bug|security|style|performance",
                        "description": "<description>",
                        "suggestion": "<suggestion>"
                    }}
                ]
            }}
            If no issues, return empty list.
            """
            
            try:
                # Synchronous call to Gemini (since the library is sync mostly, unless async version used)
                # Ideally this should be run in executor if blocking
                response = model.generate_content(prompt)
                # Simple parsing (robust parsing would be better)
                import json
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:-3]
                try:
                    data = json.loads(text)
                    if data.get("issues"):
                        results.append({
                            "filename": file.get("filename"),
                            "issues": data.get("issues")
                        })
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON for {file.get('filename')}")
                    
            except Exception as e:
                print(f"Error analyzing {file.get('filename')}: {e}")
                
        return {"analysis_results": results}

    async def summarize_review(self, state: AgentState):
        results = state.get("analysis_results", [])
        if not results:
            return {"final_review": "No major issues found in the analyzed files."}
            
        # Create a summary
        summary_prompt = f"""
        Summarize the following code review results into a cohesive Pull Request review comment.
        Highlight critical issues.
        
        Results:
        {results}
        """
        try:
            response = model.generate_content(summary_prompt)
            return {"final_review": response.text}
        except Exception as e:
            return {"final_review": f"Error generating summary: {e}"}

    async def analyze(self, pr_files: List[Dict[str, Any]], pr_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point to run the agent.
        """
        initial_state = {
            "pr_files": pr_files,
            "pr_details": pr_details,
            "analysis_results": [],
            "final_review": ""
        }
        result = await self.workflow.ainvoke(initial_state)
        return result
