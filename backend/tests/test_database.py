from database import CREDENTIALS_PATH, load_npos_from_sheets


def test_credentials_exist():
    """確認是否存在 credentials.json 檔案。"""
    assert CREDENTIALS_PATH.exists(), f"找不到憑證檔案：{CREDENTIALS_PATH}"


def test_load_npos_from_sheets_returns_data():
    """確認 load_npos_from_sheets() 能正常連線並回傳資料。"""
    result = load_npos_from_sheets()
    assert result is not None
    assert len(result) > 0
