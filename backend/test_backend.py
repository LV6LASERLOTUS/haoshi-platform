from ai_engine import calculate_match_score
from fastapi.testclient import TestClient
from main import app

# Initialize the FastAPI TestClient
client = TestClient(app)


def test_root_endpoint():
    """Test the health-check root route."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "message": "好事大平台 API server is running successfully!",
    }


def test_ai_match_logic():
    """Test the semantic matching calculation function directly."""
    query = "我們需要偏鄉教育與數位學習支援"
    npo_desc = "長期深耕中部偏鄉，為小學童舉辦程式設計營隊與科技教育課程。"

    score = calculate_match_score(query, npo_desc)

    # Assert that score is a float between 0.0 and 1.0
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    # Given the semantic overlap, it should score reasonably high
    assert score > 0.4


def test_match_endpoint_text_only():
    """Test the POST /api/v1/match endpoint with text payload only."""
    response = client.post(
        "/api/v1/match", data={"request_text": "尋找偏鄉兒童教育資源"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["status"] == "success"
    assert "processed_query" in data
    assert "top_matches" in data
    assert len(data["top_matches"]) > 0

    # Check if the top match structure contains expected fields
    top_match = data["top_matches"][0]
    assert "npo_name" in top_match
    assert "match_score" in top_match
    assert "reason" in top_match
