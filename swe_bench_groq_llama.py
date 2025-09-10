from datasets import load_dataset
import json
from groq import Groq
import os
import random
from dotenv import load_dotenv
load_dotenv()

def analyze_instance(max_fail=1, max_patch_len=200, max_problem_len=500):
    """Analyze a random easy Python instance from SWE-Bench_Lite test dataset"""
    # Load the test dataset
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    
    # Filter Python instances if 'language' exists
    if 'language' in dataset.features:
        python_instances = [inst for inst in dataset if inst['language'].lower() == 'python']
        if python_instances:
            filtered_instances = [
                inst for inst in python_instances
                if len(inst.get("FAIL_TO_PASS", [])) <= max_fail
                and len(inst.get("patch", "")) < max_patch_len
                and len(inst.get("problem_statement", "")) < max_problem_len
            ]
            if filtered_instances:
                instance = random.choice(filtered_instances)
            else:
                # Fallback if no easy instance found
                instance = random.choice(python_instances)
        else:
            print("No Python instances found, picking a random instance instead.")
            instance = random.choice(dataset)
    else:
        # If no language info, pick a random instance
        instance = random.choice(dataset)
    
    # Display basic info
    print("="*80)
    print("RANDOM INSTANCE ANALYSIS")
    print(f"Instance ID: {instance.get('instance_id', 'N/A')}")
    print(f"Repository: {instance.get('repo', 'N/A')}")
    print(f"Base Commit: {instance.get('base_commit', 'N/A')}")
    print(f"Problem Statement:\n{instance.get('problem_statement', 'N/A')}")
    print(f"Expected Patch:\n{instance.get('patch', 'N/A')}")
    
    if 'test_patch' in instance:
        print(f"Test Patch:\n{instance['test_patch']}")
    
    # Print other metadata
    for key, value in instance.items():
        if key not in ['problem_statement', 'patch', 'test_patch']:
            print(f"{key}: {value}")
    
    return instance

def test_groq_on_instance(instance, api_key=None):
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
    print("TESTING GROQ ON SELECTED INSTANCE")
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
        print(generated_patch)
        
        print(f"\nEXPECTED SOLUTION:")
        print("-" * 50)
        print(instance['patch'])
        
        print(f"\nAPI USAGE:")
        print(f"Tokens used: {tokens_used}")
        
        # Save results
        result = {
            "instance_id": instance['instance_id'],
            "repository": instance['repo'],
            "problem_statement": instance['problem_statement'],
            "expected_patch": instance['patch'],
            "groq_generated_patch": generated_patch,
            "tokens_used": tokens_used,
            "model": "llama-3.3-70b-versatile",
            "analysis_timestamp": str(os.times())
        }
        
        # Save with instance ID in filename for uniqueness
        filename = f"swebench_result_{instance['instance_id'].replace('/', '_')}.json"
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)

        print(f"\nResult saved to: {filename}")

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
        print("High similarity - likely successful fix")
        return "SUCCESS"
    elif similarity > 50:
        print("Medium similarity - partial fix")
        return "PARTIAL"
    else:
        print("Low similarity - likely failed fix")
        return "FAILED"

def run_multiple_tests(num_tests=5):
    """Run multiple tests to get both success and failure cases"""
    
    print("="*80)
    print(f"RUNNING {num_tests} TESTS TO FIND SUCCESS/FAILURE CASES")
    print("="*80)
    
    results = []
    success_cases = []
    failed_cases = []
    
    for i in range(num_tests):
        print(f"\n--- TEST {i+1}/{num_tests} ---")
        
        # Get a random instance
        instance = analyze_instance()
        
        if os.getenv("GROQ_API_KEY"):
            # Test with Groq
            result = test_groq_on_instance(instance)
            
            if result:
                # Compare patches
                comparison = compare_patches(result['expected_patch'], result['groq_generated_patch'])
                result['comparison_result'] = comparison
                results.append(result)
                
                if comparison == "SUCCESS":
                    success_cases.append(result)
                    print(f"SUCCESS CASE FOUND: {result['instance_id']}")
                elif comparison == "FAILED":
                    failed_cases.append(result)
                    print(f"FAILED CASE FOUND: {result['instance_id']}")
        else:
            print("GROQ_API_KEY not found - skipping API test")
    
    # Save summary
    summary = {
        "total_tests": len(results),
        "success_cases": len(success_cases),
        "failed_cases": len(failed_cases),
        "success_examples": success_cases[:2],  # First 2 successes
        "failed_examples": failed_cases[:2]     # First 2 failures
    }
    
    with open("swe_bench_groq_llama_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total tests run: {len(results)}")
    print(f"Success cases: {len(success_cases)}")
    print(f"Failed cases: {len(failed_cases)}")
    print(f"Summary saved to: swe_bench_groq_llama_results.json")

    return summary

if __name__ == "__main__":
    # FIXED: Now properly passes the selected instance to the test function
    
    # Step 1: Analyze a random instance
    selected_instance = analyze_instance()
    
    # Step 2: Test Groq on the SAME instance
    if os.getenv("GROQ_API_KEY"):
        result = test_groq_on_instance(selected_instance)  # Pass the selected instance!
        if result:
            comparison = compare_patches(result['expected_patch'], result['groq_generated_patch'])
            print(f"\nFinal Result: {comparison}")
    else:
        print("\n Set GROQ_API_KEY to run the API test")
    
    # Uncomment to run multiple tests:
    run_multiple_tests(5)