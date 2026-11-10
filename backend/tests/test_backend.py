from fastapi.testclient import TestClient

from ai_engine import calculate_match_score
from main import app

# 初始化 FastAPI TestClient
client = TestClient(app)


def test_root_endpoint():
    """測試健康檢查的根路由。"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "message": "好事大平台 API server is running successfully!",
    }


def test_ai_match_logic():
    """直接測試語意匹配計算函式。"""
    query = "我們需要偏鄉教育與數位學習支援"
    npo_desc = "長期深耕中部偏鄉，為小學童舉辦程式設計營隊與科技教育課程。"

    score = calculate_match_score(query, npo_desc)

    # 斷言分數為介於 0.0 到 1.0 之間的浮點數
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    # 由於語意高度重疊，分數應相當高
    assert score > 0.4


def test_match_endpoint_text_only():
    """測試僅帶文字內容的 POST /api/v1/match 端點。"""
    response = client.post(
        "/api/v1/match", data={"request_text": "尋找偏鄉兒童教育資源"}
    )

    assert response.status_code == 200
    data = response.json()

    # 驗證回應結構
    assert data["status"] == "success"
    assert "processed_query" in data
    assert "top_matches" in data
    assert len(data["top_matches"]) > 0

    # 檢查最佳匹配結果是否包含預期欄位
    top_match = data["top_matches"][0]
    assert "npo_name" in top_match
    assert "match_score" in top_match
    assert "reason" in top_match
