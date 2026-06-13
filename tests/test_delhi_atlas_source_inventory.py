import unittest

from scripts.recipes.delhi.build_atlas_source_inventory import (
    classify_dataset,
    delhi_candidate,
    flatten_inventory_rows,
    shortlist_flag,
)


class DelhiAtlasSourceInventoryTest(unittest.TestCase):
    def test_delhi_candidate_matches_group_name_or_title(self) -> None:
        self.assertTrue(delhi_candidate({"groups": ["delhi"], "title": "Municipal Corporation Budget"}))
        self.assertTrue(delhi_candidate({"groups": [], "title": "Delhi Road Crashes Data", "name": "road-crashes"}))
        self.assertTrue(delhi_candidate({"groups": [], "title": "Road Crashes", "name": "delhi-road-crashes-data"}))
        self.assertFalse(delhi_candidate({"groups": ["bengaluru"], "title": "Bengaluru Budget"}))

    def test_classify_dataset_marks_budget_as_pays(self) -> None:
        dataset = {
            "title": "Municipal Corporation of Delhi Budget 2025-26",
            "tags": [],
            "notes": "",
            "organization": "government-of-delhi",
            "name": "municipal-corporation-of-delhi-budget-2025-26",
        }

        self.assertIn("pays", classify_dataset(dataset))

    def test_shortlist_prioritizes_structured_boundary_budget_and_transport(self) -> None:
        budget = {
            "title": "Municipal Corporation of Delhi Budget 2025-26",
            "resources": [{"format": "PDF"}],
            "axis_labels": ["pays"],
        }
        boundary = {
            "title": "Villages Maps of Delhi",
            "resources": [{"format": "GEOJSON"}],
            "axis_labels": ["base"],
        }
        culture = {
            "title": "Delhi Cultural Events Brochure",
            "resources": [{"format": "PDF"}],
            "axis_labels": [],
        }

        self.assertTrue(shortlist_flag(budget))
        self.assertTrue(shortlist_flag(boundary))
        self.assertFalse(shortlist_flag(culture))

    def test_flatten_inventory_rows_preserves_resource_metadata(self) -> None:
        dataset = {
            "name": "delhi-test",
            "title": "Delhi Test",
            "url": "https://data.opencity.in/dataset/delhi-test",
            "organization": "government-of-delhi",
            "groups": ["delhi"],
            "tags": ["budget"],
            "metadata_modified": "2026-01-01T00:00:00",
            "axis_labels": ["pays"],
            "shortlist": True,
            "resources": [
                {
                    "id": "r1",
                    "name": "CSV",
                    "format": "CSV",
                    "url": "https://example.test/file.csv",
                    "size_bytes": 123,
                    "last_modified": "2026-01-02T00:00:00",
                    "mimetype": "text/csv",
                }
            ],
        }

        rows = flatten_inventory_rows([dataset])

        self.assertEqual(rows[0]["dataset_name"], "delhi-test")
        self.assertEqual(rows[0]["resource_format"], "CSV")
        self.assertEqual(rows[0]["axis_labels"], "pays")
        self.assertEqual(rows[0]["shortlist"], "1")


if __name__ == "__main__":
    unittest.main()
