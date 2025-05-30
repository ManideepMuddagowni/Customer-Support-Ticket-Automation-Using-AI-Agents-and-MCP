import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("🚫 GROQ_API_KEY is missing from your .env file")

client = Groq(api_key=GROQ_API_KEY)

def generate_reply(name: str, text: str) -> str:
    prompt = f"""
You are a friendly and professional customer support agent.

Respond to the following issue with empathy, clear explanation, and helpful advice.

Include a greeting using the customer's first name and end the message with:
Best regards,
Customer Support Team

Customer Name: {name}

Issue:
\"\"\"{text}\"\"\"

Only return the final response message.
"""

    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
            top_p=1,
            stream=True,
            stop=None,
        )
    except Exception as e:
        print(f"⚠️ API call failed: {e}")
        return f"Hello {name},\n\nWe are currently unable to process your request. Please try again later.\n\nBest regards,\nCustomer Support Team"

    reply_text = ""  # Collect reply here

    try:
        for chunk in completion:
            if hasattr(chunk, "choices") and chunk.choices:
                delta_content = getattr(chunk.choices[0].delta, "content", None)
                if delta_content:
                    print(delta_content, end="", flush=True)  # optional: streaming print
                    reply_text += delta_content
            else:
                print("\n⚠️ Unexpected chunk format or error received.", flush=True)
                break

    except Exception as e:
        print(f"\n⚠️ Error during streaming response: {e}", flush=True)

    print()  # newline after streaming print
    return reply_text
