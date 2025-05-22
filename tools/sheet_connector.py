import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sys
sys.stdout.reconfigure(encoding='utf-8')
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_cred.json", scope)
client = gspread.authorize(creds)

# Make sure your google sheet name is matching with the below name
sheet = client.open("SupportTickets").sheet1

def fetch_new_tickets():
    data = sheet.get_all_records()
    return [row for row in data if row['Sentiment'] == "" or row['AutoReply'] == ""]

def append_ticket_to_sheet(name, email, issue_type, message):
    sheet.append_row([name, email, issue_type, message, "", "", ""])

def update_ticket(row_number, sentiment, issue_type, reply):
    try:
        sheet.update_cell(row_number, 5, sentiment)     # Sentiment → E
        sheet.update_cell(row_number, 6, issue_type)    # IssueType_Label → F
        sheet.update_cell(row_number, 7, reply)         # AutoReply → G
        print(f"✅ Updated Row {row_number}")
    except Exception as e:
        print(f"❌ Error updating row {row_number}: {e}")

def append_processed_ticket(ticket, sentiment, issue_type, reply):
    try:
        workbook = client.open("SupportTickets")
        sheet = workbook.worksheet("ProcessedTickets")  # Make sure this tab exists
    except gspread.exceptions.WorksheetNotFound:
        sheet = workbook.add_worksheet(title="ProcessedTickets", rows="1000", cols="10")
        sheet.append_row(["Name", "Email", "IssueType", "Message", "Sentiment", "IssueType_Label", "AutoReply"])

    sheet.append_row([
        ticket["Name"],
        ticket["Email"],
        ticket["IssueType"],
        ticket["Message"],
        sentiment,
        issue_type,
        reply
    ])
