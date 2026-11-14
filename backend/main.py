from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import save_feedback_to_sheet


class FeedbackRequest(BaseModel):
    question_id: str
    question_text: str
    ai_summary: str
    rating: int = Field(..., ge=1, le=5)
    feedback_type: str
    feedback_content: Optional[str] = ""


app = FastAPI(
    title="好事大平台 API",
    description="Backend server for handling mobile intake and matching requests.",
    version="1.0.0",
)

# 開發階段允許所有來源（Expo web / web-dashboard）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模擬媒合結果（欄位對應 mobile-app/api/match.js 的 toCard()）
MOCK_MATCHES = [
    {
        "npo_name": "彰化偏鄉數位教育協會",
        "match_score": 0.92,
        "focus_summary": "長期深耕中部偏鄉，為小學童舉辦程式設計營隊與科技教育課程。",
        "reason": "過去已舉辦 5 次偏鄉科技營隊，與您的需求領域高度契合。",
        "category": "教育",
        "area": "彰化縣",
        "tags": ["偏鄉教育", "程式設計", "兒童"],
        "warnings": [],
        "breakdown": {"領域": 95, "地區": 90, "預算": 88, "經驗": 94},
    },
    {
        "npo_name": "台灣綠能永續發展基金會",
        "match_score": 0.81,
        "focus_summary": "推動企業ESG、環境保護、淨零碳排與校園環保講座。",
        "reason": "擅長校園講座與 ESG 合作，可結合環境教育主題。",
        "category": "環境",
        "area": "台北市",
        "tags": ["ESG", "環境教育", "講座"],
        "warnings": ["服務地區較遠"],
        "breakdown": {"領域": 80, "地區": 65, "預算": 85, "經驗": 90},
    },
    {
        "npo_name": "青年夢想協進會",
        "match_score": 0.74,
        "focus_summary": "陪伴青少年探索職涯，提供志工培訓與營隊活動。",
        "reason": "領域契合，但需注意志工調度與活動時程。",
        "category": "青少年",
        "area": "台中市",
        "tags": ["青少年", "志工", "營隊"],
        "warnings": ["志工人力有限"],
        "breakdown": {"領域": 78, "地區": 82, "預算": 70, "經驗": 66},
    },
]


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "好事大平台 API server is running successfully!",
    }


@app.post("/api/v1/match")
async def handle_match_request(
    request_text: str = Form(...),
    category: Optional[str] = Form(None),
    area: Optional[str] = Form(None),
    budget: Optional[str] = Form(None),
    uploaded_file: Optional[UploadFile] = File(None),
):
    # TODO: 接上 OCR (extract_text_from_image) 與 BGE 匹配 (calculate_match_score)
    return {
        "status": "success",
        "processed_query": request_text,
        "top_matches": MOCK_MATCHES,
    }


@app.post("/api/v1/feedback")
async def handle_feedback_request(feedback: FeedbackRequest):
    payload = feedback.model_dump()
    saved = save_feedback_to_sheet(payload)
    return {
        "status": "success",
        "saved_to_sheet": saved,
        "feedback": payload,
    }

