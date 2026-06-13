import unittest

from scripts.recipes.ahmedabad.build_library_access import summarize_ahmedabad_libraries
from scripts.recipes.delhi.build_library_access import summarize_delhi_libraries


class LibraryAccessAdaptersTest(unittest.TestCase):
    def test_summarize_ahmedabad_libraries_counts_coordinate_rows(self) -> None:
        rows = summarize_ahmedabad_libraries()

        self.assertEqual(rows[0]["city"], "ahmedabad")
        self.assertGreater(int(rows[0]["library_locations"]), 0)
        self.assertEqual(rows[0]["coordinate_coverage_status"], "complete")

    def test_summarize_delhi_libraries_separates_fixed_and_mobile_rows(self) -> None:
        rows = summarize_delhi_libraries()

        self.assertEqual(rows[0]["city"], "delhi")
        self.assertGreater(int(rows[0]["fixed_library_locations"]), 0)
        self.assertGreater(int(rows[0]["mobile_service_points"]), 0)
        self.assertEqual(rows[0]["access_status"], "geocoding_required")


if __name__ == "__main__":
    unittest.main()
