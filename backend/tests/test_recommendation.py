"""Offline acceptance tests. Fixtures are NOT production NGO facts or BGE outputs."""

import unittest
from datetime import date, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from recommendation.demand import build_plan
from recommendation.evidence import DataSourceError, build_snapshot
from recommendation.schemas import Demand, Period
from recommendation.scoring import SemanticUnavailableError, temporal_trust
from recommendation.service import recommend

AS_OF = date(2026, 11, 15)
DIM_HEADERS = ["組織編號", "組織名稱", "一句話簡介", "議題", "服務對象", "區域", "全職人數", "會籍", "重要資訊摘要", "AI分析輸入"]
CONTACT_HEADERS = ["紀錄編號", "組織編號", "日期", "活動或事件名稱", "留下的話／紀錄內容"]
NOTE_HEADERS = ["組織編號", "日期", "記錄者", "筆記"]


class FixedSemanticScorer:
    """Deterministic test double; never used by production service."""
    def __init__(self, value=.8):
        self.value, self.calls = value, []

    def similarity(self, query, passage):
        self.calls.append((query, passage))
        return self.value


def snapshot(text=None, notes=None, extra_contacts=None, staff="8", ai_input=""):
    tables = {
        "NPO_dim": [DIM_HEADERS, ["T01", "測試組織", "學童課後陪伴", "教育", "國小學童", "台北", staff, "非會員", ai_input, ai_input]],
        "②接觸紀錄": [CONTACT_HEADERS], "③顧問筆記": [NOTE_HEADERS],
    }
    if text:
        tables["②接觸紀錄"].append(["R01", "T01", "2026-11-01", "行銷培力課程", text])
    if notes:
        tables["③顧問筆記"].append(["T01", "2026-11-02", "顧問", notes])
    tables["②接觸紀錄"].extend(extra_contacts or [])
    return build_snapshot(tables, {key: i for i, key in enumerate(tables)},
                          "https://docs.google.com/spreadsheets/d/test/edit", "2026-11-15T00:00:00+00:00")


def demand(**kwargs):
    return Demand(**({"description": "提供公關行銷能力培力", "resources": ["marketing"]} | kwargs))


def score(data, request=None, semantic=None):
    return recommend(request or demand(), data, semantic or FixedSemanticScorer(), AS_OF).recommendations[0]


