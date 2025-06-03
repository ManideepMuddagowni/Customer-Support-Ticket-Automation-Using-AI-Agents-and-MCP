import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
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
import datetime

load_dotenv()

# --------- Custom Styling ---------
st.markdown("""
<style>
div[data-testid="stSidebar"] > div:first-child {
    width: 350px;
    font-size: 20px;
}

.block-container {
    max-width: 1500px;
    padding: 2rem 2rem;
}

.centered-header {
    text-align: center;
    font-size: 3.4rem;
    font-weight: 800;
    color: #0f172a;
    margin-top: 1rem;
    margin-bottom: 2rem;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.ticket-box {
    background-color: #ffffff;
    border-left: 6px solid #3b82f6;
    padding: 1rem 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin-top: 1rem;
    margin-bottom: 1rem;
    font-size: 18px;
}

/* For Analyzed Tickets with Checkboxes */
.ticket-details {
    background-color: #f9fafb;
    border: 1px solid #ddd;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 1rem;
}
.ticket-header {
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 0.3rem;
}
.ticket-category {
    font-size: 0.9rem;
    color: #2563eb;
    margin-bottom: 0.6rem;
}
.ticket-message {
    white-space: pre-wrap;
    color: #374151;
}
.ticket-row {
    display: flex;
    align-items: flex-start;
    margin-bottom: 1rem;
}
.ticket-checkbox {
    width: 40px;
    margin-top: 40px;
    flex-shrink: 0;
}
.ticket-content {
    flex-grow: 1;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("📌 Navigation")
tab_selection = st.sidebar.radio("Go to:", ["📋 Pending Tickets", "📂 Analyzed Tickets", "📊 Dashboard"])

st.markdown("<div class='centered-header'>🤖 AI Support Ticket Management Dashboard</div>", unsafe_allow_html=True)

# Load tickets
pending_tickets = fetch_new_tickets()
processed_tickets = fetch_processed_tickets()

def format_ticket_label(ticket, idx):
    return f"#{idx} - {ticket['Name']} ({ticket['Email']})"

def filter_by_date_range(df, date_col, label):
    df = df.dropna(subset=[date_col])
    if df.empty:
        st.info(f"No valid {date_col} data available for {label}.")
        return df

    min_date = df[date_col].min().date()
    max_date = df[date_col].max().date()
    if min_date == max_date:
        max_date = min_date + datetime.timedelta(days=1)

    selected_date_range = st.date_input(
        f"Filter {label} by Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
    else:
        start_date = end_date = selected_date_range

    filtered_df = df[(df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)]
    return filtered_df

# --------- Pending Tickets ---------
if tab_selection == "📋 Pending Tickets":
    st.subheader("📋 Pending Tickets")

    if not pending_tickets:
        st.success("✅ No pending tickets to process.")
    else:
        # Classify unlabelled tickets
        for ticket in pending_tickets:
            if "IssueType_Label" not in ticket or not ticket["IssueType_Label"]:
                classification = classify_ticket(ticket["Message"])
                ticket["IssueType_Label"] = classification.get("issue_type", "Unknown")
                ticket["Sentiment"] = classification.get("sentiment", "Neutral")

        analyzed = [t for t in pending_tickets if t.get("IssueType_Label")]
        unanalyzed = [t for t in pending_tickets if not t.get("IssueType_Label")]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ⏳ Pending (Not Yet Analyzed)")
            if not unanalyzed:
                st.success("No tickets awaiting classification.")
            else:
                for i, ticket in enumerate(unanalyzed, start=1):
                    st.markdown(
                        f"<div class='ticket-box'><strong>📩 Ticket #{i}</strong><br>"
                        f"<strong>Name:</strong> {ticket['Name']}<br>"
                        f"<strong>Email:</strong> {ticket['Email']}<br>"
                        f"<strong>Message:</strong><br>{ticket['Message']}</div>", unsafe_allow_html=True
                    )

        with col2:
            st.markdown("### ✅ Analyzed (But Not Sent)")

            if not analyzed:
                st.info("No analyzed tickets available.")
            else:
                all_categories = sorted(set(t["IssueType_Label"] for t in analyzed))
                selected_categories = st.multiselect("🎯 Filter by Category", all_categories, default=all_categories)
                filtered = [t for t in analyzed if t["IssueType_Label"] in selected_categories]

                if not filtered:
                    st.info("No tickets match the selected categories.")
                else:
                    selected_to_send = {}

                    for i, ticket in enumerate(filtered, start=1):
                        cols = st.columns([0.05, 0.95])
                        with cols[0]:
                            selected_to_send[i] = st.checkbox("", key=f"send_ticket_{i}")
                        with cols[1]:
                            st.markdown(
                                f"<div class='ticket-details'>"
                                f"<div class='ticket-header'>📨 Ticket #{i} - {ticket['Name']} ({ticket['Email']})</div>"
                                f"<div class='ticket-category'>Category: {ticket['IssueType_Label']}</div>"
                                f"<div class='ticket-message'>{ticket['Message']}</div>"
                                f"</div>", unsafe_allow_html=True
                            )

                    col_btn1, col_btn2 = st.columns([1, 1])
                    with col_btn1:
                        if st.button("✉️ Send Replies to Selected"):
                            to_process = [ticket for i, ticket in enumerate(filtered, start=1) if selected_to_send.get(i)]
                            if not to_process:
                                st.warning("Please select at least one ticket to send replies.")
                            else:
                                for ticket in to_process:
                                    if not ticket.get("AutoReply"):
                                        ticket["AutoReply"] = generate_reply(ticket["Name"], ticket["Message"])

                                    sentiment = ticket.get("Sentiment", "Neutral")
                                    issue_type = ticket.get("IssueType_Label", "Unknown")
                                    reply = ticket["AutoReply"]
                                    row_number = ticket.get("RowNumber")

                                    send_email_smtp(ticket["Email"], "Automated Reply", reply)

                                    update_ticket(row_number, sentiment, issue_type, reply)
                                    append_processed_ticket(ticket, sentiment, issue_type, reply)
                                    delete_ticket_from_pending(row_number)

                                st.success(f"Sent replies to {len(to_process)} tickets and updated the records.")

                    with col_btn2:
                        if st.button("✉️ Send Replies to All"):
                            for ticket in filtered:
                                if not ticket.get("AutoReply"):
                                    ticket["AutoReply"] = generate_reply(ticket["Name"], ticket["Message"])

                                sentiment = ticket.get("Sentiment", "Neutral")
                                issue_type = ticket.get("IssueType_Label", "Unknown")
                                reply = ticket["AutoReply"]
                                row_number = ticket.get("RowNumber")

                                send_email_smtp(ticket["Email"], "Automated Reply", reply)

                                update_ticket(row_number, sentiment, issue_type, reply)
                                append_processed_ticket(ticket, sentiment, issue_type, reply)
                                delete_ticket_from_pending(row_number)

                            st.success(f"Sent replies to all ({len(filtered)}) analyzed tickets and updated the records.")

# --------- Analyzed Tickets ---------
elif tab_selection == "📂 Analyzed Tickets":
    if not processed_tickets:
        st.info("No tickets have been analyzed yet.")
    else:
        df = pd.DataFrame(processed_tickets)
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')

        issue_types = df["IssueType_Label"].dropna().unique().tolist()
        selected_issue_types = st.multiselect("Filter by Issue Type", options=issue_types, default=issue_types)

        if 'Timestamp' in df.columns and not df['Timestamp'].isnull().all():
            df = filter_by_date_range(df, 'Timestamp', 'Analyzed Tickets')

        df = df[df["IssueType_Label"].isin(selected_issue_types)]

        if df.empty:
            st.info("No tickets match the selected filters.")
        else:
            filtered_tickets = df.to_dict('records')
            processed_labels = [format_ticket_label(t, i) for i, t in enumerate(filtered_tickets, start=1)]
            selected_processed = st.selectbox("Select an analyzed ticket", processed_labels, key="processed_select_filtered")
            selected_index = processed_labels.index(selected_processed)
            ticket = filtered_tickets[selected_index]

            st.markdown(f"<div class='ticket-box'><strong>📝 Message:</strong><br>{ticket['Message']}</div>", unsafe_allow_html=True)
            st.markdown(f"**Sentiment:** `{ticket.get('Sentiment', '')}`")
            st.markdown(f"**Issue Type:** `{ticket.get('IssueType_Label', '')}`")
            st.markdown("**📬 Reply Sent:**")
            st.text_area("Reply", ticket.get("AutoReply", ""), height=140, disabled=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📁 Export Filtered CSV", csv, "processed_tickets_filtered.csv", "text/csv")

# --------- Dashboard ---------
elif tab_selection == "📊 Dashboard":
    if not processed_tickets:
        st.info("No data to display yet.")
    else:
        df = pd.DataFrame(processed_tickets)
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')

        issue_types = df["IssueType_Label"].dropna().unique().tolist()
        selected_issue_types = st.multiselect("Filter Dashboard by Issue Type", options=issue_types, default=issue_types)

        if 'Timestamp' in df.columns and not df['Timestamp'].isnull().all():
            df = filter_by_date_range(df, 'Timestamp', 'Dashboard')

        df = df[df["IssueType_Label"].isin(selected_issue_types)]

        if df.empty:
            st.info("No data to display for the selected filters.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 Sentiment Distribution")
                sentiment_counts = df["Sentiment"].value_counts(dropna=True)
                if sentiment_counts.empty:
                    st.write("No sentiment data available.")
                else:
                    fig1, ax1 = plt.subplots()
                    ax1.pie(sentiment_counts, labels=sentiment_counts.index, autopct="%1.1f%%", startangle=140)
                    ax1.axis("equal")
                    st.pyplot(fig1)

            with col2:
                st.subheader("🗂️ Issue Type Distribution")
                issue_counts = df["IssueType_Label"].value_counts(dropna=True)
                if issue_counts.empty:
                    st.write("No issue type data available.")
                else:
                    fig2, ax2 = plt.subplots()
                    ax2.bar(issue_counts.index, issue_counts.values, color="#3b82f6")
                    ax2.set_ylabel("Count")
                    ax2.set_xlabel("Issue Type")
                    ax2.set_xticklabels(issue_counts.index, rotation=30, ha="right")
                    st.pyplot(fig2)
