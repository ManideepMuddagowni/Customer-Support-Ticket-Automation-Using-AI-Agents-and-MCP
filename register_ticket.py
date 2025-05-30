import streamlit as st
import re
from tools.sheet_connector import (
    get_pending_sheet,
    fetch_new_tickets,
    update_ticket,
    append_processed_ticket,
    delete_ticket_from_pending
)
from tools.classify_ticket import classify_ticket
from tools.generate_reply import generate_reply
from tools.gmail_sender import send_email_smtp

st.set_page_config(page_title="Submit a Support Ticket", page_icon="📩")
st.title("📩 Submit a Support Ticket")
st.markdown("We'll get back to you shortly with a helpful response.")

def append_ticket_to_pending(name, email, issue_type, message):
    sheet = get_pending_sheet()
    try:
        # Append new ticket to PendingTickets with empty Sentiment, IssueType_Label, AutoReply
        sheet.append_row([name, email, issue_type, message, "", "", ""])
        return True
    except Exception as e:
        st.error(f"Failed to append ticket to PendingTickets: {e}")
        return False

with st.form("ticket_form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    issue_type = st.selectbox("Issue Type", ["Billing", "Technical", "Login Issue", "Other"])
    message = st.text_area("Describe your issue", height=200)

    submitted = st.form_submit_button("Submit Ticket")

    if submitted:
        if not name or not email or not message:
            st.error("Please fill in all required fields.")
        else:
            # Step 1: Append raw ticket to PendingTickets sheet
            success = append_ticket_to_pending(name, email, issue_type, message)
            if not success:
                st.stop()

            with st.spinner("🤖 Classifying ticket and generating reply..."):
                # Step 2: AI Classification and reply generation
                classification = classify_ticket(message)
                reply = generate_reply(message, name)

                # --- CLEAN REPLY: Remove any text before "Hi <name>" ---
                match = re.search(r"\bHi\s+" + re.escape(name), reply, re.IGNORECASE)
                if match:
                    reply = reply[match.start():].strip()
                else:
                    reply = reply.strip()
                # --------------------------------------------------------

                # Step 3: Send auto-reply email
                status = send_email_smtp(
                    to=email,
                    subject="Regarding Your Support Ticket",
                    body=reply
                )

                if status.get("status") == "success":
                    st.success("📬 Email reply sent successfully!")

                    # Step 4: Find the newly appended ticket's row number
                    # Fetch all pending tickets that need classification (Sentiment or AutoReply empty)
                    pending_tickets = fetch_new_tickets()

                    # Find the ticket by unique info (name+email+message)
                    row_number = None
                    for t in pending_tickets:
                        if (
                            t.get("Name") == name and
                            t.get("Email") == email and
                            t.get("Message") == message
                        ):
                            row_number = t.get("RowNumber")
                            break

                    if row_number:
                        # Step 5: Update the ticket row in PendingTickets
                        update_ticket(
                            row_number=row_number,
                            sentiment=classification["sentiment"],
                            issue_type=classification["issue_type"],
                            reply=reply
                        )

                        # Step 6: Append processed ticket to ProcessedTickets sheet
                        append_processed_ticket(
                            ticket={"Name": name, "Email": email, "IssueType": issue_type, "Message": message},
                            sentiment=classification["sentiment"],
                            issue_type=classification["issue_type"],
                            reply=reply
                        )
                    else:
                        st.warning("⚠️ Could not find the ticket row to update in PendingTickets.")

                else:
                    st.error("❌ Failed to send email. Please check your SMTP configuration.")

            st.success("✅ Your ticket has been submitted and processed successfully!")
