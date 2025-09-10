import os
from dotenv import load_dotenv
from groq import Groq

# Load API key from groqapi.env
load_dotenv(".env")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in groqapi.env")

client = Groq(api_key=api_key)

try:
    # Small request to check connectivity
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Write a Python program that prints Hello World"}],
        max_tokens=10,
        temperature=0.0
    )
    print("✅ API Response:", response.choices[0].message.content)
except Exception as e:
    print("❌ Error:", str(e))