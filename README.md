# SWE-Bench Evaluation

A comprehensive evaluation framework for testing Large Language Models (LLMs) on real-world software bug fixing using the SWE-bench benchmark. This project integrates with Groq and OpenRouter APIs to automatically generate code patches and evaluate them against ground-truth fixes using the official SWE-Bench CLI.

## 📋 Table of Contents

- [About](#about)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Supported Models](#supported-models)
- [Workflow](#workflow)
- [SWE-Bench CLI Integration](#swe-bench-cli-integration)
- [Examples](#examples)
- [Contributing](#contributing)

## 📝 About

This codebase evaluates the capabilities of large language models to automatically generate correct code patches for real-world software bugs using the SWE-bench benchmark. The evaluation process integrates with the official SWE-Bench CLI (sb-cli) to ensure:

- ✅ Patches are applied in the original benchmark setup (repository checkout and test execution)
- ✅ Results follow the standard SWE-Bench evaluation protocol
- ✅ Direct comparability to published baselines
- ✅ Automatic report generation for reproducible benchmarking

### About SWE-bench Lite

SWE-bench Lite is a curated dataset of real software bugs from open-source repositories. Each task includes:

- **Problem statement:** Description of the bug
- **Code context:** Relevant files and code snippets
- **Ground truth patch:** The actual fix that resolved the issue
- **Test patch:** Additional tests for regression prevention

## 🚀 Features

- **Multi-Model Support:** Evaluate different LLMs (Groq Llama, Claude Sonnet)
- **Official Integration:** Uses SWE-Bench CLI for standardized evaluation
- **Automated Pipeline:** End-to-end patch generation and evaluation
- **Structured Output:** JSON results with detailed metadata
- **Reproducible:** Consistent evaluation methodology

## 📦 Installation

### Prerequisites

- Python 3.8+
- Git

### Clone the Repository

```bash
git clone https://github.com/sohilkhan-2611/SWE-Bench-Evaluation.git
cd SWE-Bench-Evaluation
```

### Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install python-dotenv datasets groq openai requests

# Install SWE-Bench CLI
pip install sb-cli
```

## ⚙️ Configuration

### API Keys Setup

Create a `.env` file in the project root or set environment variables:

```bash
# .env file
GROQ_API_KEY=your_groq_api_key_here
SONNET_API_KEY=your_openrouter_api_key_here

# Or export in shell
export GROQ_API_KEY="your_groq_api_key_here"
export SONNET_API_KEY="your_openrouter_api_key_here"
```

### SWE-Bench CLI Authentication

Before using the SWE-Bench CLI, you need to authenticate:

```bash
# Generate API key
sb-cli gen-api-key your.email@example.com

# Set environment variable
export SWEBENCH_API_KEY=your_api_key

# Verify with the code sent to your email
sb-cli verify-api-key YOUR_VERIFICATION_CODE
```

## 🎯 Usage

### Quick Start

Test API connectivity:
```bash
# Test Groq API
python groq_ping.py

# Test Sonnet API
python sonnet_ping.py
```

### Run Evaluations

**Evaluate with Groq Llama 3.3 70B:**
```bash
python swe_bench_cli_llama.py
# Output: swe_bench_groq_llama_evaluation_YYYYMMDD_HHMM.json
```

**Evaluate with Claude 3.5 Sonnet:**
```bash
python swe_bench_cli_sonnet.py
# Output: swe_bench_sonnet_evaluation_YYYYMMDD_HHMM.json
```

### Submit to SWE-Bench

After generating predictions, submit them to the official SWE-Bench evaluation:

```bash
# Submit predictions
sb-cli submit swe-bench_lite dev \
    --predictions_path predictions.json \
    --run_id your_unique_run_id \
    --gen_report 1

# Get evaluation report
sb-cli get-report your_unique_run_id
```

## 📂 Project Structure

```
SWE-Bench-Evaluation/
├── README.md
├── requirements.txt
├── .env.example
├── ping_groq.py                          # Test Groq API connectivity
├── ping_sonnet.py                        # Test Sonnet API connectivity
├── llama_swe_bench_test.py               # Groq Llama evaluation with custom python script
├── sonnet_swe_bench_test.py              # Claude Sonnet evaluation with custom python script
├── cli_llama_swe_bench_evaluation.py     # Evaluate Groq Llama via official SWE-Bench CLI  
├── cli_sonnet_swe_bench_evaluation.py    # Evaluate Claude Sonnet via official SWE-Bench CLI 
└── test files
    -test_instance_selection.py           # Utility for instance selection
    ──test_problem_statement.py           # Test problem statement extraction
└── SWE-bench/                            # Upstream SWE-bench documentation
└──sb-cli/                             # SWE-Bench CLI for submitting predictions and generating reports
└──sb-ci-reports                      # Generated evaluation results
    -swe-bench_lite__test__sonnet_20250919_120804.json.   # Example report generated by Sonnet API
```

## 🤖 Supported Models

| Provider | Model | API Endpoint |
|----------|-------|--------------|
| **Groq** | llama-3.3-70b-versatile | Groq API |
| **OpenRouter** | anthropic/claude-3.5-sonnet | OpenRouter API |

## 🔄 Workflow

The evaluation pipeline follows these steps:

### 1. Dataset Loading
- Load SWE-Bench Lite test instances from HuggingFace
- Filter instances based on criteria (language, difficulty)

### 2. Instance Analysis
- Extract problem statement and failing tests
- Identify target files that need modification
- Prepare context for the LLM

### 3. Patch Generation
- Send structured prompt to the LLM
- Request unified diff format patches
- Validate patch format and target files

### 4. Result Processing
- Store generated patches with metadata
- Format results for SWE-Bench CLI submission
- Save evaluation outcomes to JSON

### 5. Official Evaluation
- Submit to SWE-Bench using sb-cli
- Apply patches in isolated environments
- Run test suites to determine correctness
- Generate standardized reports

## 🛠️ SWE-Bench CLI Integration

This project leverages the official SWE-Bench CLI for rigorous evaluation:

### Key Commands

```bash
# Submit predictions
sb-cli submit <dataset> <split> \
    --predictions_path <path_to_predictions.json> \
    --run_id <unique_run_id> \
    --gen_report 1

# Parameters:
# <dataset>: swe-bench or swe-bench_lite
# <split>: train, dev, or test
# <path_to_predictions.json>: path to your predictions file
# <unique_run_id>: unique identifier for the run
```

### Benefits of CLI Integration

- **Standardized Environment:** Tests run in the original repository setup
- **Automated Validation:** Patches are applied and tested automatically  
- **Comparable Results:** Results directly comparable to published benchmarks
- **Detailed Reports:** Comprehensive evaluation metrics and error analysis

## 📊 Examples

### Sample Evaluation Output

```json
{
  "instance_id": "django__django-12345",
  "model_name": "claude-3.5-sonnet",
  "problem_statement": "Fix database connection pooling issue...",
  "generated_patch": "--- a/django/db/backends/base.py\n+++ b/django/db/backends/base.py\n...",
  "evaluation": {
    "patch_applied": true,
    "tests_passed": true,
    "score": 1.0
  },
  "metadata": {
    "timestamp": "2025-09-18T10:30:00Z",
    "processing_time": 15.2,
    "target_files": ["django/db/backends/base.py"]
  }
}
```

### Sample SWE-Bench Submission Format

```json
[
  {
    "instance_id": "django__django-12345",
    "model_patch": "--- a/django/db/backends/base.py\n+++ b/django/db/backends/base.py\n@@ -100,7 +100,7 @@\n-    old_code\n+    new_code\n",
    "model_name_or_path": "claude-3.5-sonnet"
  }
]
```

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🔗 Links

- [SWE-Bench Official Repository](https://github.com/princeton-nlp/SWE-bench)
- [SWE-Bench CLI Documentation](https://github.com/SWE-bench/sb-cli)
- [SWE-Bench Lite Dataset](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite)
- [Groq API Documentation](https://console.groq.com/docs)
- [OpenRouter API Documentation](https://openrouter.ai/docs)

