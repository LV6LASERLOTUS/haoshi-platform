import os

import gspread

# Define the scope for Google Sheets and Drive
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def load_npos_from_sheet():
    """
    Connects to Google Sheets via gspread and fetches all active NPO profiles.
    Expects a sheet named 'NPO_Database' with columns like: id, name, focus
    """
    credentials_path = "credentials.json"

    if not os.path.exists(credentials_path):
        print("Warning: credentials.json not found. Falling back to mock data.")
        return []

    try:
        # Authenticate using the service account key file
        client = gspread.service_account(filename="credentials.json")

        # Open your Google Sheet by its exact title
        sheet = client.open("好事大平台_Database").worksheet("NPO_Database")

        # Fetch all records as a list of dictionaries
        records = sheet.get_all_records()
        return records
    except ConnectionError as e:
        print(f"Error connecting to Google Sheets: {e}")
        return []
