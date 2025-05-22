import streamlit as st
from tools.sheet_connector import append_ticket_to_sheet

st.set_page_config(page_title="Submit a Support Ticket", page_icon="📩")

st.title("📩 Submit a Support Ticket")
st.markdown("We'll get back to you shortly with a helpful response.")

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
            append_ticket_to_sheet(name, email, issue_type, message)
            st.success("✅ Your ticket has been submitted successfully!")
