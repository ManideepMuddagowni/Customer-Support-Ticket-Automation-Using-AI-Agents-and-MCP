import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("🚫 GROQ_API_KEY is missing from your .env file")

client = Groq(api_key=GROQ_API_KEY)

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

    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",  # your intended model
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
            stream=False  # no streaming for classification, simpler usage
        )

        # The response content text is here:
        content = completion.choices[0].message.content
        print("📨 Groq Raw Response:", content)

        # Safely parse JSON string returned by the model
        parsed = json.loads(content)
        return {
            "sentiment": parsed.get("sentiment", "Unknown"),
            "issue_type": parsed.get("issue_type", "General")
        }

    except Exception as e:
        print("⚠️ Classification Error:", e)
        return {"sentiment": "Unknown", "issue_type": "General"}
