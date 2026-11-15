"""Pure scoring and eligibility rules; BGE is injected, never replaced by mock data."""

import math
import re
from datetime import date
from typing import Protocol

from .evidence import normalize
from .policy import (CONFIRMATION_TRUST_THRESHOLD, COVERAGE_THRESHOLD,
                     EVIDENCE_HALF_LIFE_DAYS, RESOURCES, SEMANTIC_REFERENCE_LIMIT,
                     UNDATED_EVIDENCE_TRUST, UNKNOWN_BASELINE, VERSION)
from .schemas import Demand, EligibilityCheck, Evidence, Organization, Plan, Recommendation, Subscore


class SemanticScorer(Protocol):
    def similarity(self, query: str, passage: str) -> float: ...


class SemanticUnavailableError(RuntimeError):
    pass


def unknown(reason: str, evidence_ids=()) -> Subscore:
    return Subscore(state="Unknown", reason=reason, evidence_ids=list(evidence_ids))


def known(score: float, reason: str, evidence_ids=(), cosine=None, method="rule") -> Subscore:
    return Subscore(state="Known", score=score, reason=reason,
                    evidence_ids=list(evidence_ids), raw_cosine=cosine, method=method)


def _semantic(scorer: SemanticScorer, query: str, passage: str, ids) -> Subscore:
    raw = float(scorer.similarity(query, passage))
    if not math.isfinite(raw):
        raise SemanticUnavailableError("BGE 回傳非有限數值，不能產生推薦指數。")
    raw = max(-1.0, min(1.0, raw))
    return known(100 * max(0.0, raw), "BGE cosine 暫定轉換；未經人工校準，不能解讀為成功率。", ids, raw, "bge")


def usable(evidence: Evidence, as_of: date) -> bool:
    """Search all historical years; future event dates still require correction."""
    return (evidence.source_kind != "profile"
            and (evidence.event_date is None or evidence.event_date <= as_of))


def temporal_trust(evidence: Evidence, as_of: date) -> float:
    """Recency reference weight, not a probability that a statement is true."""
    if evidence.source_kind == "profile":
        return 1.0  # No historical discount; does NOT verify profile freshness.
    if evidence.event_date is None:
        return UNDATED_EVIDENCE_TRUST
    age = (as_of - evidence.event_date).days
    return 2 ** (-age / EVIDENCE_HALF_LIFE_DAYS) if age >= 0 else 0.0


def _annotate_trust(subscores: dict[str, Subscore], organization: Organization, as_of: date):
    by_id = {e.evidence_id: e for e in organization.evidence}
    for sub in subscores.values():
        if sub.state != "Known":
            continue
        sources = [by_id[eid] for eid in sub.evidence_ids if eid in by_id]
        if not sources:
            sub.evidence_trust = 0.0
            continue
        if sub.method == "bge" and len(sources) > 1:
            sub.evidence_trust = sum(temporal_trust(e, as_of) for e in sources) / len(sources)
            if all(e.source_kind != "profile" and e.event_date is not None for e in sources):
                sub.evidence_age_days = round(sum((as_of - e.event_date).days for e in sources) / len(sources))
            continue
        source = max(sources, key=lambda e: temporal_trust(e, as_of))
        sub.evidence_trust = temporal_trust(source, as_of)
        if source.source_kind != "profile" and source.event_date is not None:
            sub.evidence_age_days = (as_of - source.event_date).days


def _profile(organization: Organization, field: str) -> tuple[str, list[str]]:
    value = organization.profile.get(field, "").strip()
    if normalize(value) in {"", "未提供", "未知", "不詳", "n/a", "-", "—"}:
        return "", []
    return value, [e.evidence_id for e in organization.evidence
                   if e.source_kind == "profile" and e.event_name == field]


def resource_rules(key: str, demand: Demand):
    if key == "other":
        return {"label": "、".join(demand.custom_resource_terms), "direct": tuple(demand.custom_resource_terms), "adjacent": (), "weak": ()}
    return RESOURCES[key]


