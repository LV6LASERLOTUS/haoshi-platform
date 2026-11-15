"""Validate an internal dataset: python -m recommendation path/to/data.json."""

import argparse
import json
from pathlib import Path

from . import BgeScorer, DataValidationError, adapt_dataset, recommend


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a v0.1/v0.2 dataset without loading BGE or OCR")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--request", type=Path, help="Structured request JSON; enables recommendation")
    parser.add_argument("--strategy", choices=("rules", "bge", "hybrid", "compare"), default="rules")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5", help="Local model ID or directory")
    parser.add_argument("--output", type=Path, help="Write recommendation JSON as UTF-8")
    args = parser.parse_args()
    if not args.request and (args.strategy != "rules" or args.output):
        parser.error("--request is required for recommendation options")
    try:
        payload = json.loads(args.dataset.read_text(encoding="utf-8"))
        result = adapt_dataset(payload)
        if args.request:
            query = json.loads(args.request.read_text(encoding="utf-8"))
            strategies = ("rules", "bge", "hybrid") if args.strategy == "compare" else (args.strategy,)
            scorer = BgeScorer(args.model) if args.strategy != "rules" else None
            reports = {mode: recommend(result.data, query, strategy=mode,
                                       top_k=args.top_k, semantic_scorer=scorer) for mode in strategies}
            report = reports if args.strategy == "compare" else reports[args.strategy]
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"Recommendation report written: {args.output}")
            else:
                print(json.dumps(report, ensure_ascii=True, indent=2))
            return 0
    except (OSError, ValueError, RuntimeError) as exc:
        if isinstance(exc, DataValidationError):
            for issue in exc.issues:
                print(f"{issue.path} [{issue.code}]: {issue.message}")
        else:
            print(str(exc))
        return 1
    data = result.data
    if data["schema_version"] == "0.2":
        noted = {note["organization_id"] for note in data["consultant_notes"]}
        print(f"Valid schema 0.2: {len(data['organizations'])} organizations, "
              f"{len(data['contacts'])} contacts, {len(data['consultant_notes'])} notes "
              f"for {len(noted)} organizations, {len(data['task_cards'])} task cards")
    else:
        print(f"Valid schema 0.1: {len(data['organizations'])} organizations, "
              f"{len(data['programs'])} programs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
