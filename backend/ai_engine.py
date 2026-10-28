import os

import numpy as np
from paddleocr import PaddleOCR
from sentence_transformers import SentenceTransformer, util

# 1. Initialize Local Chinese OCR (Runs 100% offline, supports Traditional/Simplified Chinese)
print("Loading PaddleOCR model...")
ocr = PaddleOCR(use_textline_orientation=True, lang="ch")

# 2. Initialize Local Chinese Semantic Embedding Model (~95MB, runs on CPU)
print("Loading BAAI/bge-small-zh-v1.5 model...")
embedding_model = SentenceTransformer("BAAI/bge-small-zh-v1.5")


def extract_text_from_image(image_path: str) -> str:
    """
    Extracts Chinese text from an uploaded image file using local PaddleOCR.
    """
    if not os.path.exists(image_path):
        return ""

    result = ocr.ocr(image_path, cls=True)
    print(result)
    extracted_lines = []

    for idx in range(len(result)):
        res = result[idx]
        if res:
            for line in res:
                text = line[1][0]  # Extracted text string
                confidence = line[1][1]
                if confidence > 0.6:  # Filter low-confidence noise
                    extracted_lines.append(text)

    return " ".join(extracted_lines)


def get_embedding(text: str) -> np.ndarray:
    """
    Converts a Chinese text string into a semantic vector embedding.
    """
    # BGE models perform best with instruction formatting for queries,
    # but direct encoding works well for short descriptive matching.
    return embedding_model.encode(text, normalize_embeddings=True)


def calculate_match_score(user_query: str, npo_focus_description: str) -> float:
    """
    Calculates cosine similarity between the user's request and an NPO's focus area description.
    Returns a score between 0.0 and 1.0.
    """
    query_vector = get_embedding(user_query)
    npo_vector = get_embedding(npo_focus_description)

    # Compute cosine similarity
    score = util.cos_sim(query_vector, npo_vector).item()
    return round(score, 4)
