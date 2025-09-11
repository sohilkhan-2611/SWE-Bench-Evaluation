from datasets import load_dataset
import json
from groq import Groq
import os
import random
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def test_specific_problem():
    """Test Groq on the specific problem statement about partitions()"""
    
    # Define the specific problem statement and expected patch
    problem_statement = """partitions() reusing the output dictionaries\nThe partitions() iterator in sympy.utilities.iterables reuses the output dictionaries. There is a caveat about it in the docstring. 

I'm wondering if it's really that important for it to do this. It shouldn't be that much of a performance loss to copy the dictionary before yielding it. This behavior is very confusing. It means that something as simple as list(partitions()) will give an apparently wrong result. And it can lead to much more subtle bugs if the partitions are used in a nontrivial way."""

    expected_patch = """diff --git a/sympy/utilities/iterables.py b/sympy/utilities/iterables.py
--- a/sympy/utilities/iterables.py
+++ b/sympy/utilities/iterables.py
@@ -1738,21 +1738,6 @@ def partitions(n, m=None, k=None, size=False):
     {2: 1, 4: 1}
     {3: 2}
 
-    Note that the _same_ dictionary object is returned each time.
-    This is for speed:  generating each partition goes quickly,
-    taking constant time, independent of n.
-
-    >>> [p for p in partitions(6, k=2)]
-    [{1: 6}, {1: 6}, {1: 6}, {1: 6}]
-
-    If you want to build a list of the returned dictionaries then
-    make a copy of them:
-
-    >>> [p.copy() for p in partitions(6, k=2)]  # doctest: +SKIP
-    [{2: 3}, {1: 2, 2: 2}, {1: 4, 2: 1}, {1: 6}]
-    >>> [(M, p.copy()) for M, p in partitions(6, k=2, size=True)]  # doctest: +SKIP
-    [(3, {2: 3}), (4, {1: 2, 2: 2}), (5, {1: 4, 2: 1}), (6, {1: 6})]
-
     References
     ==========
 
@@ -1802,9 +1787,9 @@ def partitions(n, m=None, k=None, size=False):
         keys.append(r)
     room = m - q - bool(r)
     if size:
-        yield sum(ms.values()), ms
+        yield sum(ms.values()), ms.copy()
     else:
-        yield ms
+        yield ms.copy()
 
     while keys != [1]:
         # Reuse any 1's.
@@ -1842,9 +1827,9 @@ def partitions(n, m=None, k=None, size=False):
             break
         room -= need
         if size:
-            yield sum(ms.values()), ms
+            yield sum(ms.values()), ms.copy()
         else:
-            yield ms
+            yield ms.copy()
 
 
 def ordered_partitions(n, m=None, sort=True):"""

    # Create a mock instance with the specific problem
    instance = {
        'instance_id': 'sympy_sympy__partitions_fix',
        'repo': 'sympy/sympy',
        'problem_statement': problem_statement,
        'patch': expected_patch
    }

    # Display the problem info
    print("="*80)
    print("SPECIFIC PROBLEM ANALYSIS")
    print(f"Instance ID: {instance.get('instance_id', 'N/A')}")
    print(f"Repository: {instance.get('repo', 'N/A')}")
    print(f"Problem Statement:\n{instance.get('problem_statement', 'N/A')}")
    print(f"Expected Patch:\n{instance.get('patch', 'N/A')}")
    
    return instance