def _mentions(text: str, terms) -> bool:
    value = normalize(text)
    return any(normalize(term) in value for term in terms)


def _need_grade(evidence: Evidence, rules) -> int | None:
    text = normalize(evidence.quote)
    tentative = bool(re.search(r"可能|應該|可以考慮|先觀察|建議", text))
    # Only explicit, scoped absence of a direct resource is a negative need claim.
    for term in rules["direct"]:
        token = re.escape(normalize(term))
        if re.search(r"(?:不需要|無需|暫不需要|目前不需要)(?:任何)?" + token, text):
            return None if tentative else 0
        if re.search(r"沒有" + token + r"(?:的)?(?:協助)?需求", text):
            return None if tentative else 0
    if re.search(r"不想|不希望|無意|不是要|並非|沒有想|不需要學|暫不想", text):
        return None
    # 'No chance to apply this' is not 'no need', and role titles alone are not needs.
    if not re.search(r"需要|想學|想把|想用|想先|想建立|想加強|希望|不足|缺乏|待加強|不知道|想了解|想導入|想設定|想進一步", text):
        return None
    for field, grade in (("direct", 100), ("adjacent", 70), ("weak", 40)):
        if _mentions(text, rules[field]):
            if tentative:
                grade = min(40, grade)
            if evidence.source_kind == "consultant_note" or "審查委員" in text or "外部公開資訊" in text:
                grade = min(70, grade)
            return grade
    return None


def score_resource(key: str, organization: Organization, demand: Demand,
                   scorer: SemanticScorer, as_of: date) -> tuple[dict[str, Subscore], list[Evidence]]:
    rules = resource_rules(key, demand)
    history = [e for e in organization.evidence if usable(e, as_of)]
    # Search every meaningful historical clause first, including negative claims.
    # Deduplicate identical text across dates before BGE; keep its freshest source.
    references = {}
    for e in sorted(history, key=lambda e: (-temporal_trust(e, as_of), e.evidence_id)):
        text = normalize(e.quote)
        if len(text) >= 4 and text not in {"出席", "委託出席", "每月一次陪跑會議", "外部公開資訊"}:
            references.setdefault(text, e)
    query = f"需要{rules['label']}的協助與支持"
    retrieved = {text: _semantic(scorer, query, e.quote, [e.evidence_id]) for text, e in references.items()}

    # Apply intent, negation and conflict rules only AFTER semantic retrieval.
    # Scan all history, so a negative outside the top passages is not missed.
    candidates = [(grade, e) for e in history
                  if (grade := _need_grade(e, rules)) is not None]
    positive = [(grade, e) for grade, e in candidates if grade > 0]
    negative = [e for grade, e in candidates if grade == 0]
    if positive and negative:
        ids = [e.evidence_id for _, e in positive] + [e.evidence_id for e in negative]
        result = unknown("同類資源有需求與無需求證據衝突，需人工確認，不以最新一句自動覆蓋。", ids)
        return {"semantic": result, "explicit": result}, []
    if negative:
        ids = [e.evidence_id for e in negative]
        result = known(0, "有效原文明確表示沒有此類資源需求；語意高分不得抵銷。", ids)
        raw = [retrieved[normalize(e.quote)].raw_cosine for e in negative if normalize(e.quote) in retrieved]
        override = known(0, "BGE 已搜尋原文；明確無需求規則覆寫整個資源構面，相似度不能抵銷否定。",
                         ids, cosine=max(raw) if raw else None, method="rule_override")
        return {"semantic": override, "explicit": result}, []

    def aggregate(pool, reason):
        distinct = {}
        for e in sorted(pool, key=lambda e: (-temporal_trust(e, as_of), e.evidence_id)):
            text = normalize(e.quote)
            if text in retrieved:
                distinct.setdefault(text, e)
        ordered = sorted(distinct.items(), key=lambda item: (
            -retrieved[item[0]].raw_cosine, -temporal_trust(item[1], as_of), item[1].evidence_id))
        top = ordered[:SEMANTIC_REFERENCE_LIMIT]
        if not top:
            return unknown("沒有可供語意比對的歷史片段。")
        raw = sum(retrieved[text].raw_cosine for text, _ in top) / len(top)
        return known(100 * max(0.0, raw), reason, [e.evidence_id for _, e in top], raw, "bge")

    pool = [e for e in references.values()
            if not re.search(r"不想|不希望|無意|不是要|並非|沒有想|不需要|無需|不同意", e.quote)]
    if not positive:
        semantic = aggregate(pool, "BGE 全歷史搜尋後取最多三段平均；僅為語意參考，不確認資源需求或意願。")
        return {"semantic": semantic,
                "explicit": unknown("詞表未確認同類需求；保留語意參考候選，需人工確認。", semantic.evidence_ids)}, []
    # Rules confirm explicit need separately; BGE orders the supporting passages.
    positive.sort(key=lambda item: (-item[0] * temporal_trust(item[1], as_of), -item[0], item[1].evidence_id))
    grade, selected = positive[0]
    ids = [selected.evidence_id]
    return {
        "semantic": aggregate(pool, "BGE 全歷史搜尋後取最多三段 cosine 平均；明確需求由獨立規則確認，尚未人工校準。"),
        "explicit": known(grade, f"{rules['label']}需求證據規則；只使用可追溯原文。", ids),
    }, [e for _, e in positive]


