"""Source preserving ingestion. Summary/AI input columns never become evidence."""

import hashlib
import re
import unicodedata
from datetime import date
from urllib.parse import quote

from .policy import PROFILE_COLUMNS
from .schemas import Evidence, Organization, Snapshot


class DataSourceError(RuntimeError):
    """The source is unavailable or cannot be interpreted safely."""


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(text))).replace("臺", "台").casefold()


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip().replace("/", "-"))
    except ValueError:
        return None


def _records(values: list[list[str]], required: set[str], sheet_name: str):
    if not values:
        raise DataSourceError(f"{sheet_name} 缺少表頭。")
    headers = [h.strip() for h in values[0]]
    if len(headers) != len(set(headers)) or not required <= set(headers):
        raise DataSourceError(f"{sheet_name} 表頭缺漏或重複。")
    for row_number, row in enumerate(values[1:], start=2):
        if any(str(value).strip() for value in row):
            yield row_number, {h: str(row[i]).strip() if i < len(row) else "" for i, h in enumerate(headers)}


def _url(base: str, sheet_id: int, row: int) -> str:
    return f"{base.split('/edit')[0]}/edit#gid={sheet_id}&range={quote(f'A{row}:Z{row}')}"


def _clauses(text: str):
    start = 0
    for boundary in [*re.finditer(r"[。！？；;\n，,]|但是|不過|但", text), None]:
        end = boundary.start() if boundary else len(text)
        raw = text[start:end]
        clause = raw.strip()
        if clause:
            offset = start + len(raw) - len(raw.lstrip())
            yield offset, offset + len(clause), clause
        if boundary:
            start = boundary.end()


def build_snapshot(tables: dict[str, list[list[str]]], sheet_ids: dict[str, int],
                   spreadsheet_url: str, captured_at: str) -> Snapshot:
    """Pure ingestion function, usable with real Sheets or explicit test fixtures."""
    required_sheets = {"NPO_dim", "②接觸紀錄", "③顧問筆記"}
    if not required_sheets <= tables.keys():
        raise DataSourceError("需要 NPO_dim、②接觸紀錄、③顧問筆記 三張工作表。")
    organizations, warnings = {}, []
    for row, record in _records(tables["NPO_dim"], {"組織編號", "組織名稱", "一句話簡介", "議題", "服務對象", "區域", "全職人數", "會籍"}, "NPO_dim"):
        npo_id = record["組織編號"]
        if not npo_id or not record["組織名稱"]:
            raise DataSourceError(f"NPO_dim 第 {row} 列缺少組織編號或名稱。")
        if npo_id in organizations:
            raise DataSourceError(f"NPO_dim 組織編號重複：{npo_id}。")
        profile = {key: record.get(key, "") for key in PROFILE_COLUMNS}
        evidence = []
        for key, value in profile.items():
            if value:
                evidence.append(Evidence(
                    evidence_id=f"{npo_id}:profile:{key}", npo_id=npo_id,
                    source_sheet="NPO_dim", source_record_id=npo_id,
                    source_url=_url(spreadsheet_url, sheet_ids["NPO_dim"], row), row=row,
                    source_kind="profile", quote=value, original_text=value, end=len(value), event_name=key,
                ))
        organizations[npo_id] = Organization(npo_id=npo_id, name=record["組織名稱"], profile=profile, evidence=evidence)
    if not organizations:
        raise DataSourceError("NPO_dim 沒有可評分組織，不能以模擬資料代替。")

    seen_records, seen_clauses = set(), set()
    sources = (
        ("②接觸紀錄", "留下的話／紀錄內容", "contact_record", {"紀錄編號", "組織編號", "日期", "活動或事件名稱", "留下的話／紀錄內容"}),
        ("③顧問筆記", "筆記", "consultant_note", {"組織編號", "日期", "記錄者", "筆記"}),
    )
    for sheet, text_key, source_kind, required in sources:
        for row, record in _records(tables[sheet], required, sheet):
            text, npo_id = record[text_key], record["組織編號"]
            if not text:
                continue  # Includes the explanatory footer in the consultant sheet.
            if npo_id not in organizations:
                warnings.append(f"{sheet} 第 {row} 列缺少有效組織編號，未使用；需要人工確認關聯。")
                continue
            event_date = parse_date(record["日期"])
            if event_date is None:
                warnings.append(f"{sheet} 第 {row} 列日期無法解析，保留為低信任度參考，不能確認必要條件。")
            record_id = record.get("紀錄編號") or "note-" + hashlib.sha256(
                f"{npo_id}|{record['日期']}|{record.get('記錄者', '')}|{text}".encode()
            ).hexdigest()[:20]
            record_key = (sheet, record_id)
            if record_key in seen_records:
                raise DataSourceError(f"{sheet} 有重複來源識別：{record_id}。")
            seen_records.add(record_key)
            for start, end, clause in _clauses(text):
                if not clause or clause.startswith(("目前沒有接觸歷史", "目前沒有顧問筆記")):
                    continue
                key = (npo_id, event_date, normalize(clause))
                if key in seen_clauses:
                    continue
                seen_clauses.add(key)
                # Keep offsets into the original source, not into a generated summary.
                organizations[npo_id].evidence.append(Evidence(
                    evidence_id=f"{sheet}:{record_id}:{start}:{end}",
                    npo_id=npo_id, source_sheet=sheet, source_record_id=record_id,
                    source_url=_url(spreadsheet_url, sheet_ids[sheet], row), row=row,
                    event_date=event_date, event_name=record.get("活動或事件名稱", ""),
                    source_kind=source_kind, quote=clause, original_text=text,
                    start=start, end=end,
                ))
    return Snapshot(captured_at=captured_at, organizations=list(organizations.values()), warnings=warnings)
