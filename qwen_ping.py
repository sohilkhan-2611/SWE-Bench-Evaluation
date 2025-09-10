import os
from openai import OpenAI
from dotenv import load_dotenv

#Load API key from .env
load_dotenv(".env")

api_key =  os.getenv("QWEN_API_KEY")
if not api_key:
    raise ValueError("❌ API key not found. Please set QWEN_API_KEY in your .env")
else:
    print("✅ Qwen API Key loaded:", api_key[:5] + "*****")

# Configure OpenAI client with Qwen base URL
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

# 3. Send minimal prompt to check connectivity
try:
    response = client.chat.completions.create(
        model="qwen-max",                # Use the appropriate Qwen model name
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=5,
        temperature=0.0
    )
    print("✅ Qwen API Response:", response.choices[0].message.content)
except Exception as e:
    print("❌ Error calling Qwen API:", str(e))