def _plan_participation(organization: Organization, demand: Demand, as_of: date) -> Subscore:
    if not demand.plan_name:
        return unknown("未提供本次計畫名稱，不能把歷史參與當作本次意願。")
    positive, negative = [], []
    for e in organization.evidence:
        if not usable(e, as_of) or normalize(demand.plan_name) not in normalize(e.event_name + e.original_text):
            continue
        text = normalize(e.quote)
        # A speculative consultant observation is never a confirmed plan commitment.
        if e.source_kind == "consultant_note" or re.search(r"可能|應該|建議|先觀察", text):
            continue
        if re.search(r"確認(?:拒絕|不參加|不參與)|明確拒絕參加|確認無法參加|確認無法參與", text):
            negative.append(e.evidence_id)
        elif re.search(r"確認(?:願意|可以|能|可)?(?:參加|參與)|已確認報名", text):
            positive.append(e.evidence_id)
    if positive and negative:
        return unknown("本次計畫參與證據衝突。", positive + negative)
    if negative:
        return known(0, "明確確認不參加本次計畫。", negative)
    if positive:
        return known(100, "原文確認參加本次計畫。", positive)
    return unknown("未記載本次計畫的明確參與確認。")


def _time(organization: Organization, demand: Demand, as_of: date) -> Subscore:
    if not demand.period or not demand.plan_name:
        return unknown("缺少本次計畫名稱或指定起訖日期。")
    positive, negative = [], []
    for e in organization.evidence:
        context = e.event_name + e.original_text
        if not usable(e, as_of) or normalize(demand.plan_name) not in normalize(context):
            continue
        dates_present = all(any(token in context for token in (value.isoformat(), value.strftime('%Y/%m/%d')))
                            for value in (demand.period.start, demand.period.end))
        text = normalize(e.quote)
        if not dates_present or e.source_kind == "consultant_note" or re.search(r"可能|應該|建議", text):
            continue
        if re.search(r"確認(?:期間|時間)?(?:無法|不能|不可)(?:全程)?參(?:加|與)", text):
            negative.append(e.evidence_id)
        elif re.search(r"確認(?:期間|時間)?(?:可|可以|能)(?:全程)?參(?:加|與)", text):
            positive.append(e.evidence_id)
    if positive and negative:
        return unknown("指定期間的可參與證據衝突。", positive + negative)
    if negative:
        return known(0, "明確確認不能參加指定起訖期間。", negative)
    if positive:
        return known(100, "明確確認可參加指定起訖期間；未推論其他投入條件。", positive)
    return unknown("沒有指定起訖期間的明確可參與確認，其他計畫或歷史出席不能代替。")


