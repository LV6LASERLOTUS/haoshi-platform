"""Data-boundary regression tests; no AI models, credentials or network required."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from recommendation import DataValidationError, adapt_dataset, adapt_legacy_npos


EXAMPLE = Path(__file__).resolve().parents[1] / "docs" / "recommendation-example-v0.1.json"


class RecommendationDataTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def assertInvalid(self, payload, path, code=None):
        with self.assertRaises(DataValidationError) as caught:
            adapt_dataset(payload)
        matches = [issue for issue in caught.exception.issues if issue.path == path]
        self.assertTrue(matches, caught.exception.issues)
        if code:
            self.assertIn(code, [issue.code for issue in matches])

    def test_documented_example_is_accepted_without_inventing_capabilities(self):
        result = adapt_dataset(self.payload)
        self.assertIsNone(result.data["organizations"][1]["target_groups"])
        self.assertIsNone(result.data["programs"][0]["max_employee_volunteers"])
        self.assertIsNone(result.data["programs"][0]["available_dates"])
        self.assertEqual(result.raw_data, self.payload)

    def test_minimal_data_defaults_optional_fields_to_unknown(self):
        data = adapt_dataset({
            "schema_version": "0.1", "request": {"id": "r1", "text": "教育合作"},
            "organizations": [{"id": "o1", "name": "組織"}],
        }).data
        self.assertIsNone(data["request"]["submitted_on"])
        self.assertEqual(data["request"]["required_fields"], [])
        self.assertIsNone(data["organizations"][0]["service_location_codes"])
        self.assertEqual(data["programs"], [])

    def test_unknown_empty_and_zero_remain_distinct(self):
        program = self.payload["programs"][0]
        program["cooperation_modes"] = []
        program["max_employee_volunteers"] = 0
        result = adapt_dataset(self.payload).data["programs"][0]
        self.assertEqual(result["cooperation_modes"], [])
        self.assertEqual(result["max_employee_volunteers"], 0)
        self.assertIsNone(result["available_dates"])

    def test_result_and_raw_data_are_detached_from_input_and_each_other(self):
        original = deepcopy(self.payload)
        result = adapt_dataset(self.payload)
        result.data["request"]["target_groups"].append("older_adults")
        self.assertEqual(self.payload, original)
        self.assertEqual(result.raw_data, original)
        self.payload["organizations"][0]["name"] = "changed"
        self.assertNotEqual(result.raw_data, self.payload)

    def test_whitespace_is_trimmed_without_changing_raw_data(self):
        self.payload["organizations"][0]["name"] = "  協會  "
        result = adapt_dataset(self.payload)
        self.assertEqual(result.data["organizations"][0]["name"], "協會")
        self.assertEqual(result.raw_data["organizations"][0]["name"], "  協會  ")

    def test_invalid_numeric_values_are_not_coerced_or_replaced_with_zero(self):
        for value in (-1, True, "40", 2.5, float("nan"), float("inf")):
            with self.subTest(value=value):
                payload = deepcopy(self.payload)
                payload["request"]["beneficiary_count"] = value
                self.assertInvalid(payload, "$.request.beneficiary_count")
        for value in (-1, True, "15 萬", float("nan"), float("inf")):
            with self.subTest(amount=value):
                payload = deepcopy(self.payload)
                payload["request"]["budget"]["max_amount"] = value
                self.assertInvalid(payload, "$.request.budget.max_amount")

    def test_required_condition_cannot_be_missing_empty_or_noncomparable(self):
        for value in (None, []):
            with self.subTest(value=value):
                payload = deepcopy(self.payload)
                payload["request"]["target_groups"] = value
                self.assertInvalid(payload, "$.request.required_fields", "required")
        self.payload["request"]["required_fields"] = ["text"]
        self.assertInvalid(self.payload, "$.request.required_fields[0]")

    def test_zero_is_a_valid_explicit_required_condition(self):
        self.payload["request"]["employee_volunteer_count"] = 0
        self.payload["request"]["required_fields"] = ["employee_volunteer_count"]
        self.assertEqual(adapt_dataset(self.payload).data["request"]["employee_volunteer_count"], 0)

    def test_date_format_calendar_and_submission_order_are_validated(self):
        for value in ("2027-02-30", "20270116", "2027-1-16", "2027-01-16T00:00:00"):
            with self.subTest(value=value):
                payload = deepcopy(self.payload)
                payload["request"]["event_dates"] = [value]
                self.assertInvalid(payload, "$.request.event_dates[0]")
        self.payload["request"]["event_dates"] = ["2026-11-10"]
        self.assertInvalid(self.payload, "$.request.event_dates[0]", "date_order")

    def test_availability_requires_a_window_and_dates_within_it(self):
        self.payload["programs"][0]["available_dates"] = []
        self.assertInvalid(self.payload, "$.programs[0].available_dates", "paired_fields")
        self.payload["programs"][0]["availability_window"] = {"start": "2027-01-01", "end": "2027-01-31"}
        self.assertEqual(adapt_dataset(self.payload).data["programs"][0]["available_dates"], [])
        self.payload["programs"][0]["available_dates"] = ["2027-02-01"]
        self.assertInvalid(self.payload, "$.programs[0].available_dates[0]", "range")
        self.payload["programs"][0]["available_dates"] = []
        self.payload["programs"][0]["availability_window"] = {"start": "2027-02-01", "end": "2027-01-31"}
        self.assertInvalid(self.payload, "$.programs[0].availability_window", "date_order")

    def test_cost_bounds_and_cost_inclusion_type(self):
        self.payload["programs"][0]["cost"]["min_amount"] = 200000
        self.assertInvalid(self.payload, "$.programs[0].cost", "range")
        self.payload["programs"][0]["cost"]["includes_all_costs"] = "false"
        self.assertInvalid(self.payload, "$.programs[0].cost.includes_all_costs", "invalid_type")

    def test_broken_organization_reference_and_duplicate_ids(self):
        self.payload["programs"][0]["organization_id"] = "missing"
        self.assertInvalid(self.payload, "$.programs[0].organization_id", "reference")
        self.payload["organizations"][1]["id"] = "npo-demo-001"
        self.assertInvalid(self.payload, "$.organizations[1].id", "duplicate")
        self.payload["programs"].append(deepcopy(self.payload["programs"][0]))
        self.assertInvalid(self.payload, "$.programs[1].id", "duplicate")

    def test_timestamp_requires_timezone(self):
        self.payload["organizations"][0]["updated_at"] = "2026-11-11T09:00:00"
        self.assertInvalid(self.payload, "$.organizations[0].updated_at")
        self.payload["organizations"][0]["updated_at"] += "+08:00"
        adapt_dataset(self.payload)

    def test_unknown_fields_and_versions_are_not_silently_discarded(self):
        self.payload["request"]["buget"] = 10000
        self.assertInvalid(self.payload, "$.request.buget", "unknown_field")
        self.payload["schema_version"] = "9.9"
        self.assertInvalid(self.payload, "$.schema_version", "schema_version")

    def test_labels_and_duplicates_are_rejected_at_internal_boundary(self):
        for field, value in (("target_groups", ["兒童"]), ("location_codes", ["彰化"]),
                             ("target_groups", ["children", "children"])):
            with self.subTest(field=field, value=value):
                payload = deepcopy(self.payload)
                payload["request"][field] = value
                with self.assertRaises(DataValidationError):
                    adapt_dataset(payload)

    def test_legacy_rows_convert_ids_and_preserve_unmapped_columns(self):
        rows = [{"id": 1, "name": "彰化偏鄉協會", "focus": "教育", "budget": "待確認"}]
        before = deepcopy(rows)
        result = adapt_legacy_npos(rows, {"id": "r1", "text": "教育"}, source="sheet:test")
        org = result.data["organizations"][0]
        self.assertEqual(org["id"], "1")
        self.assertEqual(org["description"], "教育")
        self.assertEqual(org["source"], "sheet:test")
        self.assertIsNone(org["service_location_codes"])
        self.assertIsNone(org["updated_at"])
        self.assertEqual(result.data["programs"], [])
        self.assertEqual(result.raw_data["rows"], before)
        self.assertEqual(rows, before)
        self.assertEqual({w.code for w in result.warnings}, {"limited_data", "unmapped_fields"})

    def test_renamed_source_columns_only_require_mapping_changes(self):
        result = adapt_legacy_npos(
            [{"編號": 12, "單位": "協會", "簡介": "  "}],
            {"id": "r1", "text": "教育"},
            field_mapping={"id": "編號", "name": "單位", "description": "簡介"},
        )
        self.assertEqual(result.data["organizations"][0]["id"], "12")
        self.assertIsNone(result.data["organizations"][0]["description"])

    def test_legacy_validation_errors_reference_source_columns(self):
        with self.assertRaises(DataValidationError) as caught:
            adapt_legacy_npos([{"編號": True, "單位": ""}], {"id": "r", "text": "教育"},
                              field_mapping={"id": "編號", "name": "單位"})
        paths = {issue.path for issue in caught.exception.issues}
        self.assertIn("$.rows[0].編號", paths)
        self.assertIn("$.rows[0].單位", paths)

    def test_legacy_id_collision_after_normalization_is_rejected(self):
        with self.assertRaises(DataValidationError) as caught:
            adapt_legacy_npos([{"id": 1, "name": "甲"}, {"id": " 1 ", "name": "乙"}],
                              {"id": "r", "text": "教育"})
        self.assertIn("duplicate", {issue.code for issue in caught.exception.issues})

    def test_bad_mapping_and_bad_rows_are_reported(self):
        for mapping in ({"unknown": "x"}, {"id": ""}, {"id": "name"}):
            with self.subTest(mapping=mapping), self.assertRaises(DataValidationError):
                adapt_legacy_npos([], {"id": "r", "text": "教育"}, field_mapping=mapping)
        with self.assertRaises(DataValidationError) as caught:
            adapt_legacy_npos([None], {"id": "r", "text": "教育"})
        self.assertEqual(caught.exception.issues[0].path, "$.rows[0]")

    def test_nonobjects_and_bad_collections_return_field_errors(self):
        for payload in (None, [], "data"):
            with self.subTest(payload=payload):
                self.assertInvalid(payload, "$", "invalid_type")
        for field in ("organizations", "programs"):
            payload = deepcopy(self.payload)
            payload[field] = {}
            self.assertInvalid(payload, f"$.{field}", "invalid_type")

    def test_command_line_reports_success_and_invalid_data_exit_code(self):
        backend = EXAMPLE.parents[1]
        valid = subprocess.run(
            [sys.executable, "-m", "recommendation", str(EXAMPLE)],
            cwd=backend, capture_output=True, text=True, check=False,
        )
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertIn("2 organizations, 1 programs", valid.stdout)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text('{"schema_version": "unsupported"}', encoding="utf-8")
            invalid = subprocess.run(
                [sys.executable, "-m", "recommendation", str(path)],
                cwd=backend, capture_output=True, text=True, check=False,
            )
        self.assertEqual(invalid.returncode, 1, invalid.stderr)
        self.assertIn("$.schema_version [schema_version]", invalid.stdout)
        self.assertNotIn("Traceback", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
