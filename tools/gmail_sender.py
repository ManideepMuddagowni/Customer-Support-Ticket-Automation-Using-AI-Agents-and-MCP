import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
    raise ValueError("❌ EMAIL_ADDRESS or EMAIL_APP_PASSWORD not found in .env")

print("🔐 Loaded credentials:")
print("Email:", EMAIL_ADDRESS)
print("App Password (length):", len(EMAIL_APP_PASSWORD))


# ✅ Reusable Email Sender Function
def send_email_smtp(to, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        print(f"📡 Connecting to smtp.gmail.com to send email to {to}...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(0)  # Set to 1 to enable full SMTP debug
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("✅ Email sent successfully to:", to)
        return {"status": "success", "message": f"Email sent to {to}"}
    except Exception as e:
        print("❌ Failed to send email:", e)
        return {"status": "error", "message": str(e)}
