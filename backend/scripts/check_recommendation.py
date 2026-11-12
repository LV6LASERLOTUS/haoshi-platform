"""Run recommendation checks without starting the app or contacting Google Sheets."""

import argparse
import json
from pathlib import Path
import sys
import unittest


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from recommendation import BgeScorer, recommend


def run_unit_tests(verbose: bool) -> unittest.TestResult:
    """Only collect our offline recommendation tests, not live Sheets/OCR tests."""
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(BACKEND / "tests"), pattern="test_recommendation*.py",
    )
    return unittest.TextTestRunner(verbosity=2 if verbose else 1, stream=sys.stdout).run(suite)


def run_examples(include_bge: bool, model_name: str) -> dict[str, dict]:
    """Use real rules and optionally real local BGE; never replace BGE with fake scores."""
    dataset = json.loads((BACKEND / "docs" / "recommendation-example.json").read_text(encoding="utf-8"))
    query = json.loads((BACKEND / "docs" / "recommendation-request-example.json").read_text(encoding="utf-8"))
    strategies = ("rules", "bge", "hybrid") if include_bge else ("rules",)
    scorer = BgeScorer(model_name) if include_bge else None
    return {mode: recommend(dataset, query, strategy=mode, semantic_scorer=scorer) for mode in strategies}


def print_recommendations(mode: str, report: dict, path: Path) -> None:
    """Show the returned names as well as the report location in the terminal."""
    matches = report["top_matches"]
    print(f"{mode}: {len(matches)} returned; counts={report['counts']}")
    for rank, candidate in enumerate(matches, 1):
        print(f"  {rank:>2}. [{candidate['organization_id']}] {candidate['name']}")
    if not matches:
        print("  No confirmed matches; check pending_matches and excluded in the report.")
    print(f"  JSON: {path.resolve()} (top_matches)")


def save_reports(reports: dict[str, dict], tests: unittest.TestResult, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    summary = {"unit_tests": {"run": tests.testsRun, "failures": len(tests.failures),
                              "errors": len(tests.errors)}, "strategies": {}}
    for mode, report in reports.items():
        path = directory / f"{mode}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        summary["strategies"][mode] = {
            "counts": report["counts"], "returned": len(report["top_matches"]),
            "semantic_document_count": report["semantic_document_count"],
            "elapsed_ms": report["elapsed_ms"], "report": path.name,
        }
        print_recommendations(mode, report, path)
    (directory / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8",
    )
    not_refreshed = [mode for mode in ("bge", "hybrid")
                     if mode not in reports and (directory / f"{mode}.json").exists()]
    if not_refreshed:
        print(f"Not run in this check: {', '.join(not_refreshed)}; existing JSON files were not refreshed.")
    print(f"Reports: {directory.resolve()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-bge", action="store_true", help="Also exercise the real local BGE model")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5", help="Local Chinese BGE model ID or directory")
    parser.add_argument("--report-dir", type=Path, default=BACKEND / ".cache" / "recommendation-check")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    tests = run_unit_tests(args.verbose)
    if not tests.wasSuccessful():
        return 1
    try:
        reports = run_examples(args.with_bge, args.model)
        save_reports(reports, tests, args.report_dir)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Recommendation check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
