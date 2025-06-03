import streamlit as st
from datetime import datetime
from tools.sheet_connector import get_pending_sheet

# ------------------- PAGE CONFIG -------------------
st.set_page_config(
    page_title="📩 Submit a Support Ticket",
    page_icon="📩",
    layout="centered",
    initial_sidebar_state="auto"
)

# ------------------- CUSTOM CSS -------------------
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 8px;
        border: none;
    }
    .stTextInput, .stTextArea, .stSelectbox {
        background-color: #ffffff !important;
        border-radius: 8px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------- PAGE TITLE -------------------
st.title("📩 Submit a Support Ticket")
st.markdown("Please fill out the form below, and our support team will get back to you soon.")

# ------------------- FORM -------------------
def append_ticket_to_pending(name, email, issue_type, message):
    sheet = get_pending_sheet()
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Append with placeholders for Sentiment, IssueType, Reply
        sheet.append_row([timestamp, name, email, issue_type, message, "", "", ""])
        return True
    except Exception as e:
        st.error(f"Failed to append ticket to PendingTickets: {e}")
        return False

with st.form("ticket_form"):
    st.subheader("📄 Ticket Information")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", placeholder="e.g., Mani deep")
    with col2:
        email = st.text_input("Email Address", placeholder="e.g., mani@example.com")

    issue_type = st.selectbox(
        "Select Issue Type",
        ["Billing", "Technical", "Login Issue", "Other"]
    )
    message = st.text_area("Describe your issue in detail", height=200, placeholder="Please describe your issue...")

    submitted = st.form_submit_button("📨 Submit Ticket")

    if submitted:
        if not name.strip() or not email.strip() or not message.strip():
            st.error("⚠️ Please fill in all required fields.")
        else:
            success = append_ticket_to_pending(name.strip(), email.strip(), issue_type, message.strip())
            if success:
                st.success("✅ Your ticket has been submitted successfully!")
