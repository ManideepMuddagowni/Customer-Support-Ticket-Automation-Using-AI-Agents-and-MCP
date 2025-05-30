import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set up Google Sheets API client
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_cred.json", scope)
gs_client = gspread.authorize(creds)

# Open your main spreadsheet by name
SPREADSHEET_NAME = "SupportTickets"
PENDING_SHEET_NAME = "PendingTickets"
PROCESSED_SHEET_NAME = "ProcessedTickets"

def get_pending_sheet():
    workbook = gs_client.open(SPREADSHEET_NAME)
    try:
        sheet = workbook.worksheet(PENDING_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        sheet = workbook.add_worksheet(title=PENDING_SHEET_NAME, rows="1000", cols="10")
        # Set header row
        sheet.append_row(["Name", "Email", "IssueType", "Message", "Sentiment", "IssueType_Label", "AutoReply"])
    return sheet

def get_processed_sheet():
    workbook = gs_client.open(SPREADSHEET_NAME)
    try:
        sheet = workbook.worksheet(PROCESSED_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        sheet = workbook.add_worksheet(title=PROCESSED_SHEET_NAME, rows="1000", cols="10")
        # Set header row
        sheet.append_row(["Name", "Email", "IssueType", "Message", "Sentiment", "IssueType_Label", "AutoReply"])
    return sheet

def fetch_new_tickets():
    """Fetch tickets from PendingTickets sheet that are not yet analyzed."""
    sheet = get_pending_sheet()
    data = sheet.get_all_records()
    tickets = []
    for i, row in enumerate(data, start=2):  # rows start at 2 because of header
        # Consider tickets with empty Sentiment or AutoReply as pending
        if not row.get('Sentiment') or not row.get('AutoReply'):
            row['RowNumber'] = i
            tickets.append(row)
    return tickets

def update_ticket(row_number, sentiment, issue_type, reply):
    """Update the ticket row in PendingTickets sheet after analysis and reply generation."""
    sheet = get_pending_sheet()
    try:
        # Columns indexes based on header:
        # Sentiment = 5 (E), IssueType_Label = 6 (F), AutoReply = 7 (G)
        sheet.update_cell(row_number, 5, sentiment)     # E
        sheet.update_cell(row_number, 6, issue_type)    # F
        sheet.update_cell(row_number, 7, reply)         # G
        print(f"✅ Updated Row {row_number} in PendingTickets")
    except Exception as e:
        print(f"❌ Error updating row {row_number} in PendingTickets: {e}")

def append_processed_ticket(ticket, sentiment, issue_type, reply):
    """Append the processed ticket to ProcessedTickets sheet."""
    sheet = get_processed_sheet()
    try:
        sheet.append_row([
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
    """Delete a ticket from PendingTickets sheet by row number."""
    sheet = get_pending_sheet()
    try:
        sheet.delete_rows(row_number)
        print(f"✅ Deleted Row {row_number} from PendingTickets")
    except Exception as e:
        print(f"❌ Error deleting row {row_number} from PendingTickets: {e}")

def fetch_processed_tickets():
    """Fetch all processed tickets from ProcessedTickets sheet."""
    sheet = get_processed_sheet()
    try:
        data = sheet.get_all_records()
        return data
    except Exception as e:
        print(f"❌ Error fetching processed tickets: {e}")
        return []
