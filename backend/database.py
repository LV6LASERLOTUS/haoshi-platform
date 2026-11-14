from pathlib import Path

import gspread
from gspread import Client, Spreadsheet, Worksheet

CREDENTIALS_PATH: Path = Path(__file__).parent / "config" / "credentials.json"

# TODO: 待建立實際的回饋 Google 試算表／工作表後，替換以下網址或工作表名稱
FEEDBACK_SHEET_URL: str = "https://docs.google.com/spreadsheets/d/1Ehx7HHmbmxGbMeuw0WK76jdjGs3_3gsFerduEv5b5aI/edit?gid=2132473483#gid=2132473483"
FEEDBACK_WORKSHEET_NAME: str = "feedback_mock"


def load_npos_from_sheet() -> dict[str, Worksheet]:
    """
    透過 gspread 連線至 Google Sheets，並取得所有工作表。
    回傳字典：key 為工作表名稱 (sheet name)，value 為 gspread Worksheet 物件。
    """
    if not CREDENTIALS_PATH.exists():
        print("Warning: credentials.json not found. Falling back to mock data.")
        return {}

    try:
        # 使用服務帳戶金鑰檔進行驗證
        client: Client = gspread.service_account(filename=CREDENTIALS_PATH)

        # 依完整名稱開啟 Google 試算表
        spreadsheet: Spreadsheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/1Ehx7HHmbmxGbMeuw0WK76jdjGs3_3gsFerduEv5b5aI/edit?gid=2132473483#gid=2132473483"
        )

        records: dict[str, Worksheet] = {
            sheet.title: sheet for sheet in spreadsheet.worksheets()
        }
        return records
    except ConnectionError as e:
        print(f"Error connecting to Google Sheets: {e}")
        return {}


# 提供 load_npos_from_sheets 別名
load_npos_from_sheets = load_npos_from_sheet



def save_feedback_to_sheet(feedback_data: dict) -> bool:
    """
    將使用者回饋寫入 Google Sheets 指定工作表。
    目前使用暫定的 mock 工作表名稱（FEEDBACK_WORKSHEET_NAME），
    待實際工作表建立後即可直接寫入。
    """
    if not CREDENTIALS_PATH.exists():
        print("Warning: credentials.json not found. Skipping Google Sheets write.")
        return False

    try:
        client: Client = gspread.service_account(filename=CREDENTIALS_PATH)
        spreadsheet: Spreadsheet = client.open_by_url(FEEDBACK_SHEET_URL)
        worksheet: Worksheet = spreadsheet.worksheet(FEEDBACK_WORKSHEET_NAME)
        row = [
            feedback_data.get("question_id", ""),
            feedback_data.get("question_text", ""),
            feedback_data.get("ai_summary", ""),
            feedback_data.get("rating", ""),
            feedback_data.get("feedback_type", ""),
            feedback_data.get("feedback_content", ""),
        ]
        worksheet.append_row(row)
        return True
    except (gspread.exceptions.GSpreadException, ConnectionError) as e:
        print(
            f"Warning: Could not write feedback to sheet '{FEEDBACK_WORKSHEET_NAME}': {e}"
        )
        return False
