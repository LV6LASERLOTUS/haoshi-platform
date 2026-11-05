import os

import numpy as np
from paddleocr import PaddleOCR
from sentence_transformers import SentenceTransformer, util

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
