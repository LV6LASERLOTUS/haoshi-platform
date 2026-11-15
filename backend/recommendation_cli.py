"""Conda-friendly local entry point. Reads Sheets, never writes NGO data."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from recommendation.demand import build_plan
from recommendation.evidence import DataSourceError
from recommendation.schemas import Demand
from recommendation.scoring import SemanticUnavailableError


def format_summary(output):
    if output.status == "needs_clarification":
        return "需要補充需求：\n" + "\n".join(output.plan.clarification_questions)
    labels = {
        "review_candidate": "候選待評估", "historical_candidate": "歷史參考需更新",
        "semantic_candidate": "語意參考待確認", "needs_verification": "待確認",
        "core_mismatch": "核心需求不符", "insufficient_evidence": "證據不足", "ineligible": "不符合必要條件",
    }
    lines = [f"本次列出 {len(output.recommendations)} 家／可保留 {output.available_candidates} 家；排除 {len(output.excluded)} 家。",
             "ID | 名稱 | 契合分 | 排序分 | 覆蓋率 | 時間信任 | 狀態"]
    for item in output.recommendations:
        lines.append(f"{item.npo_id} | {item.npo_name} | {item.match_score:.2f} | {item.ranking_score:.2f} | "
                     f"{item.evidence_coverage:.0%} | {item.evidence_trust:.0%} | {labels[item.scoring_status]}")
    lines.append("時間信任是資料新鮮度參考，不是正確率；歷史／語意候選須確認目前需求與意願。")
    for message in output.warnings:
        lines.append("提醒：" + message)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="CSR–NGO 推薦 V1")
    parser.add_argument("request", type=Path, help="企業需求 JSON 檔案")
    parser.add_argument("--plan-only", action="store_true", help="只預覽規則與權重，不連線、不載入模型")
    parser.add_argument("--summary", action="store_true", help="顯示易讀候選摘要，包含時間信任與排序分")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        demand = Demand.model_validate_json(args.request.read_text(encoding="utf-8-sig"))
        plan = build_plan(demand)
        if args.plan_only:
            output = plan
        elif plan.clarification_questions:
            from recommendation.schemas import RecommendationResponse

            output = RecommendationResponse(status="needs_clarification", plan=plan)
        else:
            from database import load_recommendation_snapshot
            from recommendation.service import recommend

            output = recommend(demand, load_recommendation_snapshot())
        if args.summary and not args.plan_only:
            print(format_summary(output))
        else:
            print(json.dumps(output.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValidationError, DataSourceError, SemanticUnavailableError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
