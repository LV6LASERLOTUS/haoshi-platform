"""Rank candidates within eligibility groups without loading data or AI models."""

from copy import deepcopy


STRATEGIES = ("rules", "bge", "hybrid")
ELIGIBILITY_GROUPS = ("eligible", "needs_confirmation", "excluded")
SCORE_TYPES = {
    "rules": "weighted_rule_support",
    "bge": "cosine_similarity",
    "hybrid": "reciprocal_rank_fusion",
}


def validate_options(strategy: str, top_k: int, rrf_k: int) -> None:
    if strategy not in STRATEGIES:
        raise ValueError("strategy must be rules, bge or hybrid")
    if type(top_k) is not int or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    if type(rrf_k) is not int or rrf_k < 1:
        raise ValueError("rrf_k must be a positive integer")


def _competition_ranks(rows: list[dict], field: str) -> dict[str, int]:
    """Equal scores get equal ranks; IDs only resolve the display order."""
    ranked = sorted(
        (row for row in rows if row[field] is not None),
        key=lambda row: (-row[field], row["organization_id"]),
    )
    ranks = {}
    previous_score = None
    for position, row in enumerate(ranked, 1):
        if row[field] != previous_score:
            rank = position
        ranks[row["organization_id"]] = rank
        previous_score = row[field]
    return ranks


def _ranking_score(row: dict, strategy: str, rrf_k: int) -> float | None:
    if strategy == "rules":
        return row["rule_support"]
    if strategy == "bge":
        return row["semantic_score"]
    ranks = [rank for rank in (row["rule_rank"], row["semantic_rank"]) if rank is not None]
    return sum(1 / (rrf_k + rank) for rank in ranks) if ranks else None


def rank_candidates(rows: list[dict], *, strategy: str, rrf_k: int) -> dict[str, list[dict]]:
    """Return detached groups; pending/excluded candidates never alter eligible ranks."""
    validate_options(strategy, top_k=1, rrf_k=rrf_k)
    buckets = {}
    for eligibility in ELIGIBILITY_GROUPS:
        bucket = [deepcopy(row) for row in rows if row["eligibility"] == eligibility]
        if eligibility != "excluded":
            rule_ranks = _competition_ranks(bucket, "rule_support")
            semantic_ranks = _competition_ranks(bucket, "semantic_score")
            for row in bucket:
                row["rule_rank"] = rule_ranks.get(row["organization_id"])
                row["semantic_rank"] = semantic_ranks.get(row["organization_id"])
                row["ranking_score"] = _ranking_score(row, strategy, rrf_k)
        bucket.sort(key=lambda row: (
            row["ranking_score"] is None,
            -(row["ranking_score"] or 0),
            row["organization_id"],
        ))
        buckets[eligibility] = bucket
    return buckets
