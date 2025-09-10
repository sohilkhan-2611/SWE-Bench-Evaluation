import os
import time
import json
from groq import Groq
from typing import Dict, Any, List
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class GroqSWEAgent:
    def __init__(self, api_key: str = None):
        self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"  # Groq model for coding
        self.max_tokens = 4000
        self.temperature = 0.1
        
        # Rate limiting (to avoid hitting API limits)
        self.requests_per_minute = 25  
        self.last_request_time = 0
        self.request_interval = 60 / self.requests_per_minute  
        
        # Logging setup
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            self.logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def generate_patch(self, problem_statement: str, repo_context: str, file_content: str = "", instance_id: str = "") -> Dict[str, Any]:
        """Generate a patch for the given problem"""
        self._rate_limit()
        
        prompt = f"""You are an expert software engineer working on fixing a GitHub issue.

PROBLEM STATEMENT:
{problem_statement}

REPOSITORY CONTEXT:
{repo_context}

CURRENT FILE CONTENT (if available):
{file_content}

TASK:
Analyze the issue and provide a complete fix. Your response should include:
1. Analysis of the root cause
2. The exact patch/fix needed
3. Brief explanation of your solution

Focus on:
- Minimal changes that fix the issue
- Preserving existing functionality
- Following the existing code style

Provide your fix in a clear, implementable format.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert software engineer specializing in debugging and patch generation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            patch_content = response.choices[0].message.content
            result = {
                "instance_id": instance_id,
                "model": self.model,
                "patch": patch_content,
                "success": True,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0,
                "error": None
            }
            self.logger.info(f"Generated patch for {instance_id} - Tokens used: {result['tokens_used']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating patch for {instance_id}: {str(e)}")
            return {
                "instance_id": instance_id,
                "model": self.model,
                "patch": None,
                "success": False,
                "tokens_used": 0,
                "error": str(e)
            }

if __name__ == "__main__":
    # Initialize agent
    agent = GroqSWEAgent()
    
    # The buggy problem
    test_problem = """
    The function calculate_sum has a bug where it returns None instead of 0 for empty lists.
    Fix this issue.
    """
    
    test_context = """
    def calculate_sum(numbers):
        if not numbers:
            return None  # BUG: should return 0
        return sum(numbers)
    """
    
    # Run Groq to generate the patch
    result = agent.generate_patch(
        problem_statement=test_problem,
        repo_context=test_context,
        instance_id="calculate_sum_bug"
    )
    
    # Print model’s fix
    print("\n=== Test Result ===")
    print(json.dumps(result, indent=2))