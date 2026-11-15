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


def main():
    parser = argparse.ArgumentParser(description="CSR–NGO 推薦 V1")
    parser.add_argument("request", type=Path, help="企業需求 JSON 檔案")
    parser.add_argument("--plan-only", action="store_true", help="只預覽規則與權重，不連線、不載入模型")
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
        print(json.dumps(output.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValidationError, DataSourceError, SemanticUnavailableError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
