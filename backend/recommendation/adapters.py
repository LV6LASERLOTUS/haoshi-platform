"""Source conversion with raw-data preservation and explicit diagnostics."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from .validation import DataIssue, DataValidationError, validate_dataset


@dataclass(frozen=True)
class AdaptedData:
    data: dict
    raw_data: Any
    warnings: tuple[DataIssue, ...]


def adapt_dataset(payload: dict) -> AdaptedData:
    """Accept a versioned dataset without guessing missing capabilities."""
    data = validate_dataset(payload)
    return AdaptedData(data, deepcopy(payload), ())


def adapt_legacy_npos(
    rows: list[dict],
    request: dict,
    *,
    field_mapping: Mapping[str, str] | None = None,
    source: str | None = None,
) -> AdaptedData:
    """Convert existing id/name/focus rows, including Google Sheets records.

    Mapping keys are internal names (id, name, description), values are source columns.
    Only these three fields are imported; all other source data is retained in raw_data.
    Extended capabilities need an explicit adapter, not guesses from organization names.
    """
    mapping = {"id": "id", "name": "name", "description": "focus"}
    if field_mapping is not None:
        unknown = set(field_mapping) - mapping.keys()
        if unknown:
            raise DataValidationError([
                DataIssue(f"$.field_mapping.{key}", "unknown_field", "Unsupported internal field")
                for key in sorted(unknown)
            ])
        mapping.update(field_mapping)
    for key, column in mapping.items():
        if not isinstance(column, str) or not column.strip():
            raise DataValidationError([DataIssue(f"$.field_mapping.{key}", "invalid_type", "Expected a non-empty source column name")])
    if len(set(mapping.values())) != len(mapping):
        raise DataValidationError([DataIssue("$.field_mapping", "duplicate", "Source columns must be distinct")])
    if not isinstance(rows, list):
        raise DataValidationError([DataIssue("$.rows", "invalid_type", "Expected a list of source rows")])
    organizations = []
    warnings = []
    errors = []
    for i, row in enumerate(rows):
        path = f"$.rows[{i}]"
        if not isinstance(row, dict):
            errors.append(DataIssue(path, "invalid_type", "Expected an object"))
            continue
        org = {target: row.get(column) for target, column in mapping.items()}
        if type(org["id"]) is int:
            org["id"] = str(org["id"])
        # Empty spreadsheet cells are unknown only for the optional description.
        if isinstance(org["description"], str) and not org["description"].strip():
            org["description"] = None
        org["source"] = source
        organizations.append(org)
        warnings.append(DataIssue(path, "limited_data", "Only organization identity and description were imported; capabilities and programs remain unknown"))
        ignored = sorted(set(row) - set(mapping.values()))
        if ignored:
            warnings.append(DataIssue(path, "unmapped_fields", f"Unmapped source fields retained in raw_data: {', '.join(ignored)}"))
    if errors:
        raise DataValidationError(errors)
    payload = {"schema_version": "0.1", "request": deepcopy(request),
               "organizations": organizations, "programs": []}
    try:
        data = validate_dataset(payload)
    except DataValidationError as exc:
        # Report legacy organization errors against the source row and source column.
        issues = []
        for issue in exc.issues:
            path = issue.path.replace("$.organizations[", "$.rows[")
            if path.startswith("$.rows["):
                prefix, field = path.rsplit(".", 1)
                path = f"{prefix}.{mapping.get(field, field)}"
            issues.append(DataIssue(path, issue.code, issue.message))
        raise DataValidationError(issues) from exc
    return AdaptedData(data, deepcopy({"request": request, "rows": rows}), tuple(warnings))
