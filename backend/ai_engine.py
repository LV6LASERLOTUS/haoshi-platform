import json
import os
from pathlib import Path
from typing import Any

import httpx
import numpy as np
from paddleocr import PaddleOCR
from sentence_transformers import SentenceTransformer, util

ENV_PATH = Path(__file__).parent / ".env"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

# 1. 初始化本地中文 OCR（完全離線運行，支援繁體／簡體中文）
print("Loading PaddleOCR model...")
ocr = PaddleOCR(use_textline_orientation=True, lang="ch")

# 2. 初始化本地中文語意嵌入模型（約 95MB，於 CPU 上運行）
print("Loading BAAI/bge-small-zh-v1.5 model...")
embedding_model = SentenceTransformer("BAAI/bge-small-zh-v1.5")


def extract_text_from_image(image_path: str) -> str:
    """
    使用本地 PaddleOCR 從上傳的圖片檔中擷取中文文字。
    """
    if not os.path.exists(image_path):
        return ""

    result = ocr.predict(image_path)
    extracted_lines = []

    for res in result:
        rec_texts = res.get("rec_texts", [])
        rec_scores = res.get("rec_scores", [])
        for text, confidence in zip(rec_texts, rec_scores):
            if confidence > 0.6:  # 過濾低信心度的雜訊
                extracted_lines.append(text)

    return " ".join(extracted_lines)


def get_embedding(text: str) -> np.ndarray:
    """
    將中文文字字串轉換為語意向量嵌入。
    """
    # BGE 模型在查詢時搭配指令格式效果最佳，
    # 但對於簡短的描述性比對，直接編碼也能運作良好。
    return embedding_model.encode(text, normalize_embeddings=True)


def calculate_match_score(user_query: str, npo_focus_description: str) -> float:
    """
    計算使用者需求與 NPO 關注領域描述之間的餘弦相似度。
    回傳介於 0.0 到 1.0 之間的分數。
    """
    query_vector = get_embedding(user_query)
    npo_vector = get_embedding(npo_focus_description)

    # 計算餘弦相似度
    score = util.cos_sim(query_vector, npo_vector).item()
    return round(score, 4)


