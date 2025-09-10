from datasets import load_dataset
import random

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

# Example usage
analyze_instance()