class RecommendationTests(unittest.TestCase):
    def test_plan_deactivates_unspecified_size_time_and_area(self):
        plan = build_plan(demand())
        self.assertEqual(set(plan.weights), {"resource_need", "readiness"})
        self.assertAlmostEqual(sum(plan.weights.values()), 1)
        self.assertIn("size", plan.inactive_dimensions)

    def test_half_year_requires_dates(self):
        plan = build_plan(demand(description="行銷陪跑為期半年"))
        self.assertTrue(plan.clarification_questions)

    def test_esg_purpose_does_not_change_plan_or_query(self):
        a, b = FixedSemanticScorer(), FixedSemanticScorer()
        first = score(snapshot("想學行銷"), demand(), a)
        second = score(snapshot("想學行銷"), demand(corporate_purpose="成果供 ESG 報告使用"), b)
        self.assertEqual(first.match_score, second.match_score)
        self.assertEqual(a.calls, b.calls)
        self.assertNotIn("ESG", b.calls[0][0])

    def test_summary_and_ai_input_never_become_evidence(self):
        result = score(snapshot(ai_input="確認參加行銷陪跑，需要行銷資源"))
        self.assertEqual(result.evidence_coverage, 0)
        self.assertEqual(result.scoring_status, "insufficient_evidence")
        self.assertEqual(result.source_evidence, [])

    def test_complete_example(self):
        request = demand(plan_name="行銷陪跑V1", period=Period(start=date(2027, 1, 1), end=date(2027, 6, 30)))
        data = snapshot("需要行銷協助；確認可參加行銷陪跑V1，期間2027-01-01至2027-06-30")
        result = score(data, request)
        self.assertAlmostEqual(result.match_score, 93.33)
        self.assertEqual(result.evidence_coverage, 1)
        self.assertEqual(result.scoring_status, "review_candidate")

    def test_partial_example_keeps_unknowns_and_range(self):
        request = demand(plan_name="行銷陪跑V1", period=Period(start=date(2027, 1, 1), end=date(2027, 6, 30)))
        result = score(snapshot("需要行銷協助"), request)
        self.assertEqual(result.match_score, 62.22)
        self.assertAlmostEqual(result.evidence_coverage, 5 / 9, places=5)
        self.assertEqual(result.known_score, 88)
        self.assertEqual(result.score_range, (48.89, 93.33))
        self.assertEqual(result.subscores["time"].state, "Unknown")
        self.assertIsNone(result.subscores["time"].score)
        self.assertEqual(result.scoring_status, "review_candidate")
        self.assertTrue(result.verification_required)
        self.assertTrue(any("低於 60%" in message for message in result.warnings))

    def test_no_need_overrides_high_semantic(self):
        semantic = FixedSemanticScorer(.99)
        result = score(snapshot("不需要行銷協助"), semantic=semantic)
        self.assertEqual(result.subscores["resource_need.marketing.semantic"].score, 0)
        self.assertEqual(result.subscores["resource_need.marketing.semantic"].method, "rule_override")
        self.assertEqual(result.subscores["resource_need.marketing.semantic"].raw_cosine, .99)
        self.assertEqual(result.scoring_status, "core_mismatch")
        self.assertEqual(len(semantic.calls), 1)

    def test_conflicting_need_is_unknown_not_latest_wins(self):
        data = snapshot("需要行銷協助", extra_contacts=[["R02", "T01", "2026-11-10", "行銷", "不需要行銷協助"]])
        result = score(data)
        self.assertEqual(result.subscores["resource_need.marketing.explicit"].state, "Unknown")
        self.assertEqual(len(result.source_evidence), 2)

    def test_refusal_of_sankey_is_not_refusal_of_marketing(self):
        result = score(snapshot("不同意上架桑基圖"))
        self.assertEqual(result.subscores["resource_need.marketing.explicit"].state, "Unknown")

    def test_tentative_no_need_and_negated_desire_do_not_confirm_need(self):
        for text in ("可能不需要行銷協助", "不想學行銷", "並非想學行銷"):
            with self.subTest(text=text):
                result = score(snapshot(text))
                self.assertEqual(result.subscores["resource_need.marketing.explicit"].state, "Unknown")

    def test_contrast_in_same_record_preserves_conflict(self):
        result = score(snapshot("不需要行銷協助但想學行銷"))
        self.assertEqual(result.subscores["resource_need.marketing.explicit"].state, "Unknown")

    def test_any_and_all_resource_eligibility_are_distinct_and_traceable(self):
        data = snapshot("需要行銷協助；不需要財務協助")
        request = demand(resources=["marketing", "finance"], required_conditions=["resource_need"])
        result = score(data, request)
        self.assertEqual(result.eligibility_status, "Eligible")
        referenced = {eid for check in result.eligibility_checks.values() for eid in check.evidence_ids}
        self.assertTrue(referenced <= {e.evidence_id for e in result.source_evidence})
        request.resource_mode = "all"
        response = recommend(request, data, FixedSemanticScorer(), AS_OF)
        self.assertEqual(response.excluded[0].eligibility_status, "Ineligible")

    def test_existing_marketing_department_is_not_absence_of_need(self):
        result = score(snapshot(notes="有自己的品牌與行銷部門"))
        self.assertEqual(result.subscores["resource_need.marketing.explicit"].state, "Unknown")

    def test_duplicate_history_does_not_change_score(self):
        a = score(snapshot("想學行銷"))
        b = score(snapshot("想學行銷", extra_contacts=[["R02", "T01", "2026-11-01", "行銷培力課程", "想學行銷"]]))
        self.assertEqual(a.match_score, b.match_score)
        self.assertEqual(len(a.source_evidence), len(b.source_evidence))

    def test_unrelated_attendance_does_not_add_motivation(self):
        a = score(snapshot("想學行銷"))
        b = score(snapshot("想學行銷", extra_contacts=[["R02", "T01", "2026-11-10", "會員大會", "出席"]]))
        self.assertEqual(a.match_score, b.match_score)
        self.assertEqual(b.subscores["readiness"].state, "Unknown")

    def test_source_quote_offsets_and_record_id_are_preserved(self):
        result = score(snapshot("出席，想學行銷；已開始試做"))
        for e in result.source_evidence:
            self.assertEqual(e.quote, e.original_text[e.start:e.end])
            self.assertEqual(e.source_record_id, "R01")

    def test_orphan_record_is_not_assigned_by_name(self):
        data = snapshot(extra_contacts=[["R02", "", "2026-11-01", "行銷", "想學行銷"]])
        self.assertTrue(data.warnings)
        self.assertEqual(score(data).evidence_coverage, 0)

    def test_future_evidence_is_not_used(self):
        result = score(snapshot(extra_contacts=[["R02", "T01", "2027-01-01", "行銷", "想學行銷"]]))
        self.assertEqual(result.evidence_coverage, 0)

    def test_old_evidence_is_kept_but_ranking_trust_decreases(self):
        recent = score(snapshot("想學行銷"))
        old = score(snapshot(extra_contacts=[["R02", "T01", "2023-01-01", "行銷", "想學行銷"]]))
        self.assertEqual(old.match_score, recent.match_score)
        self.assertGreater(old.evidence_coverage, 0)
        self.assertLess(old.evidence_trust, recent.evidence_trust)
        self.assertLess(old.ranking_score, recent.ranking_score)
        self.assertEqual(old.scoring_status, "historical_candidate")
        self.assertTrue(old.verification_required)

    def test_two_year_half_life_is_continuous_without_year_cutoff(self):
        e = snapshot("想學行銷").organizations[0].evidence[-1]
        e.event_date = AS_OF
        self.assertEqual(temporal_trust(e, AS_OF), 1)
        e.event_date = AS_OF - timedelta(days=730)
        self.assertAlmostEqual(temporal_trust(e, AS_OF), .5)
        e.event_date = AS_OF - timedelta(days=3650)
        self.assertGreater(temporal_trust(e, AS_OF), 0)

    def test_old_refusal_does_not_exclude_present_required_resource(self):
        data = snapshot(extra_contacts=[["R02", "T01", "2020-01-01", "行銷", "不需要行銷協助"]])
        result = score(data, demand(required_conditions=["resource_need"]))
        self.assertEqual(result.subscores["resource_need.marketing.explicit"].score, 0)
        self.assertEqual(result.eligibility_status, "Unverified")
        self.assertEqual(result.scoring_status, "historical_candidate")

    def test_undated_need_is_low_trust_and_not_a_confirmed_eligibility(self):
        data = snapshot(extra_contacts=[["R02", "T01", "", "行銷", "想學行銷"]])
        result = score(data, demand(required_conditions=["resource_need"]))
        self.assertAlmostEqual(result.evidence_trust, .35)
        self.assertEqual(result.eligibility_status, "Unverified")
        self.assertTrue(result.source_evidence)

    def test_semantic_reference_can_retrieve_without_resource_keyword(self):
        semantic = FixedSemanticScorer(.8)
        result = score(snapshot("期待讓更多人理解我們的故事"), semantic=semantic)
        self.assertTrue(semantic.calls)
        self.assertEqual(result.subscores["resource_need.marketing.semantic"].raw_cosine, .8)
        self.assertEqual(result.subscores["resource_need.marketing.explicit"].state, "Unknown")
        self.assertEqual(result.subscores["readiness"].state, "Unknown")
        self.assertEqual(result.scoring_status, "semantic_candidate")
        self.assertTrue(result.verification_required)

    def test_semantic_reference_does_not_confirm_required_need(self):
        result = score(snapshot("期待讓更多人理解我們的故事"), demand(required_conditions=["resource_need"]))
        self.assertEqual(result.eligibility_status, "Unverified")

    def test_all_unknown_unchanged_not_artificially_boosted(self):
        result = score(snapshot())
        self.assertEqual(result.match_score, 30)
        self.assertEqual(result.ranking_score, 30)
        self.assertEqual(result.evidence_coverage, 0)
        self.assertEqual(result.evidence_trust, 0)

    def test_all_history_searched_but_aggregation_is_bounded_and_deduplicated(self):
        contacts = [[f"R{i:02}", "T01", "2026-11-01", "觀察", f"期待對外分享故事的方式{i}"] for i in range(10)]
        semantic = FixedSemanticScorer(.8)
        result = score(snapshot(extra_contacts=contacts), semantic=semantic)
        self.assertEqual(len(semantic.calls), 10)
        self.assertEqual(len(result.subscores["resource_need.marketing.semantic"].evidence_ids), 3)
        a = score(snapshot("期待更多人看見我們"))
        b = score(snapshot("期待更多人看見我們", extra_contacts=[["R02", "T01", "2026-11-01", "觀察", "期待更多人看見我們"]]))
        self.assertEqual(a.ranking_score, b.ranking_score)

    def test_relevant_older_fourth_record_is_not_lost_before_bge(self):
        class MeaningScorer(FixedSemanticScorer):
            def similarity(self, query, passage):
                self.calls.append((query, passage))
                return .95 if "品牌故事" in passage else .2
        contacts = [[f"R{i}", "T01", "2026-11-10", "紀錄", f"組織一般行政近況{i}"] for i in range(4)]
        contacts.append(["Rold", "T01", "2022-01-01", "紀錄", "期待讓更多人理解品牌故事"])
        result = score(snapshot(extra_contacts=contacts), semantic=MeaningScorer())
        semantic = result.subscores["resource_need.marketing.semantic"]
        self.assertTrue(any("Rold" in eid for eid in semantic.evidence_ids))
        self.assertAlmostEqual(semantic.raw_cosine, (.95 + .2 + .2) / 3)
        self.assertEqual(result.subscores["resource_need.marketing.explicit"].state, "Unknown")

    def test_keyword_hit_does_not_stop_searching_different_wording(self):
        semantic = FixedSemanticScorer()
        score(snapshot("想學行銷", extra_contacts=[["Rother", "T01", "2026-11-02", "紀錄", "期待讓更多人理解我們的品牌故事"]]), semantic=semantic)
        self.assertTrue(any("品牌故事" in passage for _, passage in semantic.calls))

    def test_old_participation_and_time_claims_do_not_exclude_current_plan(self):
        request = demand(plan_name="行銷陪跑V1", period=Period(start=date(2027, 1, 1), end=date(2027, 6, 30)),
                         required_conditions=["time", "participation"])
        data = snapshot(extra_contacts=[["R02", "T01", "2020-01-01", "行銷陪跑V1",
                                        "行銷陪跑V1期間2027-01-01至2027-06-30確認無法參加"]])
        result = score(data, request)
        self.assertEqual(result.eligibility_checks["time"].status, "Unverified")
        self.assertEqual(result.eligibility_checks["participation"].status, "Unverified")
        self.assertTrue(result.verification_required)

    def test_summary_explains_new_candidate_types_and_separates_ranking(self):
        from recommendation_cli import format_summary
        response = recommend(demand(), snapshot("期待讓更多人理解我們的故事"), FixedSemanticScorer(), AS_OF)
        summary = format_summary(response)
        self.assertIn("契合分 | 排序分", summary)
        self.assertIn("語意參考待確認", summary)
        self.assertIn("不是正確率", summary)

    def test_required_unknown_is_retained(self):
        request = demand(plan_name="行銷陪跑V1", required_conditions=["participation"])
        response = recommend(request, snapshot("想學行銷"), FixedSemanticScorer(), AS_OF)
        self.assertEqual(len(response.recommendations), 1)
        self.assertEqual(response.recommendations[0].eligibility_status, "Unverified")
        self.assertEqual(response.excluded, [])

    def test_required_size_mismatch_is_excluded(self):
        response = recommend(demand(staff_max=5, required_conditions=["size"]), snapshot("想學行銷"), FixedSemanticScorer(), AS_OF)
        self.assertEqual(response.recommendations, [])
        self.assertEqual(response.excluded[0].eligibility_status, "Ineligible")

    def test_missing_size_is_not_zero_or_excluded(self):
        result = score(snapshot("想學行銷", staff=""), demand(staff_max=5, required_conditions=["size"]))
        self.assertEqual(result.subscores["size"].state, "Unknown")
        self.assertEqual(result.eligibility_status, "Unverified")

    def test_service_area_not_inferred_from_registered_location(self):
        result = score(snapshot("想學行銷"), demand(areas=["台北"], required_conditions=["area"]))
        self.assertEqual(result.subscores["area"].state, "Unknown")
        self.assertEqual(result.eligibility_status, "Unverified")

    def test_primary_target_mismatch_not_proof_of_ineligibility(self):
        result = score(snapshot(), Demand(description="公益議題合作", demand_type="issue_collaboration", target_groups=["長者"], required_conditions=["target"]))
        self.assertEqual(result.subscores["target"].score, 0)
        self.assertEqual(result.eligibility_status, "Unverified")

    def test_other_plan_not_proof_of_time_conflict(self):
        request = demand(plan_name="行銷陪跑V1", period=Period(start=date(2027, 1, 1), end=date(2027, 6, 30)))
        result = score(snapshot(notes="入選其他三年期計畫，這陣子應該很忙"), request)
        self.assertEqual(result.subscores["time"].state, "Unknown")

    def test_explicit_time_conflict_excluded_only_when_required(self):
        request = demand(plan_name="行銷陪跑V1", period=Period(start=date(2027, 1, 1), end=date(2027, 6, 30)), required_conditions=["time"])
        data = snapshot("需要行銷協助；行銷陪跑V1期間2027-01-01至2027-06-30確認無法參加")
        response = recommend(request, data, FixedSemanticScorer(), AS_OF)
        self.assertEqual(response.excluded[0].eligibility_checks["time"].status, "Ineligible")

    def test_unknown_demand_or_resource_is_clarified(self):
        for request in (Demand(description="想做一些CSR"), demand(resources=["not-a-resource"]), demand(resource_direction="seek_ngo_service")):
            with self.subTest(request=request):
                self.assertTrue(build_plan(request).clarification_questions)

    def test_validation_rejects_inconsistent_conditions(self):
        with self.assertRaises(ValidationError):
            demand(staff_min=10, staff_max=3)
        with self.assertRaises(ValidationError):
            Demand(description="   ")

    def test_nonfinite_semantic_is_error_not_fake_score(self):
        with self.assertRaises(SemanticUnavailableError):
            score(snapshot("想學行銷"), semantic=FixedSemanticScorer(float("nan")))

    def test_real_sheet_error_not_mock(self):
        with self.assertRaises(DataSourceError):
            build_snapshot({}, {}, "url", "time")

    def test_api_plan_and_clarification_do_not_read_sheets(self):
        from main import app
        client = TestClient(app)
        with patch("main.load_recommendation_snapshot") as loader:
            response = client.post("/api/v1/recommendations/plan", json=demand().model_dump(mode="json"))
            self.assertEqual(response.status_code, 200)
            response = client.post("/api/v1/recommendations", json={"description": "想做CSR"})
            self.assertEqual(response.json()["status"], "needs_clarification")
            loader.assert_not_called()

    def test_api_returns_503_for_data_error(self):
        from main import app
        with patch("main.load_recommendation_snapshot", side_effect=DataSourceError("來源失敗")):
            response = TestClient(app).post("/api/v1/recommendations", json=demand().model_dump(mode="json"))
            self.assertEqual(response.status_code, 503)

    def test_api_success_returns_real_contract_and_traceable_scores(self):
        from main import app
        with patch("main.load_recommendation_snapshot", return_value=snapshot("想學行銷")), patch("recommendation.service.BgeScorer", return_value=FixedSemanticScorer()):
            response = TestClient(app).post("/api/v1/recommendations", json=demand().model_dump(mode="json"))
        self.assertEqual(response.status_code, 200)
        item = response.json()["recommendations"][0]
        self.assertTrue(0 <= item["match_score"] <= 100)
        self.assertIn("raw_cosine", item["subscores"]["resource_need.marketing.semantic"])
        self.assertTrue(item["source_evidence"])

    def test_api_returns_503_instead_of_fake_bge_score(self):
        from main import app
        with patch("main.load_recommendation_snapshot", return_value=snapshot("想學行銷")), patch("main.recommend", side_effect=SemanticUnavailableError("模型不可用")):
            response = TestClient(app).post("/api/v1/recommendations", json=demand().model_dump(mode="json"))
        self.assertEqual(response.status_code, 503)

    def test_cosine_preserves_negative_values_and_clips_roundoff(self):
        import numpy as np
        from ai_engine import calculate_match_score
        for vector, expected in ((np.array([-1., 0.]), -1.), (np.array([1.00000001, 0.]), 1.)):
            with self.subTest(expected=expected), patch("ai_engine.get_embedding", side_effect=[vector, np.array([1., 0.])]):
                self.assertEqual(calculate_match_score("query", "passage"), expected)

    def test_legacy_match_contract_is_preserved(self):
        from main import app
        response = TestClient(app).post("/api/v1/match", data={"request_text": "教育資源"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(0 <= response.json()["top_matches"][0]["match_score"] <= 1)


if __name__ == "__main__":
    unittest.main()
