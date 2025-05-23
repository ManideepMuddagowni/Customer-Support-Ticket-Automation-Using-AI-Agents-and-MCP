from mcp.server.fastmcp import FastMCP
from tools.sheet_connector import update_ticket, append_processed_ticket
from tools.classify_ticket import classify_ticket
from tools.generate_reply import generate_reply
from tools.gmail_sender import send_email_smtp


mcp = FastMCP("AICustomerSupportTicketResolver")

@mcp.tool(name="resolve_ticket", description="Classifies, replies, updates, and emails a support ticket.")
def resolve_ticket(name: str, email: str, message: str) -> dict:
    try:
        # Step 1: AI Classify
        classification = classify_ticket(message)
        sentiment = classification["sentiment"]
        issue_type = classification["issue_type"]

        # Step 2: Generate reply
        reply = generate_reply(message)

        # Step 3: Update Google Sheet (append only)
        fake_ticket = {
            "Name": name,
            "Email": email,
            "IssueType": issue_type,
            "Message": message
        }
        append_processed_ticket(fake_ticket, sentiment, issue_type, reply)

        # Step 4: Send Email
        mail_result = send_email_smtp(
                        to=email,
                        subject="Regarding Your Support Ticket",
                        body=reply
                    )

        return {
                "status": "success",
                "sentiment": sentiment,
                "issue_type": issue_type,
                "reply": reply,
                "email_status": mail_result.get("status"),
                "email_message": mail_result.get("message", "Email sent.")
              }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    mcp.run()
