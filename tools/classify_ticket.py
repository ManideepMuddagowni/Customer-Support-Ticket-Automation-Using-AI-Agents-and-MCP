import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()
import sys
sys.stdout.reconfigure(encoding='utf-8')
print("🔐 EURI API Key:", os.getenv("EURI_API_KEY"))
EURI_API_URL = "https://api.euron.one/api/v1/euri/alpha/chat/completions"
EURI_API_KEY = os.getenv("EURI_API_KEY")
def classify_ticket(text: str) -> dict:
    prompt = f"""
You are a smart support ticket classifier.

Given a customer ticket, classify it into:
- Sentiment: Positive, Negative, Neutral
- Issue Type: Billing, Technical, Login, General, Other

Respond ONLY with a JSON object like this:
{{
  "sentiment": "Negative",
  "issue_type": "Billing"
}}

Customer Ticket:
\"\"\"{text}\"\"\"
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
        "temperature": 0.3
    }

    try:
        response = requests.post(EURI_API_URL, headers=headers, json=payload)
        result = response.json()
        print("📨 EURI Raw Response:", result)
        content = result["choices"][0]["message"]["content"]

        # Safer JSON parsing
        parsed = json.loads(content)
        return {
            "sentiment": parsed.get("sentiment", "Unknown"),
            "issue_type": parsed.get("issue_type", "General")
        }

    except Exception as e:
        print("⚠️ Classification Error:", e)
        return {"sentiment": "Unknown", "issue_type": "General"}
