import time
from pathlib import Path

import gspread
from gspread import Client, Spreadsheet, Worksheet

CREDENTIALS_PATH: Path = Path(__file__).parent / "config" / "credentials.json"

# TODO: 待建立實際的回饋 Google 試算表／工作表後，替換以下網址或工作表名稱
FEEDBACK_SHEET_URL: str = "https://docs.google.com/spreadsheets/d/1Ehx7HHmbmxGbMeuw0WK76jdjGs3_3gsFerduEv5b5aI/edit?gid=2132473483#gid=2132473483"
FEEDBACK_WORKSHEET_NAME: str = "NPO_feedback"


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


def query_ngo(ngo_name: str) -> dict:
    """傳送 NGO 名稱至 NGO_Search的B2，並取回試算表計算後的相關資料"""
    print(f"正在查詢 NGO：{ngo_name}...")
    client: Client = gspread.service_account(filename=CREDENTIALS_PATH)
    spreadsheet: Spreadsheet = client.open_by_url(FEEDBACK_SHEET_URL)
    worksheet: Worksheet = spreadsheet.worksheet("NGO_search")
    worksheet.update([[ngo_name]], "B2")

    # 短暫暫停 0.5 ~ 1 秒，確保雲端公式重新計算完成
    time.sleep(1)

    # 批次讀取 B2 至 B22 的最新數值
    result_values = worksheet.get("B2:B22")

    # NGO_Search 結果的欄位row號
    mapping = {
        "ngo_name": 2,
        "organization_id": 3,
        "service_domain": 4,
        "region": 5,
        "contact_count": 6,
        "latest_contact_date": 7,
        "consultant_notes": 9,
        "cooperation_hint": 10,
        "verification_status": 11,
        "ngo_overview": 15,
        "contact_history_summary": 18,
        "ai_analysis_input": 20,
        "ai_analysis_output": 22,
    }

    data = {}
    for key, row_num in mapping.items():
        idx = row_num - 2
        # 避免因空白列產生長度不足的問題，安全讀取輔助函式
        if idx < len(result_values) and result_values[idx]:
            data[key] = result_values[idx][0]
        else:
            data[key] = ""

    return data


if __name__ == "__main__":
    records = load_npos_from_sheet()
    for record in records:
        print(record)
#     target_ngo = "共好行動組織01"
#     result = query_ngo(target_ngo)

#     print("\n--- 查詢結果 ---")
#     print(f"組織 ID: {result['organization_id']}")
#     print(f"服務領域: {result['service_domain']}")
#     print(f"接觸次數: {result['contact_count']}")
#     print(f"\nAI 分析輸出：\n{result['ai_analysis_output']}")