def _readiness(organization: Organization, demand: Demand, as_of: date, participation: Subscore) -> Subscore:
    if participation.state == "Known":
        return participation
    if participation.evidence_ids:
        return participation  # Preserve conflicts instead of falling back to historic actions.
    terms = tuple(term for key in demand.resources for field in ("direct", "adjacent")
                  for term in resource_rules(key, demand)[field])
    for e in sorted(organization.evidence, key=lambda e: (-temporal_trust(e, as_of), e.evidence_id)):
        if usable(e, as_of) and _mentions(e.event_name + e.original_text, terms):
            if re.search(r"已開始試做|已導入|已經在下次會議提出|課後有帶回組織分享|準時交功課|整個團隊都在用", e.quote):
                return known(60, "有相關改善行動，尚未確認本次參與；未以接觸筆數加分。", [e.evidence_id])
    return unknown("未找到獨立的相關改善行動或本次參與確認；想學不重複當動機加分。")


def score_profile(dimension: str, organization: Organization, demand: Demand) -> Subscore:
    if dimension == "size":
        value, ids = _profile(organization, "全職人數")
        if not re.fullmatch(r"\d+", value):
            return unknown("全職人數缺漏或不是有效非負整數，不推測規模。")
        count = int(value)
        fits = (demand.staff_min is None or count >= demand.staff_min) and (demand.staff_max is None or count <= demand.staff_max)
        return known(100 if fits else 0, "依企業明確人數區間比對主檔；人數不代表能力，主檔未提供更新日期。", ids)
    field, wanted = {
        "issue": ("議題", demand.issues), "target": ("服務對象", demand.target_groups),
        "area": ("區域", demand.areas), "membership": ("會籍", demand.memberships),
    }[dimension]
    if dimension == "area" and demand.area_basis != "registered_area":
        return unknown("區域主檔不等於完整可服務範圍，不能推論跨區能力。")
    value, ids = _profile(organization, field)
    if not value:
        return unknown(f"{field}缺少可用資料。")
    values = [normalize(v) for v in re.split(r"[、,，;/；]", value)]
    matched = any(normalize(term) in values for term in wanted)
    return known(100 if matched else 0, f"比對主檔{field}的明確分類，不作模糊能力推論。", ids)


def summarize(subscores: dict[str, Subscore], weights: dict[str, float]):
    """Impute ONLY totals; unknown leaf scores remain None in the public response."""
    coverage = sum(w for key, w in weights.items() if subscores[key].state == "Known")
    coverage = min(1.0, max(0.0, coverage))
    contribution = sum(w * subscores[key].score for key, w in weights.items() if subscores[key].state == "Known")
    u = 1 - coverage
    return (contribution + UNKNOWN_BASELINE * u, coverage,
            contribution / coverage if coverage else None, (contribution, contribution + 100 * u))


