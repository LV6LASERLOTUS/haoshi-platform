import os
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def get_ocr_model():
    """只在處理圖片時載入 OCR，純文字推薦不需要初始化它。"""
    from paddleocr import PaddleOCR

    return PaddleOCR(use_textline_orientation=True, lang="ch")


@lru_cache(maxsize=1)
def get_embedding_model():
    """首次需要時載入 BGE；首次使用仍需本機模型快取或下載模型。"""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("BAAI/bge-small-zh-v1.5")


def extract_text_from_image(image_path: str) -> str:
    """
    使用本地 PaddleOCR 從上傳的圖片檔中擷取中文文字。
    """
    if not os.path.exists(image_path):
        return ""

    result = get_ocr_model().predict(image_path)
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
    return get_embedding_model().encode(text, normalize_embeddings=True)


def calculate_match_score(user_query: str, npo_focus_description: str) -> float:
    """
    計算使用者需求與 NPO 關注領域描述之間的餘弦相似度。
    回傳介於 -1.0 到 1.0 之間的餘弦相似度，保留四位小數。
    此值是語意比對特徵，不是 0–100 的需求契合指數或合作成功率。
    """
    query_vector = get_embedding(user_query)
    npo_vector = get_embedding(npo_focus_description)

    # 計算餘弦相似度
    # 向量已正規化，內積即為餘弦相似度。
    score = np.dot(query_vector, npo_vector).item()
    # 限制浮點誤差造成的微小越界，保留負相似度的意義。
    return round(float(np.clip(score, -1.0, 1.0)), 4)
