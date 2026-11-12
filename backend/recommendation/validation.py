"""Validate versioned recommendation data using only the standard library."""

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
import math
import re


@dataclass(frozen=True)
class DataIssue:
    path: str
    code: str
    message: str


class DataValidationError(ValueError):
    def __init__(self, issues: list[DataIssue]):
        self.issues = issues
        super().__init__("; ".join(f"{i.path}: {i.message}" for i in issues))


TAG_FIELDS = ("target_groups", "issue_tags", "activity_types", "cooperation_modes")
CONDITIONS = (*TAG_FIELDS, "location_codes", "budget", "event_dates",
              "beneficiary_count", "employee_volunteer_count")

# A ! suffix means the field is required and cannot be null.
REQUEST = {
    "id": "text!", "text": "text!", **dict.fromkeys(TAG_FIELDS, "tags"),
    "location_codes": "locations", "budget": "budget", "event_dates": "dates",
    "submitted_on": "date", "beneficiary_count": "count",
    "employee_volunteer_count": "count", "required_fields": "conditions",
}
ORGANIZATION = {
    "id": "text!", "name": "text!", "description": "text",
    "target_groups": "tags", "issue_tags": "tags",
    "service_location_codes": "locations", "source": "text", "updated_at": "timestamp",
}
PROGRAM = {
    "id": "text!", "organization_id": "text!", "name": "text!", "description": "text",
    **dict.fromkeys(TAG_FIELDS, "tags"), "service_location_codes": "locations",
    "cost": "cost", "max_beneficiaries": "count", "max_employee_volunteers": "count",
    "minimum_lead_days": "count", "available_dates": "dates",
    "availability_window": "window", "source": "text", "updated_at": "timestamp",
}
NESTED = {
    "budget": {"max_amount": "amount!", "currency": "currency!"},
    "cost": {"min_amount": "amount!", "max_amount": "amount!",
             "currency": "currency!", "includes_all_costs": "boolean"},
    "window": {"start": "date!", "end": "date!"},
}


class _Validator:
    def __init__(self):
        self.issues: list[DataIssue] = []

    def error(self, path, message, code="invalid_value"):
        self.issues.append(DataIssue(path, code, message))

    def object(self, value, schema, path):
        if not isinstance(value, dict):
            self.error(path, "Expected an object", "invalid_type")
            return {}
        for key in value.keys() - schema.keys():
            self.error(f"{path}.{key}", "Unknown field; map source fields in an adapter",
                       "unknown_field")
        result = {}
        for field, kind in schema.items():
            item = value.get(field)
            field_path = f"{path}.{field}"
            if item is None:
                if kind.endswith("!"):
                    self.error(field_path, "Field is required", "required")
                result[field] = [] if kind == "conditions" else None
            else:
                result[field] = self.value(item, kind.rstrip("!"), field_path)
        return result

    def value(self, value, kind, path):
        if kind in NESTED:
            return self.object(value, NESTED[kind], path)
        if kind in ("tags", "locations", "dates", "conditions", "texts"):
            if not isinstance(value, list):
                self.error(path, "Expected a list", "invalid_type")
                return value
            item_kind = {"tags": "tag", "locations": "location", "dates": "date",
                         "conditions": "condition", "texts": "text"}[kind]
            result = [self.value(v, item_kind, f"{path}[{i}]") for i, v in enumerate(value)]
            if all(isinstance(v, str) for v in result) and len(set(result)) != len(result):
                self.error(path, "Duplicate values are not allowed", "duplicate")
            return result
        if kind in ("count", "amount"):
            valid = type(value) is int if kind == "count" else type(value) in (int, float)
            if not valid:
                self.error(path, f"Expected a non-negative {'integer' if kind == 'count' else 'number'}",
                           "invalid_type")
            elif value < 0 or (type(value) is float and not math.isfinite(value)):
                self.error(path, "Must be finite and non-negative")
            return value
        if kind == "boolean":
            if type(value) is not bool:
                self.error(path, "Expected a boolean", "invalid_type")
            return value
        if not isinstance(value, str):
            self.error(path, "Expected a string", "invalid_type")
            return value
        value = value.strip()
        if not value:
            self.error(path, "Must not be blank; use null for unknown data")
            return value
        if kind == "date":
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    raise ValueError
                date.fromisoformat(value)
            except ValueError:
                self.error(path, "Expected a valid YYYY-MM-DD date")
        elif kind == "timestamp":
            try:
                if "T" not in value or datetime.fromisoformat(value).utcoffset() is None:
                    raise ValueError
            except ValueError:
                self.error(path, "Expected an ISO 8601 datetime with timezone")
        elif kind == "currency" and not re.fullmatch(r"[A-Z]{3}", value):
            self.error(path, "Expected a three-letter uppercase currency code")
        elif kind == "tag" and not re.fullmatch(r"[a-z][a-z0-9_]*", value):
            self.error(path, "Expected a stable lowercase tag code")
        elif kind == "location" and not re.fullmatch(r"TW-[A-Z0-9]{2,3}", value):
            self.error(path, "Expected an internal Taiwan region code, e.g. TW-CHA")
        elif kind == "condition" and value not in CONDITIONS:
            self.error(path, "Not a comparable request field")
        return value


