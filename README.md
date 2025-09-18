
# SWE-Bench-Evaluation

## 📝 Purpose

This codebase evaluates the capabilities of large language models (LLMs) to automatically generate correct code patches for real-world software bugs using the SWE-bench benchmark. It integrates with APIs from Groq and OpenRouter (Anthropic Sonnet) to prompt models, validate outputs, and compare their predictions against ground-truth fixes.

Evaluation and submission are conducted using the official SWE-Bench CLI (sb-cli), which ensures:
	•	Patches are applied in the original benchmark setup (repository checkout and test execution).
	•	Results follow the standard SWE-Bench evaluation protocol, making them directly comparable to        published baselines.
	•	Automatic report generation for reproducible and rigorous benchmarking.

Users can generate predictions in the required format and then submit them to SWE-Bench via sb-cli submit, followed by sb-cli get-report to retrieve evaluation results.

---

## 📘 About SWE-bench Lite

SWE-bench Lite is a dataset of real software bugs curated from open-source repositories. Each bug ("task") includes:
- **Problem statement:** Description of the bug.
- **Code context:** Relevant files.
- **Patch:** The actual fix.
- **Test patch:** Additional tests for regression prevention.


---

## aBOUT swe cli
What is SWE-Bench CLI?
SWE-Bench CLI is a command-line tool for interacting with the SWE-bench API that allows you to submit predictions, manage runs, and retrieve evaluation reports GitHubSWE-bench. It's designed to evaluate AI systems on real GitHub issues from popular Python repositories.

Installation
pip install sb-cli
Authentication
Before using the CLI, you'll need to get an API key:

Generate an API key:
sb-cli gen-api-key your.email@example.com
Set your API key as an environment variable - and store it somewhere safe!
export SWEBENCH_API_KEY=your_api_key

# or add export SWEBENCH_API_KEY=your_api_key to your .*rc file
You'll receive an email with a verification code. Verify your API key:
sb-cli verify-api-key YOUR_VERIFICATION_CODE


## 🚀 Installation

### Clone the Repository

```bash
git clone https://github.com/sohilkhan-2611/SWE-Bench-Evaluation.git
cd SWE-Bench-Evaluation
```

---


### Set Up Environment

Install dependencies:

```bash
pip install -r requirements.txt
pip install python-dotenv datasets groq openai requests
```

### Configure API Keys

Set your keys in a `.env` file or export them in your shell:

```bash
export GROQ_API_KEY="your_groq_api_key_here"
export SONNET_API_KEY="your_openrouter_api_key_here"
```

### Dataset

The evaluation script uses the `princeton-nlp/SWE-bench_Lite` dataset via Hugging Face:

```python
from datasets import load_dataset
dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
```

---


## 📂 Project Structure

- `groq_ping.py` — Test connectivity/authentication with Groq API.
- `sonnet_ping.py` — Test connectivity/authentication with Sonnet API (via OpenRouter).
- `llama_swe_bench_test.py` — Evaluate 5 random Python instances using Groq’s Llama 3.3 70B Versatile model. Results in `swe_bench_groq_llama_evaluation.json`.
- `sonnet_swe_bench_test.py` — Evaluate 5 random Python instances using Anthropic Claude 3.5 Sonnet via OpenRouter. Results in `swe_bench_sonnet_evaluation.json`.
- `test_instance_selection.py`, `test_problem_statement.py` — Utility and test scripts.
- `SWE-bench/` — Upstream SWE-bench codebase and documentation.
- ``
---


## ⚙️ Workflow

1. **Analyze instance:** Select a random Python bug and extract target files.
2. **Prompt the LLM:** Pass problem statement, failing tests, and file context to the model.
3. **Validate format:** Ensure generated patch uses correct unified diff format and targets correct files.
4. **Evaluate correctness:** Compare generated patch against ground truth and score the result.
5. **Store results:** Save all metadata and evaluation outcomes to JSON.


---


## 📈 Supported Models

- **Groq:** llama-3.3-70b-versatile
- **OpenRouter:** anthropic/claude-3.5-sonnet

---


## ✅ Example Run

**Groq (Llama 3.3 70B):**

```bash
python llama_swe_bench_test.py
# Output: swe_bench_groq_llama_evaluation_YYYYMMDD_HHMM.json
```

**Sonnet (Claude 3.5 via OpenRouter):**

```bash
python sonnet_swe_bench_test.py
# Output: swe_bench_sonnet_evaluation_YYYYMMDD_HHMM.json
```

---

---

What is SWE-Bench CLI?
SWE-Bench CLI is a command-line tool for interacting with the SWE-bench API that allows you to submit predictions, manage runs, and retrieve evaluation reports GitHubSWE-bench. It's designed to evaluate AI systems on real GitHub issues from popular Python repositories.

Installation
pip install sb-cli
Authentication
Before using the CLI, you'll need to get an API key:

Generate an API key:
sb-cli gen-api-key your.email@example.com
Set your API key as an environment variable - and store it somewhere safe!
export SWEBENCH_API_KEY=your_api_key
# or add export SWEBENCH_API_KEY=your_api_key to your .*rc file
You'll receive an email with a verification code. Verify your API key:
sb-cli verify-api-key YOUR_VERIFICATION_CODE

Usage
Submit Predictions
Submit your model's predictions to SWE-bench:

sb-cli submit swe-bench-m test \
    --predictions_path predictions.json \
    --run_id my_run_id


for further details read this file https://github.com/SWE-bench/sb-cli/blob/main/README.md#installation

I adapted the pipeline to use the standard SWE-Bench evaluation framework (sb-cli), which:
	•	Applies patches in the official benchmark setup (repo checkout, test execution).
	•	Produces standardised pass/fail outcomes comparable to published results.
	•	Ensures methodological rigor beyond my current LLM-based evaluation.


🔄 Workflow Overview

This project integrates Claude Sonnet (via OpenRouter API) with the official SWE-Bench evaluation framework (sb-cli). The workflow ensures patches are generated automatically by the model and evaluated rigorously with standardized SWE-Bench benchmarks.

1. Dataset Loading
	•	Load SWE-Bench Lite test instances (princeton-nlp/SWE-bench_Lite) using HuggingFace Datasets.
	•	Filter/select instances based on difficulty or problem length.

2. Patch Generation (Model Inference)
	•	For each selected instance:
	•	Extract the problem statement and expected target files.
	•	Send a structured prompt to Claude Sonnet via the OpenRouter API.
	•	Receive a unified diff patch as model output.

3. Results Formatting
	•	Store results (problem, patch, metadata) in JSON format.
	•	Convert them into the official SWE-Bench predictions format expected by sb-cli.

4. Official Evaluation (sb-cli)
	•	Run the SWE-Bench CLI to:
	•	Checkout the repo state for each instance.
	•	Apply the model-generated patch.
	•	Run the test suite to check correctness.
	•	Generate pass/fail reports using the standard evaluation setup.

5. Submission & Reporting
	•	Submit predictions with:

    sb-cli submit swe-bench_lite dev --predictions_path predictions.json --run_id <your_run_id>


# Submit predictions to SWE-Bench
sb-cli submit <dataset> <split> \
  --predictions_path <path_to_predictions.json> \
  --run_id <unique_run_id> \
  --gen_report 1

  Parameters
	•	<dataset> → swe-bench or swe-bench_lite
	•	<split> → train, dev, or test
	•	<path_to_predictions.json> → path to your generated predictions file
	•	<unique_run_id> → any unique name to identify this run (e.g., sonnet_20250918)