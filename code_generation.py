# code_generation.py
import os
import requests
from datetime import datetime
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()  # Load SONNET_API_KEY from .env


class SOTACodeGenerator:
    def __init__(self, api_key: str = None):
        """Initialize the SOTA code generation model (Claude 3.5 Sonnet via OpenRouter)"""
        self.api_key = api_key or os.getenv("SONNET_API_KEY")
        if not self.api_key:
            raise ValueError("❌ SONNET_API_KEY not found. Please set it in your .env or pass explicitly.")

        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_name = "anthropic/claude-3.5-sonnet"

        print(f"✅ Initialized SOTA Code Generation Model: {self.model_name}")
        print(f"📊 Benchmarks: 92% HumanEval, 70.3% SWE-bench")

    def generate_code(self, 
                      problem_description: str, 
                      language: str = "python",
                      include_tests: bool = True,
                      explain_approach: bool = True) -> Dict[str, Any]:
        """Generate code using Claude 3.5 Sonnet via OpenRouter"""

        prompt = self._build_academic_prompt(problem_description, language, include_tests, explain_approach)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a world-class software engineer. Provide production-quality code with clear explanations."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 4000
        }

        try:
            response = requests.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            generated_content = data["choices"][0]["message"]["content"]

            result = self._parse_generated_response(generated_content)
            result.update({
                "model_used": self.model_name,
                "timestamp": datetime.now().isoformat(),
                "problem_description": problem_description,
                "language": language
            })
            return result

        except Exception as e:
            return {
                "error": f"Code generation failed: {str(e)}",
                "model_used": self.model_name,
                "timestamp": datetime.now().isoformat()
            }

    def _build_academic_prompt(self, problem: str, language: str, 
                              include_tests: bool, explain_approach: bool) -> str:
        """Build a structured academic-quality prompt"""
        prompt = f"""
**ACADEMIC CODE GENERATION TASK**

**Problem Statement:**
{problem}

**Requirements:**
- Programming Language: {language}
- Provide clean, production-quality code
- Follow best practices and coding standards
"""
        if explain_approach:
            prompt += """
- Include algorithm explanation and complexity analysis
- Explain design decisions"""
        if include_tests:
            prompt += """
- Include comprehensive unit tests
- Test edge cases and error conditions"""
        
        prompt += f"""

**Output Format:**
Please structure your response as follows:

## Algorithm Approach
[Explain your approach and reasoning]

## Time & Space Complexity
[Analyze computational complexity]

## Implementation
```{language}
[Your main implementation here]
```

## Unit Tests
```{language}
[Your unit tests here]
```

## Edge Cases Considered
[List important edge cases you handled]
"""
        return prompt

    def _parse_generated_response(self, content: str) -> Dict[str, Any]:
        """Parse structured response from the model"""
        result = {
            "full_response": content,
            "approach_explanation": "",
            "complexity_analysis": "",
            "main_code": "",
            "test_code": "",
            "edge_cases": ""
        }
        
        sections = content.split("##")
        for section in sections:
            section = section.strip()
            if section.startswith("Algorithm Approach"):
                result["approach_explanation"] = section.replace("Algorithm Approach", "").strip()
            elif section.startswith("Time & Space Complexity"):
                result["complexity_analysis"] = section.replace("Time & Space Complexity", "").strip()
            elif "```" in section and "Implementation" in section:
                code_blocks = section.split("```")
                if len(code_blocks) >= 2:
                    result["main_code"] = code_blocks[1].strip()
            elif "```" in section and "Unit Tests" in section:
                code_blocks = section.split("```")
                if len(code_blocks) >= 2:
                    result["test_code"] = code_blocks[1].strip()
            elif section.startswith("Edge Cases"):
                result["edge_cases"] = section.replace("Edge Cases Considered", "").strip()
        
        return result

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save generation results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sota_code_generation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filename}")
        return filename


# Example usage functions
def example_basic_usage():
    """Basic example of using the SOTA code generator"""
    
    # Initialize the generator
    generator = SOTACodeGenerator()
    
    # Example problem
    problem = """
    Implement a function that finds the longest palindromic substring in a given string.
    The function should be efficient and handle edge cases like empty strings and single characters.
    """
    
    # Generate solution
    print("🚀 Generating solution with SOTA model...")
    result = generator.generate_code(
        problem_description=problem,
        language="python",
        include_tests=True,
        explain_approach=True
    )
    
    # Display results
    if "error" not in result:
        print("\n" + "="*50)
        print("📊 SOTA CODE GENERATION RESULTS")
        print("="*50)
        print(f"Model: {result['model_used']}")
        print(f"Generated at: {result['timestamp']}")
        print("\n" + result['full_response'])
        
        # Save results
        filename = generator.save_results(result)
        print(f"\n✅ Complete results saved to: {filename}")
    else:
        print(f"❌ Error: {result['error']}")


def test_api_connection():
    """Test if the API connection works"""
    try:
        generator = SOTACodeGenerator()
        
        # Simple test problem
        test_problem = "Write a function to add two numbers and return the result."
        
        print("🧪 Testing API connection...")
        result = generator.generate_code(
            problem_description=test_problem,
            language="python",
            include_tests=False,
            explain_approach=False
        )
        
        if "error" not in result:
            print("✅ API connection successful!")
            print("📝 Sample response:")
            print(result['full_response'][:200] + "...")
            return True
        else:
            print(f"❌ API test failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("🎓 SOTA Code Generation Model - Claude 3.5 Sonnet")
    print("=" * 60)
    
    # First test the connection
    if test_api_connection():
        print("\n📋 Choose an option:")
        print("1. Run basic example (palindrome problem)")
        print("2. Enter custom problem")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            example_basic_usage()
        elif choice == "2":
            generator = SOTACodeGenerator()
            custom_problem = input("\n📝 Enter your coding problem: ")
            language = input("🔧 Programming language (default: python): ").strip() or "python"
            
            print(f"\n🚀 Generating solution for your problem...")
            result = generator.generate_code(
                problem_description=custom_problem,
                language=language,
                include_tests=True,
                explain_approach=True
            )
            
            if "error" not in result:
                print("\n" + "="*50)
                print("📊 GENERATED SOLUTION")
                print("="*50)
                print(result['full_response'])
                
                # Save results
                filename = generator.save_results(result)
                print(f"\n✅ Results saved to: {filename}")
            else:
                print(f"❌ Error: {result['error']}")
                
        elif choice == "3":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
    else:
        print("\n🔧 Please check your API key and try again.")
        print("💡 Make sure SONNET_API_KEY is set in your .env file")