def validate_dataset(payload: dict) -> dict:
    """Return a new v0.1 or v0.2 dataset or raise with field-level errors.

    This validates internal data only. Source aliases and integer IDs belong in adapters.
    Missing optional values become None; zero and empty lists remain explicit values.
    """
    if isinstance(payload, dict) and payload.get("schema_version") == "0.2":
        from .source_validation import validate_source_dataset

        return validate_source_dataset(payload)
    v = _Validator()
    if not isinstance(payload, dict):
        raise DataValidationError([DataIssue("$", "invalid_type", "Expected an object")])
    for key in payload.keys() - {"schema_version", "request", "organizations", "programs"}:
        v.error(f"$.{key}", "Unknown dataset field", "unknown_field")
    if payload.get("schema_version") != "0.1":
        v.error("$.schema_version", "Supported schema versions: 0.1, 0.2", "schema_version")
    result = {"schema_version": "0.1", "request": v.object(payload.get("request"), REQUEST, "$.request")}
    for key, schema in (("organizations", ORGANIZATION), ("programs", PROGRAM)):
        records = payload.get(key, [] if key == "programs" else None)
        if not isinstance(records, list):
            v.error(f"$.{key}", "Expected a list", "invalid_type")
            records = []
        result[key] = [v.object(record, schema, f"$.{key}[{i}]") for i, record in enumerate(records)]

    # Cross-field checks run only after structural values are safe to compare.
    if v.issues:
        raise DataValidationError(v.issues)
    request = result["request"]
    for field in request["required_fields"]:
        if request[field] is None or request[field] == []:
            v.error(f"$.request.required_fields", f"Required condition {field} has no value", "required")
    for i, event_date in enumerate(request["event_dates"] or []):
        if request["submitted_on"] and event_date < request["submitted_on"]:
            v.error(f"$.request.event_dates[{i}]", "Event precedes submission date", "date_order")

    for key in ("organizations", "programs"):
        seen = set()
        for i, record in enumerate(result[key]):
            if record["id"] in seen:
                v.error(f"$.{key}[{i}].id", "Duplicate ID", "duplicate")
            seen.add(record["id"])
    organization_ids = {record["id"] for record in result["organizations"]}
    for i, program in enumerate(result["programs"]):
        path = f"$.programs[{i}]"
        if program["organization_id"] not in organization_ids:
            v.error(f"{path}.organization_id", "Organization does not exist", "reference")
        cost = program["cost"]
        if cost and cost["min_amount"] > cost["max_amount"]:
            v.error(f"{path}.cost", "Minimum amount exceeds maximum amount", "range")
        window, dates = program["availability_window"], program["available_dates"]
        if (window is None) != (dates is None):
            v.error(f"{path}.available_dates", "Dates and availability window must be provided together", "paired_fields")
        elif window:
            if window["start"] > window["end"]:
                v.error(f"{path}.availability_window", "Start exceeds end", "date_order")
            for j, day in enumerate(dates):
                if not window["start"] <= day <= window["end"]:
                    v.error(f"{path}.available_dates[{j}]", "Date is outside the availability window", "range")
    if v.issues:
        raise DataValidationError(v.issues)
    return deepcopy(result)
