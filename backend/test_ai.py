from ai_engine import get_embedding, calculate_match_score

# Test semantic understanding in Chinese
query = "我們想找中部地區推動偏鄉兒童科技教育的團隊"
npo_profile = "本組織長期深耕南投與彰化偏鄉，為小學童舉辦程式設計營隊與科技教育。"

score = calculate_match_score(query, npo_profile)
print(f"Match Similarity Score: {score}")
