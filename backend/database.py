from pathlib import Path

import gspread
from gspread import Client, Spreadsheet, Worksheet

CREDENTIALS_PATH: Path = Path(__file__).parent / "config" / "credentials.json"


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
