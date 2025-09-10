from datasets import load_dataset
import os
import json
import logging
from typing import List, Dict

# if __name__ == "__main__":

#     # Load SWE-bench Lite
#     dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
#     print(f"Total dataset size: {len(dataset)}")


#     # Look at the first row
#     print(dataset[0].keys())
#     print(dataset[0]["instance_id"])
#     print(dataset[0]["problem_statement"])

def explore_swe_bench_dataset():
    """Explore SWE-bench Lite dataset structure and content"""
    
    # Load dataset
    print("Loading SWE-bench Lite dataset...")
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    
    print(f"Total dataset size: {len(dataset)}")
    print(f"Dataset keys: {list(dataset[0].keys())}")
    
    # Examine first instance in detail
    first_instance = dataset[0]
    
    print("\n" + "="*60)
    print("FIRST INSTANCE ANALYSIS")
    print("="*60)
    
    print(f"Instance ID: {first_instance['instance_id']}")
    print(f"Repository: {first_instance['repo']}")
    print(f"Base commit: {first_instance['base_commit']}")
    
    print(f"\nProblem Statement:")
    print("-" * 40)
    print(first_instance['problem_statement'])
    
    print(f"\nPatch (Expected Solution):")
    print("-" * 40)
    print(first_instance['patch'][:500] + "..." if len(first_instance['patch']) > 500 else first_instance['patch'])
    
    if 'test_patch' in first_instance:
        print(f"\nTest Patch:")
        print("-" * 40)
        print(first_instance['test_patch'][:300] + "..." if len(first_instance['test_patch']) > 300 else first_instance['test_patch'])
    
    # Show repository statistics
    print(f"\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    
    repos = {}
    for item in dataset:
        repo = item['repo']
        repos[repo] = repos.get(repo, 0) + 1
    
    print("Top repositories by number of issues:")
    sorted_repos = sorted(repos.items(), key=lambda x: x[1], reverse=True)
    for repo, count in sorted_repos[:10]:
        print(f"  {repo}: {count} issues")
    
    # Analyze problem complexity
    problem_lengths = [len(item['problem_statement']) for item in dataset]
    avg_length = sum(problem_lengths) / len(problem_lengths)
    
    print(f"\nProblem statement statistics:")
    print(f"  Average length: {avg_length:.0f} characters")
    print(f"  Shortest: {min(problem_lengths)} characters")
    print(f"  Longest: {max(problem_lengths)} characters")
    
    return dataset

def get_simple_instances(dataset, n=5):
    """Get simpler instances for initial testing"""
    
    print(f"\n" + "="*60)
    print(f"SELECTING {n} SIMPLER INSTANCES FOR TESTING")
    print("="*60)
    
    # Sort by problem statement length (shorter = potentially simpler)
    sorted_instances = sorted(
        enumerate(dataset), 
        key=lambda x: len(x[1]['problem_statement'])
    )
    
    simple_instances = []
    for i, (idx, instance) in enumerate(sorted_instances[:n]):
        simple_instances.append({
            'original_index': idx,
            'instance_id': instance['instance_id'],
            'repo': instance['repo'],
            'problem_statement': instance['problem_statement'],
            'patch': instance['patch'],
            'test_patch': instance.get('test_patch', ''),
            'problem_length': len(instance['problem_statement'])
        })
        
        print(f"\n{i+1}. {instance['instance_id']} (Length: {len(instance['problem_statement'])})")
        print(f"   Repo: {instance['repo']}")
        print(f"   Problem: {instance['problem_statement'][:100]}...")
    
    return simple_instances

def save_test_instances(instances, filename="test_instances.json"):
    """Save selected instances for testing"""
    with open(filename, 'w') as f:
        json.dump(instances, f, indent=2)
    print(f"\nSaved {len(instances)} test instances to {filename}")

if __name__ == "__main__":
    # Load and explore dataset
    dataset = explore_swe_bench_dataset()
    
    # Get simpler instances for initial testing
    test_instances = get_simple_instances(dataset, n=10)
    
    # Save for later use
    save_test_instances(test_instances)
    
    print(f"\n" + "="*60)
    print("RECOMMENDATIONS FOR YOUR TASK")
    print("="*60)
    print("1. Start with the shorter problem statements (they tend to be simpler)")
    print("2. Focus on Python repositories you recognize (pandas, requests, etc.)")
    print("3. Read the 'patch' field to understand expected solutions")
    print("4. Use 'problem_statement' as input to your Groq model")
    print("5. Compare your model's output with the 'patch' field")
