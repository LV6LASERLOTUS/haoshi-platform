"""Independent rules/BGE strategies and rank fusion behind one callable entry point."""

from copy import deepcopy
from time import perf_counter

from .evidence import build_evidence
from .matching import match_organization, validate_request
from .ranking import SCORE_TYPES, rank_candidates, validate_options
from .semantic import SemanticScorer, default_bge_scorer, score_organizations
from .validation import DataIssue, DataValidationError, validate_dataset


def _build_candidates(data: dict, criteria: list[dict]) -> list[dict]:
    return [
        {"organization_id": org["organization_id"], "name": org["name"],
         **match_organization(org, criteria),
         "semantic_score": None, "semantic_evidence": [],
         "rule_rank": None, "semantic_rank": None, "ranking_score": None}
        for org in data["organizations"]
    ]


def _apply_semantic_scores(rows: list[dict], data: dict, text: str,
                           scorer: SemanticScorer | None) -> int:
    candidate_ids = {row["organization_id"] for row in rows if row["eligibility"] != "excluded"}
    evidence = build_evidence(data, candidate_ids)
    if evidence:
        provider = scorer if scorer is not None else default_bge_scorer()
        scores = score_organizations(text, evidence, provider)
        for row in rows:
            row.update(scores.get(row["organization_id"], {}))
    return len(evidence)


def _report_warnings(query: dict, buckets: dict, strategy: str,
                     document_count: int, top_k: int) -> list[str]:
    warnings = []
    if not query["criteria"]:
        warnings.append("未提供結構化條件；不自動從文字推論必要條件，規則分數為未知。")
    if strategy != "rules":
        warnings.append("BGE 僅表示文字相關性；顧問筆記屬觀察，不代表合作意願或執行能力已確認。")
        if not document_count and (buckets["eligible"] or buckets["needs_confirmation"]):
            warnings.append("候選組織沒有可供 BGE 比對的文字，語意分數為未知。")
    if len(buckets["eligible"]) < top_k:
        warnings.append("已符合必要條件的組織不足指定數量，不以待確認或已排除的組織補足。")
    return warnings


def _build_report(query: dict, buckets: dict, *, strategy: str, top_k: int,
                  rrf_k: int, document_count: int, started: float) -> dict:
    return deepcopy({
        "request_id": query["request_id"], "strategy": strategy,
        "score_type": SCORE_TYPES[strategy],
        "rrf_k": rrf_k if strategy == "hybrid" else None,
        "top_matches": buckets["eligible"][:top_k],
        "pending_matches": buckets["needs_confirmation"][:top_k],
        "excluded": buckets["excluded"],
        "counts": {key: len(value) for key, value in buckets.items()},
        "semantic_document_count": document_count,
        "warnings": _report_warnings(query, buckets, strategy, document_count, top_k),
        "elapsed_ms": round((perf_counter() - started) * 1000, 3),
    })


def recommend(dataset: dict, request: dict, *, strategy="rules", top_k=10,
              semantic_scorer: SemanticScorer | None = None, rrf_k=60) -> dict:
    """Apply hard gates, score all remaining candidates, then rank within each bucket.

    semantic_scorer.score(query, texts) returns cosine similarities in document order.
    Semantic failures are surfaced; there is no silent substitution with rule scores.
    """
    started = perf_counter()
    validate_options(strategy, top_k, rrf_k)
    data = validate_dataset(dataset)
    if data["schema_version"] != "0.2":
        raise DataValidationError([DataIssue("$.schema_version", "schema_version", "Recommendation requires v0.2 organization data")])
    query = validate_request(request)
    rows = _build_candidates(data, query["criteria"])
    document_count = 0
    if strategy != "rules":
        document_count = _apply_semantic_scores(rows, data, query["text"], semantic_scorer)
    buckets = rank_candidates(rows, strategy=strategy, rrf_k=rrf_k)
    return _build_report(query, buckets, strategy=strategy, top_k=top_k,
                         rrf_k=rrf_k, document_count=document_count, started=started)
