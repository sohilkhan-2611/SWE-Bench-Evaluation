import os
from dotenv import load_dotenv
from anthropic import Anthropic

# 1. Load API key from .env
load_dotenv(".env")

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("❌ ANTHROPIC_API_KEY not found in .env")
else:
    print("✅ Anthropic API Key loaded:", api_key[:5] + "*****")

# 2. Create Anthropic client
client = Anthropic(api_key=api_key)

try:
    # 3. Small request to check connectivity
    response = client.messages.create(
        model="claude-3.5-sonnet-20240620",  # Claude Sonnet model
        max_tokens=20,
        messages=[
            {"role": "user", "content": "Write a Python program that prints Hello World"}
        ]
    )
    print("✅ API Response:", response.content[0].text)
except Exception as e:
    print("❌ Error:", str(e))