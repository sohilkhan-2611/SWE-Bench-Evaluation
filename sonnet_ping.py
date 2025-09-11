import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("SONNET_API_KEY")  

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "anthropic/claude-3.5-sonnet",
    "messages": [
        {"role": "user", "content": "Hello Sonnet, are you working?"}
    ]
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())