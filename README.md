SWE-Bench-Evaluation

Evaluation of Large Language Models (LLMs) on the SWE-bench benchmark via API integration.
This project focuses on generating minimal, correct patches to fix real-world GitHub issues with failing test cases, while preserving existing functionality.

The evaluation demonstrates how modern LLMs can be applied to software engineering tasks such as debugging, patch generation, and regression prevention.

📘 About SWE-bench Lite

SWE-bench Lite is a dataset of real software bugs curated from popular open-source repositories.
For each bug (we call it a “task”), the dataset provides:
	1.	Problem statement → short description of what’s broken.
	2.	Code context → the relevant files where the bug appears.
	3.	Patch → the actual fix that the original developer wrote (ground truth).
	4.	Test patch → sometimes, additional tests added by the developer to prevent regressions.

When you see "patch" in the dataset, it means:

👉 “Here is the exact code change that fixed this bug in real life.”

Your job (or the AI’s job) is to come up with a similar fix. The generated patch is then compared to the ground-truth patch to determine whether the LLM solved the issue correctly.


🚀 Getting Started

1. Clone the SWE-bench repository

git clone https://github.com/princeton-nlp/SWE-bench.git
cd SWE-bench

2. Set up environment

Install dependencies:
pip install -r requirements.txt
pip install python-dotenv
pip install datasets
pip install groq openai requests


Configure API keys in your shell or in a .env file:
export GROQ_API_KEY="your_groq_api_key_here"
export SONNET_API_KEY="your_openrouter_api_key_here"


3. Dataset

The evaluation script uses the princeton-nlp/SWE-bench_Lite dataset via Hugging Face:

from datasets import load_dataset
dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")



📂 Project Structure
	•	groq_ping.py
Quick check script to test connectivity and authentication with the Groq API.
	•	sonnet_ping.py
Quick check script to test connectivity and authentication with the Sonnet API (via OpenRouter).
	•	llama_swe_bench_test.py
Evaluation script that runs 5 random Python instances from SWE-bench Lite using Groq’s Llama 3.3 70B Versatile model.
Stores results (logs, generated patches, evaluation) in: swe_bench_groq_llama_evaluation.json

sonnet_swe_bench_test.py
Evaluation script that runs 5 random Python instances from SWE-bench Lite using Anthropic Claude 3.5 Sonnet via OpenRouter.
Stores results in: swe_bench_sonnet_evaluation.json

⚙️ Workflow
	1.	Analyze instance
	•	Selects a random Python bug from SWE-bench Lite (with filters for simplicity).
	•	Extracts target files from the provided ground-truth patch.
	2.	Prompt the LLM
	•	Passes the problem statement, failing tests, and target file context to the model.
	•	The model is asked to output a minimal unified diff patch (git diff format).
	3.	Validate format
	•	Ensures the generated patch follows the correct --- a/ / +++ b/ diff format.
	•	Checks whether the patch modifies the correct target files.
	4.	Evaluate correctness
	•	The generated patch is compared against the expected patch.
	•	An LLM-based evaluator scores the result:
	•	✅ SUCCESS: Correct fix (75–100% similarity)
	•	⚠️ PARTIAL: Partially correct (40–74%)
	•	❌ FAILED: Incorrect (0–39%)
	5.	Store results
	•	All results (instance metadata, problem, expected patch, generated patch, evaluation outcome) are saved into a JSON file.


	📈 Current Models Supported
	•	Groq → llama-3.3-70b-versatile
	•	OpenRouter → anthropic/claude-3.5-sonnet


✅ Example Run

Groq (Llama 3.3 70B)
python llama_swe_bench_test.py
Output:
swe_bench_groq_llama_evaluation_20250912_0210.json

Sonnet (Claude 3.5 via OpenRouter)
python sonnet_swe_bench_test.py

Output:
swe_bench_sonnet_evaluation_20250912_0210.json