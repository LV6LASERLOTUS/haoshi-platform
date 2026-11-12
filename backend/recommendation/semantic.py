"""Lazy local BGE scoring and aggregation, independent of rules and HTTP."""

from collections import OrderedDict
from functools import lru_cache
import math
from typing import Protocol, Sequence


class SemanticScorer(Protocol):
    """Implement this interface to inject BGE, a different model, or a test double."""

    def score(self, query: str, texts: list[str]) -> Sequence[float]: ...


class SemanticUnavailableError(RuntimeError):
    """The requested model or its runtime cannot be loaded locally."""


class BgeScorer:
    """Batch normalized embeddings; cache by full text within this model instance.

    No OCR imports, downloads, or model loading occur until score() needs vectors.
    Pass an existing SentenceTransformer as encoder to reuse a loaded model.
    """

    def __init__(self, model_name="BAAI/bge-small-zh-v1.5", *, encoder=None, cache_size=2048):
        if type(cache_size) is not int or cache_size < 1:
            raise ValueError("cache_size must be a positive integer")
        self.model_name = model_name
        self._encoder = encoder
        self._vectors = OrderedDict()
        self.cache_size = cache_size

    def _model(self):
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._encoder = SentenceTransformer(self.model_name, local_files_only=True)
            except (ImportError, OSError, RuntimeError, ValueError) as exc:
                raise SemanticUnavailableError(
                    f"Cannot load local BGE model {self.model_name}: {exc}. "
                    "Prepare the model locally or run strategy=rules."
                ) from exc
        return self._encoder

    def score(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        query_input = "为这个句子生成表示以用于检索相关文章：" + query
        inputs = [query_input, *texts]
        missing = list(dict.fromkeys(text for text in inputs if text not in self._vectors))
        current = {text: self._vectors[text] for text in inputs if text in self._vectors}
        if missing:
            vectors = self._model().encode(missing, normalize_embeddings=True, show_progress_bar=False)
            if len(vectors) != len(missing):
                raise ValueError("Encoder returned a different number of vectors")
            current.update(zip(missing, vectors))
        # Keep current-call vectors separately so batches larger than the cache remain valid.
        for text in dict.fromkeys(inputs):
            self._vectors[text] = current[text]
            self._vectors.move_to_end(text)
            if len(self._vectors) > self.cache_size:
                self._vectors.popitem(last=False)
        query_vector = current[query_input]
        scores = []
        for text in texts:
            vector = current[text]
            if len(vector) != len(query_vector):
                raise ValueError("Embedding dimensions differ")
            value = sum(float(a) * float(b) for a, b in zip(query_vector, vector))
            if not math.isfinite(value) or not -1.00001 <= value <= 1.00001:
                raise ValueError("Encoder must return finite normalized embeddings")
            scores.append(max(-1.0, min(1.0, value)))
        return scores


@lru_cache(maxsize=1)
def default_bge_scorer() -> BgeScorer:
    return BgeScorer()


def _validated_similarity(value: float) -> float:
    if isinstance(value, (bool, str, bytes)):
        raise ValueError("Semantic scores must be finite cosine similarities")
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Semantic scores must be numeric") from exc
    if not math.isfinite(score) or not -1 <= score <= 1:
        raise ValueError("Semantic scores must be finite cosine similarities in [-1, 1]")
    return score


def score_organizations(query: str, evidence: list[dict], scorer: SemanticScorer) -> dict[str, dict]:
    """Batch score snippets, then average within and across available source families."""
    if not evidence:
        return {}
    scores = list(scorer.score(query, [item["text"] for item in evidence]))
    if len(scores) != len(evidence):
        raise ValueError("Semantic scorer returned a different number of scores")
    grouped = {}
    for item, score in zip(evidence, scores):
        grouped.setdefault(item["organization_id"], []).append({
            **item, "similarity": _validated_similarity(score),
        })
    results = {}
    for org_id, documents in grouped.items():
        families = {}
        for document in documents:
            families.setdefault(document["kind"], []).append(document["similarity"])
        results[org_id] = {
            "semantic_score": sum(sum(values) / len(values) for values in families.values()) / len(families),
            "semantic_evidence": sorted(documents, key=lambda doc: (-doc["similarity"], doc["record_id"]))[:3],
        }
    return results
