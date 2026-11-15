"""Merge regressions: preserve main's helpers without real API calls or writes."""

import json
import unittest
from unittest.mock import MagicMock, patch


class MainCompatibilityTests(unittest.TestCase):
    def test_openai_summary_helper_survives_lazy_bge_initialization(self):
        import ai_engine

        response = MagicMock()
        payload = {"top_recommendations": [{"rank": i} for i in range(1, 8)], "ai_summary": "測試摘要"}
        response.json.return_value = {"choices": [{"message": {"content": json.dumps(payload)}}]}
        with patch.object(ai_engine, "_load_openai_api_key", return_value="test-only"), \
                patch.object(ai_engine.httpx, "post", return_value=response) as post, \
                patch.object(ai_engine, "get_ocr_model", side_effect=AssertionError("OCR loaded")), \
                patch.object(ai_engine, "get_embedding_model", side_effect=AssertionError("BGE loaded")):
            result = ai_engine.evaluate_and_summarize_ngos("top", "sheet", "feedback")
        self.assertEqual(len(result["top_recommendations"]), 5)
        self.assertEqual(result["ai_summary"], "測試摘要")
        self.assertEqual(post.call_args.args[0], ai_engine.OPENAI_CHAT_URL)
        response.raise_for_status.assert_called_once()

    def test_query_helper_preserves_main_contract_without_sheet_write(self):
        import database

        client, spreadsheet, worksheet = MagicMock(), MagicMock(), MagicMock()
        client.open_by_url.return_value = spreadsheet
        spreadsheet.worksheet.return_value = worksheet
        worksheet.get.return_value = [["測試組織"], ["T01"]]
        with patch.object(database.gspread, "service_account", return_value=client), \
                patch.object(database.time, "sleep"):
            result = database.query_ngo("測試組織")
        self.assertEqual(database.FEEDBACK_WORKSHEET_NAME, "NPO_feedback")
        self.assertEqual(result["organization_id"], "T01")
        self.assertEqual(result["ai_analysis_output"], "")
        worksheet.update.assert_called_once_with([["測試組織"]], "B2")

    def test_both_evidence_interfaces_remain_available(self):
        from recommendation import recommend as legacy_recommend
        from recommendation.evidence import build_evidence, build_snapshot
        from recommendation.service import recommend as csr_recommend

        self.assertTrue(callable(build_evidence))
        self.assertTrue(callable(build_snapshot))
        self.assertIsNot(legacy_recommend, csr_recommend)


if __name__ == "__main__":
    unittest.main()
