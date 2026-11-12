"""Data intake for the independent recommendation strategy (no AI imports)."""

from .adapters import AdaptedData, adapt_dataset, adapt_legacy_npos
from .validation import DataIssue, DataValidationError, validate_dataset
from .engine import recommend
from .matching import validate_request
from .semantic import BgeScorer, SemanticScorer, SemanticUnavailableError

__all__ = [
    "AdaptedData", "DataIssue", "DataValidationError", "adapt_dataset",
    "adapt_legacy_npos", "validate_dataset", "recommend", "validate_request",
    "BgeScorer", "SemanticScorer", "SemanticUnavailableError",
]
