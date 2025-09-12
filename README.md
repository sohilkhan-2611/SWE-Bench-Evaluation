
# SWE-Bench-Evaluation

## 📝 Purpose

This codebase evaluates the capabilities of large language models (LLMs) to automatically generate correct code patches for real-world software bugs, using the SWE-bench benchmark. It integrates with APIs from Groq and OpenRouter (Anthropic Sonnet) to prompt models, validate their outputs, and score their performance against ground truth fixes.

---

## 📘 About SWE-bench Lite

SWE-bench Lite is a dataset of real software bugs curated from open-source repositories. Each bug ("task") includes:
- **Problem statement:** Description of the bug.
- **Code context:** Relevant files.
- **Patch:** The actual fix.
- **Test patch:** Additional tests for regression prevention.


---

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

