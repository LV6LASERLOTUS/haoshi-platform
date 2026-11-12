"""Build bounded, traceable text snippets without loading or scoring a model."""


MAX_TEXT_CHARS = 240
MAX_CONTACTS = 3
MAX_NOTES = 2


def _index_by_organization(records: list[dict]) -> dict[str, list[dict]]:
    index = {}
    for record in records:
        index.setdefault(record["organization_id"], []).append(record)
    return index


def _recent_records(records: list[dict], *, date_field: str, id_field: str, limit: int) -> list[dict]:
    """Unknown dates sort after dated observations, with deterministic ties."""
    return sorted(records, key=lambda row: (row[date_field] or "", row[id_field]), reverse=True)[:limit]


def _snippet(organization_id: str, kind: str, record_id: str, text: str,
             source: str | None, recorded_on: str | None) -> dict:
    return {
        "organization_id": organization_id,
        "kind": kind,
        "record_id": record_id,
        "source": source,
        "date": recorded_on,
        "text": text[:MAX_TEXT_CHARS],
    }


def build_evidence(data: dict, organization_ids: set[str]) -> list[dict]:
    """One profile, latest three contacts and latest two notes per candidate.

    Call after validating the dataset. Encode snippets separately so history is
    not appended to one long profile and silently lost to model truncation.
    """
    contacts = _index_by_organization(data["contacts"])
    notes = _index_by_organization(data["consultant_notes"])
    evidence = []
    for org in data["organizations"]:
        org_id = org["organization_id"]
        if org_id not in organization_ids:
            continue
        profile = "；".join(
            f"{label}：{'、'.join(org[field])}"
            for field, label in (("issue_tags", "議題"), ("target_groups", "服務對象"), ("regions", "區域"))
            if org[field]
        )
        if profile:
            evidence.append(_snippet(org_id, "profile", org_id, profile, org["source"], None))
        contact_records = [record for record in contacts.get(org_id, [])
                           if record["activity_name"] or record["free_text"]]
        for record in _recent_records(contact_records, date_field="date", id_field="contact_id", limit=MAX_CONTACTS):
            text = "；".join(part for part in (
                record["contact_type"], record["activity_name"], record["free_text"],
            ) if part)
            evidence.append(_snippet(org_id, "contact", record["contact_id"], text, record["source"], record["date"]))
        for record in _recent_records(notes.get(org_id, []), date_field="recorded_on", id_field="note_id", limit=MAX_NOTES):
            evidence.append(_snippet(org_id, "consultant_note", record["note_id"],
                                     record["note_text"], record["source"], record["recorded_on"]))
    return evidence
