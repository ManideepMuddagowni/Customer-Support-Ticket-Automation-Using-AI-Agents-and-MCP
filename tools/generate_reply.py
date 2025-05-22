import os
import requests
from dotenv import load_dotenv
load_dotenv()
import sys
sys.stdout.reconfigure(encoding='utf-8')
print("✅ EURI API KEY (partial):", os.getenv("EURI_API_KEY")[:20])

EURI_API_URL = "https://api.euron.one/api/v1/euri/alpha/chat/completions"
EURI_API_KEY = os.getenv("EURI_API_KEY")

def generate_reply(text: str) -> str:
    prompt = f"""
You are a friendly and professional customer support agent

Respond to the following issue with empathy, clear explanation, and helpful advice.

Issue:
\"\"\"{text}\"\"\"

Only return the final response message.
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {EURI_API_KEY}"
    }

    payload = {
        "model": "gpt-4.1-nano",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.5
    }

    try:
        response = requests.post(EURI_API_URL, headers=headers, json=payload)
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("❌ Reply Generation Error:", e)
        return "We’re experiencing some technical issues. Our support team will respond as soon as possible."
