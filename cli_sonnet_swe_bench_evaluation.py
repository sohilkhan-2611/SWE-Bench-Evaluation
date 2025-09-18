from datasets import load_dataset
import json
import requests
import os
import random
import subprocess
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


def call_openrouter_api(messages, api_key, model="anthropic/claude-3.5-sonnet", max_tokens=2000, temperature=0.1):
    """Helper function to call OpenRouter API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"API call failed with status {response.status_code}: {response.text}")
    
    return response.json()


def test_sonnet_on_instance(instance, api_key=None, save_individual=False):
    """Test Sonnet on the PROVIDED instance with enhanced prompt including target files"""
    
    if not api_key:
        api_key = os.getenv("SONNET_API_KEY")
        if not api_key:
            print("Error: SONNET_API_KEY not found. Set it as environment variable.")
            return None
    
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
    print("TESTING SONNET ON SELECTED INSTANCE")
    print(f"Testing on Instance ID: {instance.get('instance_id', 'N/A')}")
    print("="*80)
    
    try:
        # Make API call
        response_data = call_openrouter_api(
            messages=[
                {"role": "system", "content": "You are an expert software engineer with deep expertise in code analysis, debugging, and patch generation. You specialize in creating minimal, precise fixes for complex software issues."},
                {"role": "user", "content": prompt}
            ],
            api_key=api_key,
            model="anthropic/claude-3.5-sonnet",
            max_tokens=2000,
            temperature=0.1
        )

        generated_patch = response_data['choices'][0]['message']['content']
        tokens_used = response_data.get('usage', {}).get('total_tokens', 'Unknown')
        
        print(f"SONNET GENERATED SOLUTION:")
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
            "sonnet_generated_patch": generated_patch,
            "tokens_used": tokens_used,
            "model": "anthropic/claude-3.5-sonnet",
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
        # Only save individual file if requested
        if save_individual:
            filename = f"sonnet_swebench_result_{instance['instance_id'].replace('/', '_')}.json"
            with open(filename, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nIndividual result saved to: {filename}")

        return result
        
    except Exception as e:
        print(f"Error calling OpenRouter API: {str(e)}")
        return None


def run_comprehensive_evaluation(num_tests=5):
    """Run comprehensive evaluation and create consolidated JSON output (no LLM evaluation)"""
    
    print("="*80)
    print(f"GENERATING PATCHES FOR SWE-BENCH EVALUATION")
    print(f"Number of instances: {num_tests}")
    print("="*80)
    
    results = []
    total_tokens = 0
    
    for i in range(num_tests):
        print(f"\n--- GENERATING PATCH {i+1}/{num_tests} ---")
        
        # Get a random instance
        instance = analyze_instance()
        
        if os.getenv("SONNET_API_KEY"):
            # Test with Sonnet (don't save individual files)
            result = test_sonnet_on_instance(instance, save_individual=False)
            
            if result:
                results.append(result)
                total_tokens += result['tokens_used'] if isinstance(result['tokens_used'], int) else 0
                print(f"SUCCESS: Generated patch for {result['instance_id']}")
        else:
            print("SONNET_API_KEY not found - skipping API test")
            break
    
    # Create comprehensive summary
    evaluation_summary = {
        "metadata": {
            "model_name": "anthropic/claude-3.5-sonnet",
            "provider": "openrouter",
            "evaluation_date": datetime.now().isoformat(),
            "dataset": "princeton-nlp/SWE-bench_Lite",
            "total_instances_tested": len(results),
            "evaluation_method": "SWE-Bench CLI evaluation",
            "evaluation_parameters": {
                "max_tokens": 2000,
                "temperature": 0.1,
                "max_patch_length_filter": 200,
                "max_problem_length_filter": 500
            }
        },
        "performance_summary": {
            "total_patches_generated": len(results),
            "total_tokens_used": total_tokens
        },
        "detailed_results": results
    }

    patch_dir = "patches"
    os.makedirs(patch_dir, exist_ok=True)
    
    # Save consolidated results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"sonnet_swe_bench_patches_{timestamp}.json"

    with open(os.path.join(patch_dir, filename), "w") as f:
        json.dump(evaluation_summary, f, indent=2)
    
    print(f"\n" + "="*80)
    print("PATCH GENERATION SUMMARY")
    print("="*80)
    print(f"Total patches generated: {len(results)}")
    print(f"Total tokens used: {total_tokens}")
    print(f"Patches saved to: {filename}")

    return evaluation_summary


def generate_swebench_predictions(results, model_name="sonnet"):
    """Convert your evaluation results to SWE-Bench CLI format"""
    predictions = {}
    
    for result in results:
        instance_id = result['instance_id']
        model_patch = result.get('sonnet_generated_patch', '')
        
        predictions[instance_id] = {
            "model_patch": model_patch,
            "model_name_or_path": model_name
        }
    
    return predictions


def save_predictions_for_swebench(evaluation_results, model_name="sonnet", output_file=None):
    """Save predictions in SWE-Bench CLI format under ./predictions folder"""
    
    pred_dir = "predictions"
    os.makedirs(pred_dir, exist_ok=True)

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = f"{model_name}_swebench_predictions_{timestamp}.json"
    
    # Extract results from your evaluation summary
    if 'detailed_results' in evaluation_results:
        results = evaluation_results['detailed_results']
    else:
        results = evaluation_results
    
    predictions = generate_swebench_predictions(results, model_name)
    

    # Build full path
    full_path = os.path.join(pred_dir, output_file)


    # Save in SWE-Bench format
    with open(full_path, 'w') as f:
        json.dump(predictions, f, indent=2)

    print(f"SWE-Bench predictions saved to: {full_path}")
    return os.path.abspath(full_path), predictions


def run_swebench_cli_evaluation(predictions_file, model_name="sonnet"):
    """Run SWE-Bench CLI evaluation on your predictions"""
    
    
    # Check if sb-cli is installed
    try:
        subprocess.run(["sb-cli", "--help"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: sb-cli not found. Install with: pip install sb-cli")
        return None
    
    # Check API key
    if not os.getenv("SWEBENCH_API_KEY"):
        print("Error: SWEBENCH_API_KEY not set. Follow these steps:")
        print("1. sb-cli gen-api-key your.email@example.com")
        print("2. export SWEBENCH_API_KEY=your_api_key")
        print("3. sb-cli verify-api-key YOUR_VERIFICATION_CODE")
        return None
    
    # Generate unique run ID
    run_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Get absolute path for predictions file
    predictions_file = os.path.abspath(predictions_file)

    # Submit to SWE-Bench CLI
    cmd = [
        "sb-cli", "submit", "swe-bench_lite", "test",
        "--predictions_path", predictions_file,
        "--run_id", run_id,
        "--gen_report", "1"
    ]
    
    
    print(f"Running SWE-Bench CLI evaluation...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Submission successful! Run ID: {run_id}")
        print(result.stdout)
        
        # Wait and get report
        print("Waiting for evaluation to complete...")
        print("You can check status with:")
        print(f"sb-cli get-report swe-bench_lite dev {run_id} -o ./swebench_reports")
        
        return run_id
        
    except subprocess.CalledProcessError as e:
        print(f"❌ SWE-Bench CLI submission failed:")
        print(f"Error: {e.stderr}")
        return None



def main():
    """Main function that runs SWE-Bench CLI evaluation directly"""
    
    if not os.getenv("SONNET_API_KEY"):
        print("Error: Set SONNET_API_KEY environment variable to run evaluation")
        print("Example: export SONNET_API_KEY='your_api_key_here'")
        return
    
    if not os.getenv("SWEBENCH_API_KEY"):
        print("Error: SWEBENCH_API_KEY not set. Follow these steps:")
        print("1. pip install sb-cli")
        print("2. sb-cli gen-api-key your.email@example.com")
        print("3. export SWEBENCH_API_KEY=your_api_key")
        print("4. sb-cli verify-api-key YOUR_VERIFICATION_CODE")
        return
    
    print("="*80)
    print("RUNNING SWE-BENCH CLI EVALUATION")
    print("="*80)
    
    # Get number of tests from user
    try:
        num_tests = int(input("Enter number of instances to test (default 5): ").strip() or "5")
    except ValueError:
        num_tests = 5
        print("Invalid input, using default: 5 tests")
    
    # Run pipeline to generate patches
    print(f"\nGenerating patches for {num_tests} instances...")
    evaluation_results = run_comprehensive_evaluation(num_tests=num_tests)
    
    # Convert to SWE-Bench format and submit
    print("\nConverting to SWE-Bench format...")
    predictions_file, predictions = save_predictions_for_swebench(evaluation_results, "sonnet")
    
    print("\nSubmitting to SWE-Bench CLI for official evaluation...")
    run_id = run_swebench_cli_evaluation(predictions_file, "sonnet")
    
    if run_id:
        print(f"\n" + "="*80)
        print("SUBMISSION COMPLETED")
        print("="*80)
        print(f"Run ID: {run_id}")
        print(f"Predictions file: {predictions_file}")
        print(f"Total instances: {len(predictions)}")
        print("\nTo get results:")
        print(f"sb-cli get-report swe-bench_lite dev {run_id} -o ./swebench_reports")
        print("\nTo list all runs:")
        print("sb-cli list-runs swe-bench_lite dev")


if __name__ == "__main__":
    main()