def score_organization(organization: Organization, demand: Demand, plan: Plan,
                       scorer: SemanticScorer, as_of: date, snapshot_at: str) -> Recommendation:
    subscores, weights, warnings = {}, {}, ["BGE 轉換與 Unknown=30 均為暫定政策，分數不是合作成功率。"]
    resource_results = {}
    if "resource_need" in plan.weights or "resource_need" in demand.required_conditions:
        for key in demand.resources:
            resource_results[key], _ = score_resource(key, organization, demand, scorer, as_of)
        if demand.resource_mode == "any":
            selected = max(resource_results, key=lambda key: (summarize(resource_results[key], {"semantic": .6, "explicit": .4})[0], key))
            active_resources = [selected]
        else:
            active_resources = list(resource_results)
        for key in active_resources:
            for feature, score in resource_results[key].items():
                name = f"resource_need.{key}.{feature}"
                subscores[name] = score
                if "resource_need" in plan.weights:
                    weights[name] = plan.weights["resource_need"] * (.6 if feature == "semantic" else .4) / len(active_resources)

    if "semantic" in plan.weights:
        fields = ("一句話簡介", "議題", "服務對象")
        passages = [_profile(organization, f) for f in fields]
        text = "；".join(value for value, _ in passages if value)
        ids = [eid for _, evidence_ids in passages for eid in evidence_ids]
        query = "公益合作議題：" + "、".join(demand.issues) + "；服務對象：" + "、".join(demand.target_groups)
        subscores["semantic"] = _semantic(scorer, query, text, ids) if text else unknown("缺少服務內容描述。")

    participation = _plan_participation(organization, demand, as_of)
    if "participation" in demand.required_conditions:
        subscores["participation"] = participation
    for key in plan.weights.keys() | set(demand.required_conditions):
        if key in {"size", "issue", "target", "area", "membership"}:
            subscores[key] = score_profile(key, organization, demand)
        elif key == "time":
            subscores[key] = _time(organization, demand, as_of)
        elif key == "readiness":
            subscores[key] = _readiness(organization, demand, as_of, participation)
    weights.update({key: weight for key, weight in plan.weights.items() if key != "resource_need"})

    # Temporal trust changes ranking confidence, never the original cosine or
    # the recorded evidence score. Unknown scores remain None.
    _annotate_trust(subscores, organization, as_of)
    for results in resource_results.values():
        _annotate_trust(results, organization, as_of)
    eligibility = {}
    for key in demand.required_conditions:
        if key == "resource_need":
            explicit = [resource_results[r]["explicit"] for r in resource_results]
            pos = [s for s in explicit if s.state == "Known" and s.score == 100
                   and (s.evidence_trust or 0) >= CONFIRMATION_TRUST_THRESHOLD]
            neg = [s for s in explicit if s.state == "Known" and s.score == 0
                   and (s.evidence_trust or 0) >= CONFIRMATION_TRUST_THRESHOLD]
            if (demand.resource_mode == "any" and pos) or (demand.resource_mode == "all" and len(pos) == len(explicit)):
                status = "Eligible"
            elif (demand.resource_mode == "any" and len(neg) == len(explicit)) or (demand.resource_mode == "all" and neg):
                status = "Ineligible"
            else:
                status = "Unverified"
            eligibility[key] = EligibilityCheck(status=status, reason="必要資源條件需明確且時效信任度足夠的需求／無需求證據；較舊、相鄰及缺漏保持待確認。",
                                                evidence_ids=list(dict.fromkeys(eid for s in explicit for eid in s.evidence_ids)))
        else:
            sub = subscores[key]
            status = "Unverified" if sub.state != "Known" else "Eligible" if sub.score > 0 else "Ineligible"
            if sub.state == "Known" and (sub.evidence_trust or 0) < CONFIRMATION_TRUST_THRESHOLD:
                status = "Unverified"
            # A primary issue/target is not an exhaustive statement of all services.
            if key in {"issue", "target"} and status == "Ineligible":
                status = "Unverified"
            eligibility[key] = EligibilityCheck(status=status, reason=sub.reason, evidence_ids=sub.evidence_ids)
    eligibility_status = "Ineligible" if any(c.status == "Ineligible" for c in eligibility.values()) else "Unverified" if any(c.status == "Unverified" for c in eligibility.values()) else "Eligible"
    score, coverage, known_mean, bounds = summarize(subscores, weights)
    trusted_coverage = min(1.0, sum(w * (subscores[k].evidence_trust or 0)
                                  for k, w in weights.items() if subscores[k].state == "Known"))
    evidence_trust = trusted_coverage / coverage if coverage else 0.0
    trusted_contribution = sum(w * sub.score * (sub.evidence_trust or 0)
                               for k, w in weights.items() if (sub := subscores[k]).state == "Known")
    ranking_score = trusted_contribution + UNKNOWN_BASELINE * (1 - trusted_coverage)
    core_names = [k for k in weights if k.startswith("resource_need.") or k == "semantic"]
    core_known = bool(core_names) and all(subscores[k].state == "Known" for k in core_names)
    core_zero = core_known and all(subscores[k].score == 0 for k in core_names)
    core_trust = min((subscores[k].evidence_trust or 0 for k in core_names if subscores[k].state == "Known"), default=0)
    core_semantic = any(subscores[k].state == "Known" and subscores[k].method == "bge" for k in core_names)
    status = "review_candidate"
    if eligibility_status == "Ineligible":
        status = "ineligible"
    elif coverage == 0:
        status = "insufficient_evidence"
    elif core_known and core_trust < CONFIRMATION_TRUST_THRESHOLD:
        status = "historical_candidate"
    elif core_zero:
        status = "core_mismatch"
    elif not core_known and core_semantic:
        status = "semantic_candidate"
    elif not core_known or eligibility_status == "Unverified":
        status = "needs_verification"
    verification_required = (coverage < COVERAGE_THRESHOLD or evidence_trust < CONFIRMATION_TRUST_THRESHOLD
                             or not core_known or eligibility_status == "Unverified"
                             or any(sub.state == "Unknown" for sub in subscores.values()))
    if coverage < COVERAGE_THRESHOLD:
        warnings.append("證據覆蓋率低於 60%，保留候選並提示補確認，不因覆蓋率單獨擋掉。")
    if evidence_trust < CONFIRMATION_TRUST_THRESHOLD and coverage:
        warnings.append("有歷史參考證據，但時間信任度較低；需確認現況，舊紀錄不直接證明目前符合或不符合。")
    if status == "review_candidate":
        warnings.append("證據覆蓋率達標不代表已確認適合；此為候選評估排序。")
    if "size" in subscores:
        warnings.append("主檔人數未提供資料更新日期，不能代表目前承接能力。")
    if any(e.source_kind != "profile" and e.event_date is None for e in organization.evidence):
        warnings.append("部分歷史缺少有效日期，以較低時間信任度參考，不能直接確認必要條件。")
    if any(e.source_kind != "profile" and not usable(e, as_of) for e in organization.evidence):
        warnings.append("部分紀錄日期在未來，需修正後才能使用。")
    ids = {eid for sub in subscores.values() for eid in sub.evidence_ids}
    ids.update(eid for check in eligibility.values() for eid in check.evidence_ids)
    sources = [e for e in organization.evidence if e.evidence_id in ids]
    missing = [f"{key}：{sub.reason}" for key, sub in subscores.items() if sub.state == "Unknown"]
    reasons = [f"{key}：{sub.reason}" for key, sub in subscores.items() if sub.state == "Known"]
    # Surface disabled dimensions explicitly without giving them fake scores.
    for key in plan.inactive_dimensions:
        if key not in subscores:
            subscores[key] = Subscore(state="Not Required", reason="本次需求未啟用，不計入權重。")
    return Recommendation(
        npo_id=organization.npo_id, npo_name=organization.name, match_score=round(score, 2),
        known_score=round(known_mean, 2) if known_mean is not None else None,
        score_range=(round(bounds[0], 2), round(bounds[1], 2)), subscores=subscores,
        evidence_coverage=round(coverage, 6), scoring_status=status,
        evidence_trust=round(evidence_trust, 6), trusted_evidence_coverage=round(trusted_coverage, 6),
        ranking_score=round(max(0.0, min(100.0, ranking_score)), 2), verification_required=verification_required,
        eligibility_status=eligibility_status, eligibility_checks=eligibility, weights_used=weights,
        recommendation_reasons=reasons, source_evidence=sources, warnings=warnings,
        missing_information=missing, scoring_version=VERSION, data_snapshot_at=snapshot_at,
    )
