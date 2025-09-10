# SWE-Bench-Evaluation
Evaluation of LLMs on SWE-bench via API integration. Focused on generating patches to fix GitHub issues with failing test cases while preserving existing functionality. Demonstrates real-world software engineering problem-solving

The SWE-bench Lite dataset is like a big collection of real software bugs.

For each bug (we call it a “task”), the dataset gives you:
	1.	Problem statement → a short description of what’s broken.
	2.	Code context → the piece of code where the bug happens.
	3.	Patch → the actual fix that the real developer wrote (the answer).
	4.	Test patch → sometimes, new tests the developer added to make sure the bug won’t come back.

So when you see "patch" in the dataset, it means:
👉 “Here is the exact code change that fixed this bug in real life.”

Your job (or the AI’s job) is to try to come up with the same kind of fix, and then you can compare it to the dataset’s patch to check if the AI solved it correctly.



cloen the repo 
git clone https://github.com/princeton-nlp/SWE-bench.git
cd SWE-bench


I'm trying with groq ai 
I’m using this llama-3.3-70b-versatile
* 
 i creared swe-bench dataset py file to check swe bench lite dataset has been loaded or not 

 next i am working on groq agent 

 import os, time, json, logging
from groq import Groq
from typing import Dict, Any, List


	•	os → for environment variables (API keys)
	•	time → used for rate limiting requests
	•	json → formatting output into JSON
	•	logging → keeps track of progress and errors
	•	Groq → Groq API client
	•	typing → type hints for cleaner code

The GroqSWEAgent class

class GroqSWEAgent:

This class acts as your agent for running SWE-bench problems on Groq’s LLMs.

there are three .py files 

groq_ping.py - to check and ping Groq API
qwen_ping.py - to check and ping Qwen API
sonnet_ping.py - to check and ping Sonnet API

DATASET.PY - File contactins Swe bench lite dataset