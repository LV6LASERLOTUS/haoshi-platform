"""Behavioral checks for hard gates, missing facts and BGE integration."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from recommendation import BgeScorer, DataValidationError, SemanticUnavailableError, recommend
from recommendation.matching import validate_request
from recommendation.evidence import build_evidence


BACKEND = Path(__file__).resolve().parents[1]


def dataset(organizations, contacts=None, notes=None):
    return {"schema_version": "0.2", "dataset_info": {"is_mock": True, "as_of_date": "2026-11-12"},
            "organizations": organizations, "contacts": contacts or [],
            "consultant_notes": notes or [], "task_cards": []}


def organization(identifier, region=None, issues=None, staff=None):
    return {"organization_id": identifier, "name": identifier, "regions": region,
            "issue_tags": issues, "full_time_staff_count": staff}


def request(criteria=None):
    return {"request_id": "r1", "text": "教育組織資料整理專業陪跑", "criteria": criteria or []}


def criterion(field="regions", operator="any_of", value=None, required=True, weight=1):
    return {"field": field, "operator": operator, "value": ["彰化縣"] if value is None else value,
            "required": required, "weight": weight}


class ConstantScorer:
    def __init__(self, value=0.9):
        self.value = value
        self.calls = []

    def score(self, query, texts):
        self.calls.append((query, texts))
        return [self.value] * len(texts)


class RecommendationEngineTests(unittest.TestCase):
    def test_hard_mismatches_are_removed_before_semantic_scoring(self):
        data = dataset([organization("pass", ["彰化縣"], ["教育"]),
                        organization("fail", ["高雄市"], ["不可進入BGE"]),
                        organization("unknown", None, ["未知地區組織"])])
        scorer = ConstantScorer()
        report = recommend(data, request([criterion()]), strategy="hybrid", semantic_scorer=scorer)
        self.assertEqual([r["organization_id"] for r in report["top_matches"]], ["pass"])
        self.assertEqual([r["organization_id"] for r in report["pending_matches"]], ["unknown"])
        self.assertEqual([r["organization_id"] for r in report["excluded"]], ["fail"])
        self.assertTrue(all("不可進入BGE" not in text for _, texts in scorer.calls for text in texts))
        self.assertIsNone(report["excluded"][0]["semantic_score"])

    def test_required_partial_match_is_pending_and_not_used_to_fill_top_k(self):
        data = dataset([organization("partial", issues=["教育"])])
        query = request([criterion("issue_tags", "all_of", ["教育", "數位學習"])])
        report = recommend(data, query, top_k=10)
        self.assertEqual(report["top_matches"], [])
        self.assertEqual(report["pending_matches"][0]["criteria"][0]["status"], "partial")
        self.assertEqual(report["counts"]["needs_confirmation"], 1)

    def test_zero_staff_is_known_and_not_treated_as_missing(self):
        data = dataset([organization("zero", staff=0), organization("unknown")])
        query = request([criterion("full_time_staff_count", "between", [0, 8])])
        report = recommend(data, query)
        self.assertEqual(report["top_matches"][0]["organization_id"], "zero")
        self.assertEqual(report["top_matches"][0]["criteria"][0]["score"], 1)
        self.assertIsNone(report["pending_matches"][0]["criteria"][0]["score"])

    def test_missing_preferences_have_separate_coverage_and_no_fake_high_rank(self):
        data = dataset([organization("sparse", ["彰化縣"]),
                        organization("complete", ["彰化縣"], ["教育"], 3)])
        query = request([criterion(required=False),
                         criterion("issue_tags", "any_of", ["教育"], False),
                         criterion("full_time_staff_count", "between", [0, 8], False)])
        report = recommend(data, query)
        complete, sparse = report["top_matches"]
        self.assertEqual(complete["organization_id"], "complete")
        self.assertEqual(sparse["rule_score"], 1)
        self.assertAlmostEqual(sparse["coverage"], 1 / 3)
        self.assertAlmostEqual(sparse["rule_support"], 1 / 3)
        self.assertIsNone(sparse["criteria"][1]["score"])

    def test_rules_mode_does_not_load_bge_and_input_is_not_changed(self):
        data = dataset([organization("a", ["彰化縣"])])
        original = deepcopy(data)
        with patch("recommendation.engine.default_bge_scorer", side_effect=AssertionError("loaded")):
            report = recommend(data, request([criterion()]), strategy="rules")
        self.assertEqual(data, original)
        self.assertIsNone(report["top_matches"][0]["semantic_score"])

    def test_bge_evaluates_all_nonexcluded_candidates_without_rule_top_k_pruning(self):
        data = dataset([organization(f"org-{i}", ["彰化縣"], [f"議題{i}"]) for i in range(8)])
        scorer = ConstantScorer()
        recommend(data, request([criterion("issue_tags", "any_of", ["議題0"], False)]),
                  strategy="hybrid", top_k=1, semantic_scorer=scorer)
        texts = scorer.calls[0][1]
        self.assertEqual(len(texts), 8)
        self.assertTrue(any("議題7" in text for text in texts))

    def test_equal_scores_have_equal_fusion_ranks_and_deterministic_ties(self):
        data = dataset([organization("b", ["彰化縣"]), organization("a", ["彰化縣"])])
        report = recommend(data, request([criterion()]), strategy="hybrid", semantic_scorer=ConstantScorer())
        first, second = report["top_matches"]
        self.assertEqual(first["organization_id"], "a")
        self.assertEqual(first["rule_rank"], second["rule_rank"])
        self.assertEqual(first["semantic_rank"], second["semantic_rank"])
        self.assertEqual(first["ranking_score"], second["ranking_score"])
        self.assertAlmostEqual(first["ranking_score"], 2 / 61)

    def test_pending_candidates_and_input_order_do_not_change_eligible_fusion(self):
        query = request([criterion()])
        passing = [organization("a", ["彰化縣"], ["教育"]),
                   organization("b", ["彰化縣"], ["陪跑"])]
        baseline = recommend(dataset(passing), query, strategy="hybrid", semantic_scorer=ConstantScorer())
        expanded = recommend(
            dataset([organization("unknown", None, ["資料整理"]), *reversed(passing)]),
            query, strategy="hybrid", semantic_scorer=ConstantScorer(),
        )
        self.assertEqual(baseline["top_matches"], expanded["top_matches"])
        self.assertEqual(expanded["counts"]["needs_confirmation"], 1)

    def test_bge_and_rules_can_disagree_and_hybrid_preserves_both_scores(self):
        class DifferentScorer:
            def score(self, query, texts):
                return [0.2 if "兒童教育" in text else 0.9 for text in texts]
        data = dataset([organization("a", issues=["兒童教育"]), organization("b", issues=["其他議題"])])
        query = request([criterion("issue_tags", "any_of", ["兒童教育"], False)])
        rules = recommend(data, query)
        bge = recommend(data, query, strategy="bge", semantic_scorer=DifferentScorer())
        hybrid = recommend(data, query, strategy="hybrid", semantic_scorer=DifferentScorer())
        self.assertEqual(rules["top_matches"][0]["organization_id"], "a")
        self.assertEqual(bge["top_matches"][0]["organization_id"], "b")
        self.assertEqual(hybrid["score_type"], "reciprocal_rank_fusion")
        self.assertIsNotNone(hybrid["top_matches"][0]["rule_score"])
        self.assertIsNotNone(hybrid["top_matches"][0]["semantic_score"])

    def test_no_criteria_does_not_invent_rules_from_free_text(self):
        data = dataset([organization("a", ["高雄市"])])
        report = recommend(data, {"request_id": "r1", "text": "必須在彰化縣"})
        self.assertIsNone(report["top_matches"][0]["rule_score"])
        self.assertIsNone(report["top_matches"][0]["coverage"])
        self.assertEqual(report["top_matches"][0]["eligibility"], "eligible")
        self.assertTrue(report["warnings"])

    def test_no_documents_preserves_unknown_semantics_without_loading_model(self):
        with patch("recommendation.engine.default_bge_scorer", side_effect=AssertionError("loaded")):
            report = recommend(dataset([organization("empty")]), request(), strategy="hybrid")
        self.assertIsNone(report["top_matches"][0]["semantic_score"])
        self.assertIsNone(report["top_matches"][0]["ranking_score"])

    def test_semantic_failures_and_invalid_scores_do_not_silently_become_rules(self):
        data = dataset([organization("a", ["彰化縣"])])
        class BrokenScorer:
            def score(self, query, texts):
                raise SemanticUnavailableError("missing model")
        with self.assertRaises(SemanticUnavailableError):
            recommend(data, request(), strategy="hybrid", semantic_scorer=BrokenScorer())
        for value in (float("nan"), float("inf"), 2, -2, True, "0.9"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                recommend(data, request(), strategy="bge", semantic_scorer=ConstantScorer(value))
        class WrongCount:
            def score(self, query, texts):
                return []
        with self.assertRaises(ValueError):
            recommend(data, request(), strategy="bge", semantic_scorer=WrongCount())

    def test_negative_cosines_sort_below_zero_and_missing_stays_last(self):
        class NegativeScorer:
            def score(self, query, texts):
                return [-0.5 if "負分" in text else 0.0 for text in texts]
        data = dataset([organization("missing"), organization("negative", issues=["負分"]),
                        organization("zero", issues=["零分"])])
        report = recommend(data, request(), strategy="bge", semantic_scorer=NegativeScorer())
        self.assertEqual([row["organization_id"] for row in report["top_matches"]], ["zero", "negative", "missing"])

    def test_source_family_aggregation_does_not_reward_repeated_identical_contacts(self):
        data = dataset([organization("a", issues=["教育"]), organization("b", issues=["教育"])],
                       contacts=[{"contact_id": f"c{i}", "organization_id": org_id,
                                  "free_text": "同一個觀察", "date": "2026-11-01"}
                                 for i, org_id in enumerate(["a", "b", "b", "b", "b"])])
        report = recommend(data, request(), strategy="bge", semantic_scorer=ConstantScorer(0.5))
        self.assertEqual(report["top_matches"][0]["semantic_score"], report["top_matches"][1]["semantic_score"])

    def test_request_validation_rejects_unconfirmed_fields_and_bad_criteria(self):
        bad = [criterion("platform_listing_status", "one_of", ["上架"]),
               criterion("full_time_staff_count", "between", [8, 0]),
               criterion(value=[]), criterion(weight=0), criterion(weight=True),
               criterion(required="yes"), criterion(operator="unsupported"),
               criterion("full_time_staff_count", "between", [False, 8])]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(DataValidationError):
                validate_request(request([item]))
        with self.assertRaises(DataValidationError):
            validate_request(request([criterion(), criterion()]))
        for value in (None, [], "request"):
            with self.assertRaises(DataValidationError):
                validate_request(value)

    def test_large_valid_weights_do_not_create_nonfinite_scores(self):
        data = dataset([organization("a", ["彰化縣"], ["教育"])])
        query = request([criterion(weight=1e308),
                         criterion("issue_tags", "any_of", ["教育"], False, 1e308)])
        row = recommend(data, query)["top_matches"][0]
        self.assertEqual(row["rule_score"], 1)
        self.assertEqual(row["rule_support"], 1)
        self.assertEqual(row["coverage"], 1)
        with self.assertRaises(DataValidationError):
            validate_request(request([criterion(weight=10 ** 1000)]))

    def test_document_builder_limits_history_and_keeps_latest_references(self):
        from recommendation import validate_dataset
        contacts = [{"contact_id": f"c{i}", "organization_id": "a", "date": f"2026-11-{i:02d}",
                     "free_text": "觀察" * 300, "source": "mock:source"} for i in range(1, 6)]
        data = validate_dataset(dataset([organization("a", issues=["教育"])], contacts))
        docs = build_evidence(data, {"a"})
        history = [doc for doc in docs if doc["kind"] == "contact"]
        self.assertEqual([doc["record_id"] for doc in history], ["c5", "c4", "c3"])
        self.assertTrue(all(len(doc["text"]) <= 240 for doc in docs))
        self.assertEqual(history[0]["source"], "mock:source")

    def test_demo_can_run_through_cli_without_ai_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            run = subprocess.run([sys.executable, "-S", "-m", "recommendation",
                                  "docs/recommendation-example.json", "--request",
                                  "docs/recommendation-request-example.json", "--strategy", "rules",
                                  "--output", str(output)], cwd=BACKEND, capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["strategy"], "rules")
        self.assertEqual(len(report["top_matches"]), 10)
        self.assertGreater(report["counts"]["excluded"], 0)


class BgeIntegrationTests(unittest.TestCase):
    def test_batch_cache_query_instruction_and_content_change(self):
        class Encoder:
            def __init__(self):
                self.calls = []
            def encode(self, texts, **kwargs):
                self.calls.append((texts, kwargs))
                return [[1.0, 0.0] for _ in texts]
        encoder = Encoder()
        scorer = BgeScorer(encoder=encoder)
        self.assertEqual(scorer.score("查詢", ["內容一", "內容二"]), [1, 1])
        self.assertEqual(len(encoder.calls), 1)
        self.assertTrue(encoder.calls[0][0][0].startswith("为这个句子生成表示"))
        self.assertEqual(encoder.calls[0][0][1:], ["內容一", "內容二"])
        self.assertTrue(encoder.calls[0][1]["normalize_embeddings"])
        scorer.score("查詢", ["內容一", "內容二"])
        self.assertEqual(len(encoder.calls), 1)
        scorer.score("查詢", ["內容一", "更新內容"])
        self.assertEqual(encoder.calls[1][0], ["更新內容"])

    def test_batch_larger_than_cache_and_empty_texts(self):
        class Encoder:
            def encode(self, texts, **kwargs):
                return [[0.6, 0.8] for _ in texts]
        scorer = BgeScorer(encoder=Encoder(), cache_size=1)
        self.assertEqual(scorer.score("q", []), [])
        self.assertEqual(scorer.score("q", ["a", "b", "c"]), [1, 1, 1])
        self.assertEqual(len(scorer._vectors), 1)


if __name__ == "__main__":
    unittest.main()
