"""Integrity checks for the screenshot-aligned organization mock data."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from recommendation import DataValidationError, adapt_dataset
from scripts.generate_mock_data import build_mock_dataset


EXAMPLE = Path(__file__).resolve().parents[1] / "docs" / "recommendation-example.json"


class OrganizationSourceTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def assertInvalid(self, path, code):
        with self.assertRaises(DataValidationError) as caught:
            adapt_dataset(self.payload)
        self.assertIn((path, code), {(i.path, i.code) for i in caught.exception.issues})

    def test_fixture_matches_picture_counts_and_organization_links(self):
        data = adapt_dataset(self.payload).data
        self.assertTrue(data["dataset_info"]["is_mock"])
        self.assertEqual(len(data["organizations"]), 48)
        self.assertEqual(len(data["contacts"]), 200)
        self.assertEqual(len(data["consultant_notes"]), 20)
        self.assertEqual(len({n["organization_id"] for n in data["consultant_notes"]}), 14)
        self.assertEqual(len(data["task_cards"]), 2)
        self.assertNotIn("programs", data)
        self.assertNotIn("request", data)

    def test_fixture_is_reproducible_from_generator(self):
        self.assertEqual(build_mock_dataset(), self.payload)
        self.assertEqual(build_mock_dataset(), build_mock_dataset())

    def test_unknown_listing_field_and_sparse_histories_are_preserved(self):
        data = adapt_dataset(self.payload).data
        organizations = {o["organization_id"] for o in data["organizations"]}
        contacted = {c["organization_id"] for c in data["contacts"]}
        noted = {n["organization_id"] for n in data["consultant_notes"]}
        self.assertEqual(len(organizations - contacted), 6)
        self.assertTrue(noted - contacted)
        self.assertTrue(all(o["platform_listing_status"] is None for o in data["organizations"]))
        staff_counts = [o["full_time_staff_count"] for o in data["organizations"]]
        self.assertIn(0, staff_counts)
        self.assertIn(None, staff_counts)
        self.assertTrue(any(n["recorded_on"] is None for n in data["consultant_notes"]))
        self.assertTrue(any(c["free_text"] is None for c in data["contacts"]))

    def test_real_data_need_not_have_fixed_mock_counts(self):
        self.payload["dataset_info"]["is_mock"] = False
        self.payload["organizations"] = [{"organization_id": "actual-001", "name": "來源提供的名稱"}]
        for table in ("contacts", "consultant_notes", "task_cards"):
            del self.payload[table]
        data = adapt_dataset(self.payload).data
        self.assertEqual(len(data["organizations"]), 1)
        self.assertEqual(data["contacts"], [])
        self.assertIsNone(data["organizations"][0]["full_time_staff_count"])

    def test_each_related_table_rejects_orphan_organization_ids(self):
        original = deepcopy(self.payload)
        for table in ("contacts", "consultant_notes"):
            with self.subTest(table=table):
                self.payload = deepcopy(original)
                self.payload[table][0]["organization_id"] = "missing"
                self.assertInvalid(f"$.{table}[0].organization_id", "reference")

    def test_each_table_rejects_duplicate_record_ids(self):
        original = deepcopy(self.payload)
        for table, field in (("organizations", "organization_id"), ("contacts", "contact_id"),
                             ("consultant_notes", "note_id"), ("task_cards", "task_id")):
            with self.subTest(table=table):
                self.payload = deepcopy(original)
                self.payload[table][1][field] = self.payload[table][0][field]
                self.assertInvalid(f"$.{table}[1].{field}", "duplicate")

    def test_headcount_rejects_strings_booleans_fractions_and_negatives(self):
        for value in ("5", True, 1.5, -1):
            with self.subTest(value=value):
                self.payload["organizations"][0]["full_time_staff_count"] = value
                with self.assertRaises(DataValidationError):
                    adapt_dataset(self.payload)

    def test_dates_are_calendar_dates_and_do_not_exceed_snapshot(self):
        self.payload["contacts"][0]["date"] = "2026-02-30"
        self.assertInvalid("$.contacts[0].date", "invalid_value")
        self.payload["contacts"][0]["date"] = "2026-11-13"
        self.assertInvalid("$.contacts[0].date", "date_order")
        self.payload["contacts"][0]["date"] = None
        self.payload["consultant_notes"][0]["recorded_on"] = "2026-11-13"
        self.assertInvalid("$.consultant_notes[0].recorded_on", "date_order")

    def test_free_text_and_chinese_categories_are_kept_without_scoring(self):
        org = self.payload["organizations"][0]
        org["issue_tags"] = ["待確認的新議題"]
        self.payload["consultant_notes"][0]["note_text"] = "單次觀察仍待確認，不能判斷合作能力。"
        result = adapt_dataset(self.payload)
        self.assertEqual(result.data["organizations"][0]["issue_tags"], ["待確認的新議題"])
        self.assertEqual(result.data["consultant_notes"][0]["note_text"], self.payload["consultant_notes"][0]["note_text"])
        self.assertNotIn("score", result.data["organizations"][0])
        self.assertEqual(result.raw_data, self.payload)
        result.data["organizations"][0]["issue_tags"].append("新增")
        self.assertNotEqual(result.data["organizations"][0], result.raw_data["organizations"][0])

    def test_task_count_and_unknown_columns_are_checked(self):
        self.payload["task_cards"][0]["requested_organization_count"] = 0
        self.assertInvalid("$.task_cards[0].requested_organization_count", "range")
        self.payload["organizations"][0]["invented_score"] = 90
        self.assertInvalid("$.organizations[0].invented_score", "unknown_field")

    def test_command_line_recognizes_new_source_data(self):
        run = subprocess.run([sys.executable, "-m", "recommendation", str(EXAMPLE)],
                             cwd=EXAMPLE.parents[1], capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("48 organizations, 200 contacts, 20 notes for 14 organizations, 2 task cards", run.stdout)


if __name__ == "__main__":
    unittest.main()
