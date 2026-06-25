import unittest

from scripts.recipes.comparators.build_library_access_comparison import comparison_rows, pair_key


class LibraryAccessComparisonTest(unittest.TestCase):
    def test_pair_key_is_stable(self) -> None:
        self.assertEqual(pair_key("delhi", "toronto"), "delhi_toronto")
        self.assertEqual(pair_key("toronto", "ahmedabad"), "ahmedabad_toronto")

    def test_comparison_rows_mark_missing_city_summary(self) -> None:
        summaries = {
            "ahmedabad": {"city": "ahmedabad", "library_locations": "83", "access_status": "population_origins_required"},
            "delhi": {"city": "delhi", "library_locations": "111", "access_status": "geocoding_required"},
        }

        rows = comparison_rows(["ahmedabad", "delhi", "toronto"], summaries)

        self.assertEqual(rows[0]["pair"], "ahmedabad_delhi")
        self.assertEqual(rows[0]["comparison_status"], "available")
        self.assertEqual(rows[1]["pair"], "ahmedabad_toronto")
        self.assertEqual(rows[1]["comparison_status"], "missing_city_summary")


if __name__ == "__main__":
    unittest.main()
