import streamlit as st
from tools.sheet_connector import (
    fetch_new_tickets,
    update_ticket,
    append_processed_ticket
)
from tools.classify_ticket import classify_ticket
from tools.generate_reply import generate_reply
from tools.gmail_sender import send_email_smtp
from dotenv import load_dotenv

# ---------- Load environment variables ----------
load_dotenv()

# ---------- Streamlit page setup ----------
st.set_page_config(page_title="AI Ticket Manager", layout="centered")

# ---------- App Header ----------
st.title("📨 AI Customer Support Ticket Manager")
st.caption("Analyze, classify, respond, and track customer support tickets — powered by AI & Gmail.")

# ---------- Fetch New Tickets ----------
tickets = fetch_new_tickets()

if not tickets:
    st.success("✅ No new tickets to process.")
else:
    for i, ticket in enumerate(tickets, start=1):
        
        # Skip already processed tickets
        if ticket["Sentiment"] and ticket["AutoReply"]:
            continue

        with st.expander(f"📩 Ticket #{i} from {ticket['Name']} ({ticket['Email']})"):
            st.markdown("**📝 Message:**")
            st.info(ticket["Message"])

            if st.button(f"🔍 Analyze & Respond Ticket #{i}"):
                with st.spinner("🤖 Running AI classification and reply generation..."):
                    classification = classify_ticket(ticket["Message"])
                    reply = generate_reply(ticket["Message"])

                st.success("✅ AI Analysis Complete")
                st.markdown(f"**Sentiment:** `{classification['sentiment']}`")
                st.markdown(f"**Issue Type:** `{classification['issue_type']}`")
                st.markdown("**📬 Suggested Reply:**")
                st.text_area("Auto-Generated Reply", reply, height=140)

                # Save to primary sheet
                update_ticket(
                    row_number=i + 1,
                    sentiment=classification["sentiment"],
                    issue_type=classification["issue_type"],
                    reply=reply
                )

                # Save to 'ProcessedTickets' tab
                append_processed_ticket(
                    ticket=ticket,
                    sentiment=classification["sentiment"],
                    issue_type=classification["issue_type"],
                    reply=reply
                )

                # Auto-send email
                with st.spinner("📤 Sending email reply..."):
                    success = send_email_smtp(
                        to=ticket['Email'],
                        subject="Regarding Your Support Ticket",
                        body=reply
                    )

                if success:
                    st.success("📬 Email sent successfully!")
                else:
                    st.error("❌ Failed to send email. Check SMTP/app password setup.")

                st.info("📝 Ticket updated, logged, and customer notified.")
