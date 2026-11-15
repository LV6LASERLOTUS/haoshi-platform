"""Basic integrity checks for screenshot-aligned v0.2 source data; no scoring."""

from copy import deepcopy

from .validation import DataValidationError, _Validator


INFO = {"is_mock": "boolean!", "as_of_date": "date!", "description": "text"}
ORGANIZATION = {
    "organization_id": "text!", "name": "text!", "issue_tags": "texts",
    "target_groups": "texts", "regions": "texts", "membership_status": "text",
    "full_time_staff_count": "count", "financial_report_type": "text",
    "platform_listing_status": "text", "support_tier": "text", "source": "text",
}
CONTACT = {
    "contact_id": "text!", "organization_id": "text!", "date": "date",
    "contact_type": "text", "activity_name": "text", "participant_roles": "texts",
    "free_text": "text", "source": "text",
}
NOTE = {
    "note_id": "text!", "organization_id": "text!", "recorded_on": "date",
    "author_role": "text", "note_text": "text!", "source": "text",
}
TASK = {
    "task_id": "text!", "title": "text!", "scenario": "text!", "user_role": "text",
    "questions": "texts", "requested_organization_count": "count",
}
TABLES = {
    "organizations": (ORGANIZATION, "organization_id"),
    "contacts": (CONTACT, "contact_id"),
    "consultant_notes": (NOTE, "note_id"),
    "task_cards": (TASK, "task_id"),
}


def validate_source_dataset(payload: dict) -> dict:
    v = _Validator()
    for key in payload.keys() - {"schema_version", "dataset_info", *TABLES}:
        v.error(f"$.{key}", "Unknown dataset field", "unknown_field")
    result = {
        "schema_version": "0.2",
        "dataset_info": v.object(payload.get("dataset_info"), INFO, "$.dataset_info"),
    }
    for table, (schema, _) in TABLES.items():
        rows = payload.get(table, [] if table != "organizations" else None)
        if not isinstance(rows, list):
            v.error(f"$.{table}", "Expected a list", "invalid_type")
            rows = []
        result[table] = [v.object(row, schema, f"$.{table}[{i}]") for i, row in enumerate(rows)]
    if v.issues:
        raise DataValidationError(v.issues)

    for table, (_, identifier) in TABLES.items():
        seen = set()
        for i, row in enumerate(result[table]):
            if row[identifier] in seen:
                v.error(f"$.{table}[{i}].{identifier}", "Duplicate ID", "duplicate")
            seen.add(row[identifier])

    organization_ids = {row["organization_id"] for row in result["organizations"]}
    as_of = result["dataset_info"]["as_of_date"]
    for table, date_field in (("contacts", "date"), ("consultant_notes", "recorded_on")):
        for i, row in enumerate(result[table]):
            if row["organization_id"] not in organization_ids:
                v.error(f"$.{table}[{i}].organization_id", "Organization does not exist", "reference")
            if row[date_field] and row[date_field] > as_of:
                v.error(f"$.{table}[{i}].{date_field}", "Record date exceeds dataset as-of date", "date_order")
    for i, task in enumerate(result["task_cards"]):
        if task["requested_organization_count"] == 0:
            v.error(f"$.task_cards[{i}].requested_organization_count", "Requested count must be positive or unknown", "range")
    if v.issues:
        raise DataValidationError(v.issues)
    return deepcopy(result)
