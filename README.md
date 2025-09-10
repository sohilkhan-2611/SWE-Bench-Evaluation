# SWE-Bench-Evaluation
Evaluation of LLMs on SWE-bench via API integration. Focused on generating patches to fix GitHub issues with failing test cases while preserving existing functionality. Demonstrates real-world software engineering problem-solving


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
    def __init__(self, api_key: str = None):
This class acts as your agent for running SWE-bench problems on Groq’s LLMs.