import os

import gspread

# 定義 Google Sheets 與 Drive 的存取範圍
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def load_npos_from_sheet():
    """
    透過 gspread 連線至 Google Sheets，並取得所有有效的 NPO 資料。
    預期有一個名為 'NPO_Database' 的工作表，欄位包含：id, name, focus
    """
    credentials_path = "credentials.json"

    if not os.path.exists(credentials_path):
        print("Warning: credentials.json not found. Falling back to mock data.")
        return []

    try:
        # 使用服務帳戶金鑰檔進行驗證
        client = gspread.service_account(filename="credentials.json")

        # 依完整名稱開啟 Google 試算表
        sheet = client.open("好事大平台_Database").worksheet("NPO_Database")

        # 以字典清單的形式取得所有記錄
        records = sheet.get_all_records()
        return records
    except ConnectionError as e:
        print(f"Error connecting to Google Sheets: {e}")
        return []
