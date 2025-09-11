from datasets import load_dataset
import json
from groq import Groq
import os
import random
from datetime import datetime
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

def run_comprehensive_evaluation(num_tests=10):
    """Run comprehensive evaluation and create consolidated JSON output"""
    
    print("="*80)
    print(f"RUNNING COMPREHENSIVE SWE-BENCH EVALUATION")
    print(f"Number of instances: {num_tests}")
    print("="*80)
    
    results = []
    success_cases = []
    failed_cases = []
    partial_cases = []
    total_tokens = 0
    
    for i in range(num_tests):
        print(f"\n--- EVALUATION {i+1}/{num_tests} ---")
        
        # Get a random instance
        instance = analyze_instance()
        
        if os.getenv("GROQ_API_KEY"):
            # Test with Groq (don't save individual files)
            result = test_groq_on_instance(instance, save_individual=False)
            
            if result:
                # Compare patches
                comparison_result, similarity_score = compare_patches(
                    result['expected_patch'], 
                    result['groq_generated_patch']
                )
                
                # Add comparison results to the result
                result['comparison_result'] = comparison_result
                result['similarity_score'] = similarity_score
                
                results.append(result)
                total_tokens += result['tokens_used'] if isinstance(result['tokens_used'], int) else 0
                
                # Categorize results
                if comparison_result == "SUCCESS":
                    success_cases.append(result)
                    print(f" SUCCESS: {result['instance_id']}")
                elif comparison_result == "PARTIAL":
                    partial_cases.append(result)
                    print(f" PARTIAL: {result['instance_id']}")
                else:
                    failed_cases.append(result)
                    print(f" FAILED: {result['instance_id']}")
        else:
            print(" GROQ_API_KEY not found - skipping API test")
            break
    
    # Create comprehensive summary
    evaluation_summary = {
        "metadata": {
            "model_name": "llama-3.3-70b-versatile",
            "provider": "groq",
            "evaluation_date": datetime.now().isoformat(),
            "dataset": "princeton-nlp/SWE-bench_Lite",
            "total_instances_tested": len(results),
            "evaluation_parameters": {
                "max_tokens": 2000,
                "temperature": 0.1,
                "max_patch_length_filter": 200,
                "max_problem_length_filter": 500
            }
        },
        "performance_summary": {
            "total_tests": len(results),
            "successful_fixes": len(success_cases),
            "partial_fixes": len(partial_cases),
            "failed_fixes": len(failed_cases),
            "success_rate": len(success_cases) / len(results) if results else 0,
            "partial_rate": len(partial_cases) / len(results) if results else 0,
            "failure_rate": len(failed_cases) / len(results) if results else 0,
            "total_tokens_used": total_tokens,
            "average_tokens_per_instance": total_tokens / len(results) if results else 0,
            "average_similarity_score": sum(r['similarity_score'] for r in results) / len(results) if results else 0
        },
        "detailed_results": results,
        "example_cases": {
            "successful_examples": success_cases[:2],  # Best 2 successes
            "failed_examples": failed_cases[:2],       # First 2 failures
            "partial_examples": partial_cases[:1]      # 1 partial case
        }
    }
    
    # Save consolidated results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"swe_bench_groq_llama_evaluation_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(evaluation_summary, f, indent=2)
    
    print(f"\n" + "="*80)
    print("FINAL EVALUATION SUMMARY")
    print("="*80)
    print(f"Total instances tested: {len(results)}")
    print(f" Successful fixes: {len(success_cases)} ({len(success_cases)/len(results)*100:.1f}%)" if results else "No results")
    print(f" Partial fixes: {len(partial_cases)} ({len(partial_cases)/len(results)*100:.1f}%)" if results else "")
    print(f" Failed fixes: {len(failed_cases)} ({len(failed_cases)/len(results)*100:.1f}%)" if results else "")
    print(f" Total tokens used: {total_tokens:,}")
    print(f" Results saved to: {filename}")
    
    return evaluation_summary

if __name__ == "__main__":
    # Run comprehensive evaluation (creates only 1 JSON file)
    if os.getenv("GROQ_API_KEY"):
        evaluation_results = run_comprehensive_evaluation(num_tests=5)
    else:
        print("  Set GROQ_API_KEY environment variable to run evaluation")
        print("  Example: export GROQ_API_KEY='your_api_key_here'")