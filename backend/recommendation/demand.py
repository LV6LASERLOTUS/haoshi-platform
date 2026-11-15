"""Conservative planning: explicit structured inputs win; prose is not a constraint."""

from .policy import DIMENSIONS, OPTIONAL_WEIGHTS, RESOURCES, TEMPLATES
from .schemas import Demand, Plan


def build_plan(demand: Demand) -> Plan:
    questions, warnings = [], []
    kind = demand.demand_type
    if kind is None:
        if demand.resources and all(r in {"marketing", "finance", "digital", "impact"} for r in demand.resources):
            kind = "professional_resources"
        elif demand.resources and set(demand.resources) <= {"funding", "materials"}:
            kind = "resource_support"
        elif demand.resources == ["volunteers"]:
            kind = "volunteering"
        elif not demand.resources and (demand.issues or demand.target_groups):
            kind = "issue_collaboration"
        else:
            questions.append("請指定需求型態；混合資源需明確選擇本次主要型態。")
    unknown_keys = sorted(set(demand.resources) - RESOURCES.keys())
    if unknown_keys:
        questions.append(f"未知資源代碼：{', '.join(unknown_keys)}。")
    if "other" in demand.resources and not demand.custom_resource_terms:
        questions.append("other 資源需提供明確 custom_resource_terms。")
    if demand.resource_direction != "offer_to_ngo":
        questions.append("V1 資源需求規則針對企業提供資源；尋找 NGO 提供服務需另定能力證據規則。")
    if kind and kind != "issue_collaboration" and not demand.resources:
        questions.append("請用 resources 指定企業提供的資源，不能從 ESG 報告用途推論。")
    if kind == "issue_collaboration" and not (demand.issues or demand.target_groups):
        questions.append("議題型合作需指定 issues 或 target_groups，避免整段企業用途污染語意查詢。")

    specified = {
        "resource_need": bool(demand.resources), "readiness": bool(demand.resources),
        "semantic": kind == "issue_collaboration", "issue": bool(demand.issues),
        "target": bool(demand.target_groups), "area": bool(demand.areas),
        "size": demand.staff_min is not None or demand.staff_max is not None,
        "membership": bool(demand.memberships), "time": demand.period is not None,
        "participation": bool(demand.plan_name),
    }
    for required in demand.required_conditions:
        if not specified[required]:
            questions.append(f"必要條件 {required} 尚未提供對應需求。")
        if required in {"time", "participation"} and not demand.plan_name:
            questions.append(f"必要條件 {required} 需提供 plan_name 才能辨識本次計畫。")
        if required in {"readiness", "semantic"}:
            questions.append(f"{required} 為排序特徵，請改用明確必要條件，例如 participation 或 resource_need。")
    if demand.period and not demand.plan_name:
        warnings.append("未提供 plan_name，時間無法對應本次計畫，將保持 Unknown。")
    if demand.areas and demand.area_basis == "service_area":
        warnings.append("現有區域欄位未確認完整服務範圍；service_area 保持 Unknown，不能以所在地排除。")
    if "半年" in demand.description and not demand.period:
        questions.append("需求提到半年，但尚未提供 period 起訖日期。")
    # Other dates/numbers in prose are not silently extracted into hard constraints.
    warnings.append("V1 以結構化欄位為準；描述中的期間、規模、限制與 ESG 用途不會自行變成 NGO 條件。")
    template = TEMPLATES.get(kind, {})
    raw = {k: v for k, v in template.items() if specified[k]}
    for key, weight in OPTIONAL_WEIGHTS.items():
        if specified[key] and key not in raw:
            raw[key] = weight
    # The professional template retains time as an unresolved request, not Not Required,
    # when the period was mentioned but not specified: clarification stops execution.
    total = sum(raw.values())
    weights = {k: v / total for k, v in raw.items()} if total else {}
    return Plan(demand_type=kind, weights=weights,
                inactive_dimensions=[d for d in DIMENSIONS if d not in weights],
                clarification_questions=list(dict.fromkeys(questions)), warnings=warnings,
                candidate_limit=demand.candidate_limit or min(max(30, 3 * demand.target_count), 500))
