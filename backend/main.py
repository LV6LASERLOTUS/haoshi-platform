from fastapi import FastAPI, Form, UploadFile, File
from typing import Optional

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
    """
    Endpoint for the mobile app to send text requests and optional files/images.
    """
    file_name = uploaded_file.filename if uploaded_file else "No file uploaded"

    # Placeholder logic (we will plug in PaddleOCR and Sentence-Transformers here later)
    return {
        "status": "success",
        "message": "Request received and processed by backend!",
        "data": {
            "request_text": request_text,
            "attached_file": file_name,
            "top_matches": [
                {
                    "npo_name": "範例偏鄉教育協會 (Mock Result)",
                    "match_score": 0.92,
                    "reason": "根據您的文字描述，與該組織的教育專案高度匹配。",
                }
            ],
        },
    }