def _load_openai_api_key() -> str:
    """
    從環境變數或專案目錄下的 .env 檔案讀取 OpenAI API Key。
    支援 `OPENAI_API_KEY=sk-...` 格式以及單行直接存放 `sk-...` 的格式。
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if api_key:
        return api_key

    if ENV_PATH.exists():
        for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
            if line.startswith("sk-"):
                return line

    raise ValueError(
        "找不到 OpenAI API Key，請於環境變數設定 OPENAI_API_KEY 或寫入 .env 檔案。"
    )


def evaluate_and_summarize_ngos(
    top_5_ngos: str,
    google_data: str,
    feedback_skill: str,
    model: str = "gpt-4o-mini",
) -> dict[str, Any]:
    """
    綜合考量初步推薦的前 5 名 NGO、Google 試算表最新資料，以及由過往回饋建立的評估技巧（Skill），
    透過 OpenAI 模型重新評估並回傳最終前 5 名 NGO 推薦清單與 AI 決策摘要說明。

    參數:
        top_5_ngos: 初步篩選出的前 5 名 NGO 推薦內容（暫存字串）。
        google_data: 從 Google Sheets 取得的 NGO 現況與相關資料（暫存字串）。
        feedback_skill: 根據過往使用者回饋整理出的評估準則／Skill（暫存字串）。
        model: 使用的 OpenAI 模型名稱，預設為 "gpt-4o-mini"。

    回傳:
        dict: {
            "top_recommendations": [
                {
                    "rank": 1,
                    "npo_name": "...",
                    "match_score": 0.95,
                    "reason": "..."
                },
                ...
            ],
            "ai_summary": "AI 綜合評估與選擇背後的推論摘要..."
        }
    """
    api_key = _load_openai_api_key()

    system_prompt = (
        "你是一位專業的公益媒合顧問 AI。請根據提供的：\n"
        "1. 初步推薦的前 5 名 NGO 清單\n"
        "2. 來自 Google 試算表的各 NGO 最新資料與紀錄\n"
        "3. 根據過往使用者回饋所歸納出的媒合技巧與偏好（Skill）\n\n"
        "綜合評估並微調排序，挑選出最適合的前 5 名 NGO 推薦結果，並撰寫一段清晰的 AI 總結說明選擇背後的理由。\n"
        "請務必以 JSON 格式回傳，且包含以下兩個欄位：\n"
        '- "top_recommendations": 包含最多 5 個 NGO 推薦物件的陣列，每個物件包含 '
        '"rank" (int), "npo_name" (str), "match_score" (float, 0~1), "reason" (str)。\n'
        '- "ai_summary": 綜合考量後的推薦決策原因與整體摘要 (str，使用繁體中文)。'
    )

    user_prompt = (
        f"【初步前 5 名 NGO 推薦】\n{top_5_ngos}\n\n"
        f"【Google 試算表最新 NGO 資料】\n{google_data}\n\n"
        f"【過往回饋累積之評估技巧 (Skill)】\n{feedback_skill}"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }

    response = httpx.post(
        OPENAI_CHAT_URL,
        headers=headers,
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)

    return {
        "top_recommendations": parsed.get("top_recommendations", [])[:5],
        "ai_summary": parsed.get("ai_summary", ""),
    }


if __name__ == "__main__":
    sample_top_5_ngos = (
        "1. 彰化偏鄉數位教育協會 (初步分數: 0.92)\n"
        "2. 台灣綠能永續發展基金會 (初步分數: 0.85)\n"
        "3. 青年夢想協進會 (初步分數: 0.81)\n"
        "4. 中部兒少關懷協會 (初步分數: 0.78)\n"
        "5. 偏鄉閱讀推廣聯盟 (初步分數: 0.75)"
    )

    sample_google_data = (
        "- 彰化偏鄉數位教育協會：服務領域=偏鄉教育，地區=彰化縣，接觸次數=5，核實狀態=已驗證，顧問備註=配合度高、曾辦過多場科技營隊\n"
        "- 台灣綠能永續發展基金會：服務領域=環境教育，地區=台北市，接觸次數=2，核實狀態=已驗證，顧問備註=以北部校園講座為主\n"
        "- 青年夢想協進會：服務領域=青少年培力，地區=台中市，接觸次數=1，核實狀態=審核中，顧問備註=志工人力較吃緊\n"
        "- 中部兒少關懷協會：服務領域=兒少扶助，地區=南投縣，接觸次數=4，核實狀態=已驗證，顧問備註=近期積極尋找數位學習合作夥伴\n"
        "- 偏鄉閱讀推廣聯盟：服務領域=閱讀教育，地區=雲林縣，接觸次數=3，核實狀態=已驗證，顧問備註=深耕國小閱讀與伴讀"
    )

    sample_feedback_skill = (
        "1. 優先選擇「核實狀態=已驗證」且接觸次數較多、配合度穩定的組織。\n"
        "2. 若需求聚焦於中部偏鄉教育，應調升中部在地且具數位教育需求之 NGO 排名。\n"
        "3. 若志工人力吃緊或服務地區過遠，應酌情調降排名並於理由中提醒。"
    )

    print("正在呼叫 OpenAI 進行 NGO 綜合評估與摘要...")
    result = evaluate_and_summarize_ngos(
        top_5_ngos=sample_top_5_ngos,
        google_data=sample_google_data,
        feedback_skill=sample_feedback_skill,
    )

    print("\n=== 最終 Top 5 推薦清單 ===")
    for item in result["top_recommendations"]:
        print(
            f"第 {item.get('rank')} 名：{item.get('npo_name')} "
            f"(分數: {item.get('match_score')})\n"
            f"  理由：{item.get('reason')}"
        )

    print("\n=== AI 決策總結摘要 ===")
    print(result["ai_summary"])


