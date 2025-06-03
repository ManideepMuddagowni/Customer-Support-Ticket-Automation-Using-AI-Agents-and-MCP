import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Google Sheets API setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_cred.json", scope)
gs_client = gspread.authorize(creds)

# Constants
SPREADSHEET_NAME = "SupportTickets"
PENDING_SHEET_NAME = "PendingTickets"
PROCESSED_SHEET_NAME = "ProcessedTickets"

def get_pending_sheet():
    workbook = gs_client.open(SPREADSHEET_NAME)
    try:
        sheet = workbook.worksheet(PENDING_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        # Create worksheet and set header row
        sheet = workbook.add_worksheet(title=PENDING_SHEET_NAME, rows="1000", cols="10")
        sheet.append_row(["timestamp","Name", "Email", "IssueType", "Message", "Sentiment", "IssueType_Label", "AutoReply"])
    return sheet

def get_processed_sheet():
    workbook = gs_client.open(SPREADSHEET_NAME)
    try:
        sheet = workbook.worksheet(PROCESSED_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        sheet = workbook.add_worksheet(title=PROCESSED_SHEET_NAME, rows="1000", cols="10")
        sheet.append_row(["timestamp","Name", "Email", "IssueType", "Message", "Sentiment", "IssueType_Label", "AutoReply"])
    return sheet

def fetch_new_tickets():
    """
    Fetch tickets from PendingTickets sheet that have empty Sentiment or AutoReply (i.e., pending processing).
    Returns a list of dicts, each with 'RowNumber' added for sheet operations.
    """
    sheet = get_pending_sheet()
    data = sheet.get_all_records()
    tickets = []
    for idx, row in enumerate(data, start=2):  # Skip header (row 1)
        if not row.get('Sentiment') or not row.get('AutoReply'):
            row['RowNumber'] = idx
            tickets.append(row)
    return tickets

def update_ticket(row_number, sentiment, issue_type, reply):
    """
    Update a ticket row in PendingTickets sheet with sentiment, issue_type_label, and reply.
    Column indices based on header:
      timestamp=1, Name=2, Email=3, IssueType=4, Message=5,
      Sentiment=6, IssueType_Label=7, AutoReply=8
    """
    sheet = get_pending_sheet()
    try:
        sheet.update_cell(row_number, 6, sentiment)       # Sentiment (F)
        sheet.update_cell(row_number, 7, issue_type)      # IssueType_Label (G)
        sheet.update_cell(row_number, 8, reply)           # AutoReply (H)
        print(f"✅ Updated Row {row_number} in PendingTickets")
    except Exception as e:
        print(f"❌ Error updating row {row_number} in PendingTickets: {e}")

def append_processed_ticket(ticket, sentiment, issue_type, reply):
    """
    Append the processed ticket to ProcessedTickets sheet with timestamp.
    Columns same as PendingTickets with timestamp added.
    """
    sheet = get_processed_sheet()
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([
            timestamp,
            ticket.get("Name", ""),
            ticket.get("Email", ""),
            ticket.get("IssueType", issue_type),
            ticket.get("Message", ""),
            sentiment,
            issue_type,
            reply
        ])
        print("✅ Appended ticket to ProcessedTickets")
    except Exception as e:
        print(f"❌ Failed to append ticket to ProcessedTickets: {e}")

def delete_ticket_from_pending(row_number):
    """
    Delete a ticket row from PendingTickets sheet.
    """
    sheet = get_pending_sheet()
    try:
        sheet.delete_rows(row_number)
        print(f"✅ Deleted Row {row_number} from PendingTickets")
    except Exception as e:
        print(f"❌ Error deleting row {row_number} from PendingTickets: {e}")

def fetch_processed_tickets():
    """
    Fetch all processed tickets from ProcessedTickets sheet.
    Returns list of dicts.
    """
    sheet = get_processed_sheet()
    try:
        return sheet.get_all_records()
    except Exception as e:
        print(f"❌ Error fetching processed tickets: {e}")
        return []