def test_groq_on_instance(instance, api_key=None, save_individual=False):
    """Test Groq on the PROVIDED instance"""
    
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY not found. Set it as environment variable.")
            return None
    
    # Initialize Groq client
    client = Groq(api_key=api_key)
    
    # Create prompt
    prompt = f"""You are an expert software engineer. Fix the following GitHub issue:

REPOSITORY: {instance['repo']}
ISSUE: {instance['problem_statement']}

Analyze the problem and provide a complete patch that fixes the issue.
Focus on:
1. Understanding what's broken
2. Implementing a minimal fix
3. Ensuring existing functionality isn't broken

Provide your solution as a unified diff patch or clear code changes."""

    print("="*80)
    print("TESTING GROQ ON SPECIFIC INSTANCE")
    print(f"Testing on Instance ID: {instance.get('instance_id', 'N/A')}")
    print("="*80)
    
    try:
        # Make API call
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert software engineer specializing in debugging and patch generation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.1
        )

        generated_patch = (
            response.choices[0].message.content
            if hasattr(response.choices[0], "message")
            else response.choices[0].text
        )

        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else "Unknown"
        
        print(f"GROQ GENERATED SOLUTION:")
        print("-" * 50)
        print(generated_patch[:300] + "..." if len(generated_patch) > 300 else generated_patch)
        
        print(f"\nAPI USAGE:")
        print(f"Tokens used: {tokens_used}")
        
        # Create result object
        result = {
            "instance_id": instance['instance_id'],
            "repository": instance['repo'],
            "problem_statement": instance['problem_statement'],
            "expected_patch": instance['patch'],
            "groq_generated_patch": generated_patch,
            "tokens_used": tokens_used,
            "model": "llama-3.3-70b-versatile",
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
        # Only save individual file if requested
        if save_individual:
            filename = f"swebench_result_{instance['instance_id'].replace('/', '_')}.json"
            with open(filename, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nIndividual result saved to: {filename}")

        return result
        
    except Exception as e:
        print(f"Error calling Groq API: {str(e)}")
        return None

def compare_patches(expected, generated):
    """Simple comparison of patches"""
    
    print("="*80)
    print("PATCH COMPARISON ANALYSIS")
    print("="*80)
    
    print(f"Expected patch length: {len(expected)} characters")
    print(f"Generated patch length: {len(generated)} characters")
    
    # Simple similarity check
    expected_lines = set(expected.lower().split('\n'))
    generated_lines = set(generated.lower().split('\n'))
    
    common_lines = expected_lines.intersection(generated_lines)
    
    if len(expected_lines) == 0 and len(generated_lines) == 0:
        similarity = 100.0
    elif max(len(expected_lines), len(generated_lines)) == 0:
        similarity = 0.0
    else:
        similarity = len(common_lines) / max(len(expected_lines), len(generated_lines)) * 100
    
    print(f"Line-level similarity: {similarity:.1f}%")
    
    if similarity > 80:
        print(" High similarity - likely successful fix")
        return "SUCCESS", similarity
    elif similarity > 50:
        print(" Medium similarity - partial fix")
        return "PARTIAL", similarity
    else:
        print(" Low similarity - likely failed fix")
        return "FAILED", similarity

def run_specific_evaluation():
    """Run evaluation on the specific partitions problem"""
    
    print("="*80)
    print("RUNNING SPECIFIC SWE-BENCH EVALUATION")
    print("Testing on: sympy partitions() dictionary reuse issue")
    print("="*80)
    
    # Get the specific problem instance
    instance = test_specific_problem()
    
    if os.getenv("GROQ_API_KEY"):
        # Test with Groq
        result = test_groq_on_instance(instance, save_individual=True)
        
        if result:
            # Compare patches
            comparison_result, similarity_score = compare_patches(
                result['expected_patch'], 
                result['groq_generated_patch']
            )
            
            # Add comparison results to the result
            result['comparison_result'] = comparison_result
            result['similarity_score'] = similarity_score
            
            # Save final result with comparison
            filename = f"specific_swebench_result_{instance['instance_id'].replace('/', '_')}.json"
            with open(filename, "w") as f:
                json.dump(result, f, indent=2)
            
            print(f"\nFinal result saved to: {filename}")
            
            return result
    else:
        print(" GROQ_API_KEY not found - cannot run API test")
        print(" Set GROQ_API_KEY environment variable to run evaluation")
        print(" Example: export GROQ_API_KEY='your_api_key_here'")
        return None

if __name__ == "__main__":
    # Run specific evaluation on the partitions problem
    result = run_specific_evaluation()