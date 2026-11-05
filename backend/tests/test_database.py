from unittest.mock import MagicMock, patch

from database import load_npos_from_sheet


def test_returns_empty_list_when_no_credentials(tmp_path, monkeypatch):
    """沒有 credentials.json → 回傳 [] 且不會崩潰。"""
    monkeypatch.chdir(tmp_path)  # 空目錄，沒有 credentials.json
    result = load_npos_from_sheet()
    assert result == []


def test_returns_records_on_success():
    """正常流程：gspread 回傳資料列 → 函式原樣回傳。"""
    fake_records = [
        {"id": 1, "name": "測試NPO", "focus": "教育"},
        {"id": 2, "name": "另一NPO", "focus": "環保"},
    ]
    with patch("database.gspread.service_account") as mock_sa:
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_sa.return_value = mock_client
        mock_client.open.return_value.worksheet.return_value = mock_sheet
        mock_sheet.get_all_records.return_value = fake_records

        with patch("database.os.path.exists", return_value=True):
            result = load_npos_from_sheet()

    assert result == fake_records


def test_returns_empty_list_on_gspread_error():
    """若 gspread 拋出任何例外 → 優雅地回傳 []。"""
    with patch("database.gspread.service_account") as mock_sa:
        mock_sa.side_effect = Exception("API quota exceeded")

        with patch("database.os.path.exists", return_value=True):
            result = load_npos_from_sheet()

    assert result == []
