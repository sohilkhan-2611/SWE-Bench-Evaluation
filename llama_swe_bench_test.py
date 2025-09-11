from datasets import load_dataset
import json
from groq import Groq
import os
import random
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()


def extract_filenames_from_patch(patch_text):
    """Extract filenames from a unified diff patch"""
    filenames = []
    for line in patch_text.splitlines():
        if line.startswith("--- a/"):
            path = line[6:]  # Remove "--- a/"
            if path and path not in filenames:
                filenames.append(path)
        elif line.startswith("+++ b/"):
            path = line[6:]  # Remove "+++ b/"
            if path and path not in filenames:
                filenames.append(path)
    return filenames


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
    
    # Extract target files from the expected patch
    target_files = extract_filenames_from_patch(instance.get('patch', ''))
    
    # Display basic info
    print("="*80)
    print("RANDOM INSTANCE ANALYSIS")
    print(f"Instance ID: {instance.get('instance_id', 'N/A')}")
    print(f"Repository: {instance.get('repo', 'N/A')}")
    print(f"Target Files: {target_files}")
    print(f"Problem Statement:\n{instance.get('problem_statement', 'N/A')}")
    print(f"Expected Patch:\n{instance.get('patch', 'N/A')}")
    
    return instance


def test_groq_on_instance(instance, api_key=None, save_individual=False):
    """Test Groq on the PROVIDED instance with enhanced prompt including target files"""
    
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY not found. Set it as environment variable.")
            return None
    
    # Initialize Groq client
    client = Groq(api_key=api_key)

    # Extract target files from expected patch
    target_files = extract_filenames_from_patch(instance.get('patch', ''))
    file_context = ""
    
    if target_files:
        file_context = f"""
## TARGET FILES TO MODIFY
The following files need to be modified based on the expected solution:
{chr(10).join(f"- {file}" for file in target_files)}

IMPORTANT: Your patch should ONLY modify these files. Do not create new files or modify other files.
"""
    
    # Enhanced prompt with target file context
    prompt = f"""You are an expert software engineer specializing in debugging and patch generation. Your task is to create a minimal, precise patch to fix a specific GitHub issue.

## REPOSITORY CONTEXT

Repository: {instance['repo']}
Instance ID: {instance.get('instance_id', 'N/A')}
{file_context}

## PROBLEM TO SOLVE
{instance['problem_statement']}


## FAILING TESTS (if available)
{', '.join(instance.get('FAIL_TO_PASS', [])) if instance.get('FAIL_TO_PASS') else 'No specific failing tests provided'}



## YOUR TASK
1. **Analyze** the problem statement to understand the root cause
2. **Focus** on the target files listed above 
3. **Generate** a minimal unified diff patch that fixes ONLY the reported issue
4. **Ensure** your patch addresses the core problem without breaking existing functionality

## CRITICAL REQUIREMENTS
- Output ONLY a valid unified diff patch (no explanations, no markdown code blocks)
- Start with "--- a/" and "+++ b/" format for each file
- Use proper file paths matching the target files above
- Make minimal changes - fix only what's broken
- Ensure the patch can be directly applied with `git apply`
- Do not include any explanatory text before or after the patch
- Modify only the relevant code; do not touch unrelated files or logic.
- Follow the existing project's style and conventions.
- Keep changes as small as possible while still being correct.
- Ensure that all tests pass with your patch.

## EXPECTED PATCH FORMAT
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -start_line,line_count +start_line,line_count @@
 context line
-line to remove
+line to add
 context line

 Now generate the patch:"""
    

    print("="*80)
    print("TESTING GROQ ON SELECTED INSTANCE")
    print(f"Testing on Instance ID: {instance.get('instance_id', 'N/A')}")
    print("="*80)
    
    try:
        # Make API call
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert software engineer with deep expertise in code analysis, debugging, and patch generation. You specialize in creating minimal, precise fixes for complex software issues."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.1  # Keep low for consistency
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
        
        # Create result object with target files info
        result = {
            "instance_id": instance['instance_id'],
            "repository": instance['repo'],
            "target_files": target_files,
            "problem_statement": instance['problem_statement'],
            "expected_patch": instance['patch'],
            "groq_generated_patch": generated_patch,
            "tokens_used": tokens_used,
            "model": "llama-3.3-70b-versatile",
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
        # Only save individual file if requested
        if save_individual:
            filename = f"groq_swebench_result_{instance['instance_id'].replace('/', '_')}.json"
            with open(filename, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nIndividual result saved to: {filename}")

        return result
        
    except Exception as e:
        print(f"Error calling Groq API: {str(e)}")
        return None


def validate_patch_format(generated_patch, expected_files):
    """Validate that the generated patch follows proper format and targets correct files"""
    
    validation_results = {
        "has_proper_format": False,
        "targets_correct_files": False,
        "generated_files": [],
        "issues": []
    }
    
    lines = generated_patch.strip().split('\n')
    
    # Check for proper diff format
    has_minus_line = any(line.startswith('--- a/') for line in lines)
    has_plus_line = any(line.startswith('+++ b/') for line in lines)
    has_hunk_header = any(line.startswith('@@') for line in lines)
    
    validation_results["has_proper_format"] = has_minus_line and has_plus_line and has_hunk_header
    
    if not validation_results["has_proper_format"]:
        validation_results["issues"].append("Missing proper unified diff format (---, +++, @@)")
    
    # Extract files from generated patch
    generated_files = extract_filenames_from_patch(generated_patch)
    validation_results["generated_files"] = generated_files
    
    # Check if generated patch targets the expected files
    if expected_files:
        expected_set = set(expected_files)
        generated_set = set(generated_files)
        validation_results["targets_correct_files"] = generated_set.issubset(expected_set)
        
        if not validation_results["targets_correct_files"]:
            extra_files = generated_set - expected_set
            missing_files = expected_set - generated_set
            if extra_files:
                validation_results["issues"].append(f"Targets unexpected files: {list(extra_files)}")
            if missing_files:
                validation_results["issues"].append(f"Missing expected files: {list(missing_files)}")
    else:
        validation_results["targets_correct_files"] = bool(generated_files)
    
    return validation_results


def evaluate_and_validate_patch(instance, generated_patch, api_key=None):
    """Evaluate Groq-generated patch against the expected patch using LLM reasoning and format validation."""

    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY not found. Set it as environment variable.")
            return None, 0, "No API key provided"

    # First, validate patch format
    expected_files = extract_filenames_from_patch(instance.get('patch', ''))
    validation = validate_patch_format(generated_patch, expected_files)
    
    print("="*80)
    print("PATCH FORMAT VALIDATION")
    print("="*80)
    print(f"Proper Format: {'Yes' if validation['has_proper_format'] else 'No'}")
    print(f"Targets Correct Files: {'Yes' if validation['targets_correct_files'] else 'No'}")
    print(f"Expected Files: {expected_files}")
    print(f"Generated Files: {validation['generated_files']}")
    if validation['issues']:
        print(f"Issues: {', '.join(validation['issues'])}")

    # If format validation fails badly, return early
    if not validation['has_proper_format'] and not validation['generated_files']:
        return "FAILED", 0, "Generated patch has no valid diff format or file targets"

    client = Groq(api_key=api_key)

    # Build evaluation prompt with validation context
    eval_prompt = f"""You are an expert code reviewer and senior software engineer specializing in code quality, correctness, and patch analysis.

Your task is to analyze and compare two code patches for a given programming issue. 
Your primary goal is to determine if the 'Generated Patch' correctly and effectively solves the 'Original Problem Statement' when compared to the 'Expected Patch'.

## Context: Original Problem Statement
{instance['problem_statement']}

## Target Files Analysis
Expected files to modify: {expected_files}
Generated patch targets: {validation['generated_files']}
Format validation: {'PASS' if validation['has_proper_format'] else 'FAIL'}

## Reference: Expected Patch (Ground Truth)
```diff
{instance['patch']}
```

## Generated Patch to Evaluate
```diff
{generated_patch}
```

## Format Validation Issues
{', '.join(validation['issues']) if validation['issues'] else 'None detected'}

## Evaluation Criteria
Please evaluate the Generated Patch based on:
1. **Correctness**: Does it solve the stated problem?
2. **Completeness**: Does it address all aspects of the issue?
3. **Code Quality**: Is the implementation clean and maintainable?
4. **File Targeting**: Does it modify the correct files?
5. **Format Compliance**: Is it a proper unified diff?
6. **Similarity to Expected**: How closely does it match the expected solution approach?

## Required Output Format
Provide your evaluation in this exact format:

EVALUATION_RESULT: [SUCCESS/PARTIAL/FAILED]
SIMILARITY_SCORE: [0-100]
REASONING: [Your brief analysis explaining the evaluation result and key factors]

Where:
- SUCCESS: Generated patch correctly solves the problem (75-100% similarity)
- PARTIAL: Generated patch partially solves the problem (40-74% similarity)  
- FAILED: Generated patch fails to solve the problem (0-39% similarity)
- SIMILARITY_SCORE: Numerical score from 0-100 based on correctness, format, and approach similarity
"""

    try:
        # Make API call for evaluation
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert code reviewer specializing in patch evaluation and software engineering best practices."},
                {"role": "user", "content": eval_prompt}
            ],
            max_tokens=1500,
            temperature=0.1
        )

        evaluation_response = (
            response.choices[0].message.content
            if hasattr(response.choices[0], "message")
            else response.choices[0].text
        )

        # Parse the evaluation response
        lines = evaluation_response.strip().split('\n')
        evaluation_result = "FAILED"  # Default
        similarity_score = 0  # Default
        reasoning = "Unable to parse evaluation response"

        for line in lines:
            if line.startswith("EVALUATION_RESULT:"):
                evaluation_result = line.split(":", 1)[1].strip()
            elif line.startswith("SIMILARITY_SCORE:"):
                try:
                    similarity_score = float(line.split(":", 1)[1].strip())
                except ValueError:
                    similarity_score = 0
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()

        print("\n" + "="*80)
        print("LLM PATCH EVALUATION ANALYSIS")
        print("="*80)
        print(f"Evaluation Result: {evaluation_result}")
        print(f"Similarity Score: {similarity_score}%")
        print(f"Reasoning: {reasoning}")

        return evaluation_result, similarity_score, reasoning

    except Exception as e:
        print(f"Error during LLM evaluation: {str(e)}")
        return "FAILED", 0, f"Evaluation error: {str(e)}"


