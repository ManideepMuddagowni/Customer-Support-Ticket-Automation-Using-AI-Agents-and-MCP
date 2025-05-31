import streamlit as st
from tools.sheet_connector import (
    fetch_new_tickets,
    update_ticket,
    append_processed_ticket,
    delete_ticket_from_pending,
    fetch_processed_tickets
)
from tools.classify_ticket import classify_ticket
from tools.generate_reply import generate_reply
from tools.gmail_sender import send_email_smtp
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Ticket Manager", layout="centered")
st.title("📨 AI Customer Support Ticket Manager")
st.caption("Analyze, classify, respond, and track customer support tickets — powered by AI & Gmail.")

pending_tickets = fetch_new_tickets()
processed_tickets = fetch_processed_tickets()

def format_ticket_label(ticket, idx):
    # Format dropdown option label with idx, name, and email
    return f"#{idx} - {ticket['Name']} ({ticket['Email']})"

# Pending Tickets Section
st.header("📋 Pending Tickets")

if not pending_tickets:
    st.success("✅ No pending tickets to process.")
else:
    pending_labels = [format_ticket_label(t, i) for i, t in enumerate(pending_tickets, start=1)]
    selected_pending = st.selectbox("Select a pending ticket", pending_labels, key="pending_select")
    selected_index = pending_labels.index(selected_pending)
    ticket = pending_tickets[selected_index]

    st.markdown("**📝 Message:**")
    st.info(ticket["Message"])

    if st.button("🔍 Analyze & Respond", key=f"analyze_{ticket.get('RowNumber', selected_index)}"):
        with st.spinner("🤖 Analyzing ticket and sending email..."):
            classification = classify_ticket(ticket["Message"])
            reply = generate_reply(name=ticket["Name"], text=ticket["Message"])

            update_ticket(
                row_number=ticket["RowNumber"],
                sentiment=classification["sentiment"],
                issue_type=classification["issue_type"],
                reply=reply
            )

            email_status = send_email_smtp(
                to=ticket['Email'],
                subject="Regarding Your Support Ticket",
                body=reply
            )

            if email_status.get("status") == "success":
                append_processed_ticket(
                    ticket=ticket,
                    sentiment=classification["sentiment"],
                    issue_type=classification["issue_type"],
                    reply=reply
                )
                delete_ticket_from_pending(ticket["RowNumber"])
                st.success("✅ Ticket analyzed and email sent successfully! Moved to Processed Tickets.")
            else:
                st.error(f"❌ Failed to send email: {email_status.get('message')}")

# Processed Tickets Section
st.header("📂 Analyzed Tickets")

if not processed_tickets:
    st.info("No tickets have been analyzed yet.")
else:
    processed_labels = [format_ticket_label(t, i) for i, t in enumerate(processed_tickets, start=1)]
    selected_processed = st.selectbox("Select an analyzed ticket", processed_labels, key="processed_select")
    selected_index = processed_labels.index(selected_processed)
    ticket = processed_tickets[selected_index]

    st.markdown("**📝 Message:**")
    st.info(ticket["Message"])
    st.markdown(f"**Sentiment:** `{ticket.get('Sentiment', '')}`")
    st.markdown(f"**Issue Type:** `{ticket.get('IssueType_Label', '')}`")
    st.markdown("**📬 Reply Sent:**")
    st.text_area(
        "Reply",
        ticket.get("AutoReply", ""),
        height=140,
        disabled=True,
        key=f"reply_{ticket.get('Name','')}_{ticket.get('Email','')}_{selected_index}"
    )
