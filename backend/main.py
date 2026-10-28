import os
import shutil
from typing import Optional

from ai_engine import calculate_match_score, extract_text_from_image
from fastapi import FastAPI, File, Form, UploadFile

UPLOAD_DIR = "uploads"

app = FastAPI(
    title="好事大平台 API",
    description="Backend server for handling mobile intake and matching requests.",
    version="1.0.0",
)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "好事大平台 API server is running successfully!",
    }


@app.post("/api/v1/match")
async def handle_match_request(
    request_text: str = Form(...), uploaded_file: Optional[UploadFile] = File(None)
):
    final_query_text = request_text
    file_name = "No file uploaded"

    # 1. OCR Processing if file attached
    if uploaded_file:
        file_name = uploaded_file.filename
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

        ocr_text = extract_text_from_image(file_path)
        if ocr_text:
            final_query_text += f" {ocr_text}"

        if os.path.exists(file_path):
            os.remove(file_path)

    # 2. Fetch Live NPO Profiles from Google Sheets (Falls back to mock data if credentials are pending)
    # npo_database = load_npos_from_sheet()
    npo_database = [
        {
            "id": 1,
            "name": "彰化偏鄉數位教育協會",
            "focus": "長期深耕中部偏鄉，為小學童舉辦程式設計營隊與科技教育課程。",
        },
        {
            "id": 2,
            "name": "台灣綠能永續發展基金會",
            "focus": "推動企業ESG、環境保護、淨零碳排與校園環保講座。",
        },
    ]

    # 3. Calculate match scores using local BGE model against live sheet data
    results = []
    for npo in npo_database:
        score = calculate_match_score(final_query_text, npo["focus"])
        results.append(
            {
                "npo_name": npo["name"],
                "match_score": score,
                "focus_summary": npo["focus"],
                "reason": f"語意相似度分析結果：與該組織核心任務匹配度為 {score * 100:.1f}%。",
            }
        )

    # Sort by highest score
    results = sorted(results, key=lambda x: x["match_score"], reverse=True)

    return {
        "status": "success",
        "processed_query": final_query_text,
        "top_matches": results[:2],
    }