def run_comprehensive_evaluation(num_tests=5):
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
                # Evaluate patches using LLM
                comparison_result, similarity_score, reasoning = evaluate_and_validate_patch(
                    instance, 
                    result['groq_generated_patch']
                )
                
                # Add evaluation results to the result
                result['comparison_result'] = comparison_result
                result['similarity_score'] = similarity_score
                result['evaluation_reasoning'] = reasoning
                
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
            "evaluation_method": "LLM-based patch evaluation with format validation",
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
    print(f"Successful fixes: {len(success_cases)} ({len(success_cases)/len(results)*100:.1f}%)" if results else "No results")
    print(f"Partial fixes: {len(partial_cases)} ({len(partial_cases)/len(results)*100:.1f}%)" if results else "")
    print(f"Failed fixes: {len(failed_cases)} ({len(failed_cases)/len(results)*100:.1f}%)" if results else "")
    print(f"Total tokens used: {total_tokens:,}")
    print(f"Results saved to: {filename}")

    return evaluation_summary


if __name__ == "__main__":
    # Run comprehensive evaluation (creates only 1 JSON file)
    if os.getenv("GROQ_API_KEY"):
        evaluation_results = run_comprehensive_evaluation(num_tests=5)
    else:
        print("  Set GROQ_API_KEY environment variable to run evaluation")
        print("  Example: export GROQ_API_KEY='your_api_key_here'")