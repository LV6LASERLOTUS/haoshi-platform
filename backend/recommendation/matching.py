"""Explicit request conditions and explainable matching against organization facts."""

from copy import deepcopy
import math

from .validation import DataIssue, DataValidationError, _Validator


LIST_FIELDS = {"issue_tags", "target_groups", "regions"}
CATEGORY_FIELDS = {"membership_status", "financial_report_type", "support_tier"}
MATCH_FIELDS = LIST_FIELDS | CATEGORY_FIELDS | {"full_time_staff_count"}


def validate_request(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise DataValidationError([DataIssue("$.request", "invalid_type", "Expected an object")])
    v = _Validator()
    request = v.object({key: value for key, value in payload.items() if key != "criteria"}, {
        "request_id": "text!", "text": "text!",
    }, "$.request")
    # Criteria have field-dependent value types and are checked separately.
    if v.issues:
        raise DataValidationError(v.issues)
    criteria = payload.get("criteria", [])
    if criteria is None:
        criteria = []
    if not isinstance(criteria, list):
        v.error("$.request.criteria", "Expected a list", "invalid_type")
        raise DataValidationError(v.issues)
    normalized = []
    seen = set()
    for i, criterion in enumerate(criteria):
        path = f"$.request.criteria[{i}]"
        if not isinstance(criterion, dict):
            v.error(path, "Expected an object", "invalid_type")
            continue
        for key in criterion.keys() - {"field", "operator", "value", "required", "weight"}:
            v.error(f"{path}.{key}", "Unknown criterion field", "unknown_field")
        field, operator = criterion.get("field"), criterion.get("operator")
        if not isinstance(field, str) or field not in MATCH_FIELDS:
            v.error(f"{path}.field", "Unsupported or unconfirmed organization field")
            continue
        if field in seen:
            v.error(f"{path}.field", "Only one criterion per field is allowed", "duplicate")
        seen.add(field)
        operators = {"any_of", "all_of"} if field in LIST_FIELDS else {"one_of"}
        if field == "full_time_staff_count":
            operators = {"between"}
        if not isinstance(operator, str) or operator not in operators:
            v.error(f"{path}.operator", f"Allowed operators: {', '.join(sorted(operators))}")
            continue
        before = len(v.issues)
        value = criterion.get("value")
        if operator == "between":
            if not isinstance(value, list) or len(value) != 2:
                v.error(f"{path}.value", "Expected inclusive [minimum, maximum]")
            else:
                value = [v.value(item, "count", f"{path}.value[{j}]") for j, item in enumerate(value)]
                if len(v.issues) == before and value[0] > value[1]:
                    v.error(f"{path}.value", "Minimum exceeds maximum", "range")
        else:
            value = v.value(value, "texts", f"{path}.value")
            if value == []:
                v.error(f"{path}.value", "Criterion must contain at least one requested value")
        required = criterion.get("required", False)
        v.value(required, "boolean", f"{path}.required")
        weight = criterion.get("weight", 1.0)
        try:
            valid_weight = type(weight) in (int, float) and math.isfinite(weight) and weight > 0
        except OverflowError:
            valid_weight = False
        if not valid_weight:
            v.error(f"{path}.weight", "Weight must be a finite positive number")
        normalized.append({"field": field, "operator": operator, "value": value,
                           "required": required, "weight": weight})
    if v.issues:
        raise DataValidationError(v.issues)
    request["criteria"] = normalized
    return deepcopy(request)


def match_organization(organization: dict, criteria: list[dict]) -> dict:
    """Keep unknown facts distinct from mismatches; hard conditions control eligibility."""
    details = []
    for criterion in criteria:
        field = criterion["field"]
        actual, expected = organization[field], criterion["value"]
        score = None
        if actual is not None:
            operator = criterion["operator"]
            if operator == "between":
                score = float(expected[0] <= actual <= expected[1])
            elif operator == "one_of":
                score = float(actual in expected)
            else:
                hits = len(set(actual) & set(expected))
                score = float(hits > 0) if operator == "any_of" else hits / len(expected)
        status = ("unknown" if score is None else "matched" if score == 1
                  else "mismatched" if score == 0 else "partial")
        reasons = {"unknown": "主檔未提供此欄位，需確認。", "matched": "主檔符合指定條件。",
                   "mismatched": "主檔不符合指定條件。", "partial": "主檔僅涵蓋部分指定條件。"}
        details.append({**criterion, "actual": deepcopy(actual), "status": status, "score": score,
                        "reason": reasons[status], "evidence": {
                            "table": "organizations", "record_id": organization["organization_id"],
                            "field": field, "value": deepcopy(actual), "source": organization["source"],
                        }})
    required = [detail for detail in details if detail["required"]]
    eligibility = "eligible"
    if any(detail["status"] == "mismatched" for detail in required):
        eligibility = "excluded"
    elif any(detail["status"] != "matched" for detail in required):
        eligibility = "needs_confirmation"
    scale = max((detail["weight"] for detail in details), default=1)
    total_weight = sum(detail["weight"] / scale for detail in details)
    known = [detail for detail in details if detail["score"] is not None]
    known_weight = sum(detail["weight"] / scale for detail in known)
    support = sum((detail["weight"] / scale) * detail["score"] for detail in known)
    return {
        "eligibility": eligibility, "criteria": details,
        "rule_score": support / known_weight if known_weight else None,
        "coverage": known_weight / total_weight if total_weight else None,
        "rule_support": support / total_weight if known_weight and total_weight else None,
    }
