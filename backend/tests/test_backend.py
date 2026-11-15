import json

from fastapi.testclient import TestClient

from ai_engine import calculate_match_score, evaluate_and_summarize_ngos
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


def test_feedback_endpoint(monkeypatch):
    """測試 POST /api/v1/feedback 端點。"""
    monkeypatch.setattr("main.save_feedback_to_sheet", lambda payload: True)

    payload = {
        "question_id": "Q-20261113-0042",
        "question_text": "尋找偏鄉兒童教育資源",
        "ai_summary": "過去已舉辦 5 次偏鄉科技營隊，與您的需求領域高度契合。",
        "rating": 5,
        "feedback_type": "推薦符合需求",
        "feedback_content": "推薦結果非常符合我們的需求！",
    }

    response = client.post("/api/v1/feedback", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["saved_to_sheet"] is True
    assert data["feedback"] == payload


def test_evaluate_and_summarize_ngos(monkeypatch):
    """測試綜合評估前 5 名 NGO 並產生 AI 摘要的函式。"""
    mock_llm_output = {
        "top_recommendations": [
            {
                "rank": 1,
                "npo_name": "彰化偏鄉數位教育協會",
                "match_score": 0.95,
                "reason": "深耕中部偏鄉且過往合作紀錄良好。",
            },
            {
                "rank": 2,
                "npo_name": "台灣綠能永續發展基金會",
                "match_score": 0.85,
                "reason": "具備豐富校園講座經驗。",
            },
        ],
        "ai_summary": "綜合 Google 試算表最新接觸紀錄與過往回饋偏好，優先推薦在地執行力強且互動率高的組織。",
    }

    class DummyResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {"message": {"content": json.dumps(mock_llm_output)}}
                ]
            }

    monkeypatch.setattr("ai_engine._load_openai_api_key", lambda: "sk-test-key")
    monkeypatch.setattr(
        "ai_engine.httpx.post", lambda *args, **kwargs: DummyResponse()
    )

    result = evaluate_and_summarize_ngos(
        top_5_ngos="1. 彰化偏鄉數位教育協會 2. 台灣綠能永續發展基金會",
        google_data="彰化偏鄉數位教育協會：近期接觸 5 次，核實狀態通過",
        feedback_skill="優先推薦核實通過且近期有實際活動紀錄的在地 NGO",
    )

    assert "top_recommendations" in result
    assert "ai_summary" in result
    assert len(result["top_recommendations"]) == 2
    assert result["top_recommendations"][0]["npo_name"] == "彰化偏鄉數位教育協會"
    assert "綜合 Google 試算表" in result["ai_summary"]


