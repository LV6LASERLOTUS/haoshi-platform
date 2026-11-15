"""Orchestration, using the same BGE model as the existing AI engine."""

from datetime import datetime, timedelta, timezone
from functools import lru_cache

from .demand import build_plan
from .schemas import Demand, RecommendationResponse, Snapshot
from .scoring import SemanticScorer, SemanticUnavailableError, score_organization


@lru_cache(maxsize=2048)
def _encode(text: str):
    from ai_engine import get_embedding

    return get_embedding(text)


class BgeScorer:
    def similarity(self, query: str, passage: str) -> float:
        import numpy as np

        try:
            # Instruction on the query only; historical evidence remains unchanged.
            q = _encode("为这个句子生成表示以用于检索相关文章：" + query)
            p = _encode(passage)
            return float(np.dot(q, p))
        except (ImportError, OSError, RuntimeError, ValueError) as exc:
            raise SemanticUnavailableError("BGE 無法使用，未以隨機或規則分數冒充語意分數。") from exc


def recommend(demand: Demand, snapshot: Snapshot, scorer: SemanticScorer | None = None,
              as_of=None) -> RecommendationResponse:
    plan = build_plan(demand)
    if plan.clarification_questions:
        return RecommendationResponse(status="needs_clarification", plan=plan, warnings=plan.warnings)
    scorer = scorer or BgeScorer()
    as_of = as_of or datetime.now(timezone(timedelta(hours=8))).date()
    results = [score_organization(org, demand, plan, scorer, as_of, snapshot.captured_at)
               for org in snapshot.organizations]
    groups = {"review_candidate": 0, "needs_verification": 1, "core_mismatch": 2, "insufficient_evidence": 3}
    candidates = [result for result in results if result.eligibility_status != "Ineligible"]
    excluded = [result for result in results if result.eligibility_status == "Ineligible"]
    candidates.sort(key=lambda r: (groups[r.scoring_status], -r.match_score, -r.evidence_coverage, r.npo_id))
    excluded.sort(key=lambda r: r.npo_id)
    warnings = list(plan.warnings) + snapshot.warnings
    if len(candidates) < plan.candidate_limit:
        warnings.append(f"目前可保留候選 {len(candidates)} 家，少於目標候選 {plan.candidate_limit} 家；未補入模擬組織。")
    if len(candidates) < demand.target_count:
        warnings.append(f"候選不足支持目標 {demand.target_count} 家，需補資料或由企業明確調整條件。")
    return RecommendationResponse(
        status="success", plan=plan, recommendations=candidates[:plan.candidate_limit], excluded=excluded,
        total_organizations=len(results), available_candidates=len(candidates), warnings=warnings,
    )
