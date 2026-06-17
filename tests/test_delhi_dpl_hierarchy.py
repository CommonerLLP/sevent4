import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.recipes.delhi.build_dpl_hierarchy import (
    classify_service_tier,
    hierarchy_rows,
    summarize_hierarchy,
)


class DelhiDplHierarchyTest(unittest.TestCase):
    def test_classify_service_tier_separates_dpl_hierarchy(self) -> None:
        self.assertEqual(classify_service_tier({"name": "DPL Head Quarter", "location_type": "fixed_library"}), "headquarters")
        self.assertEqual(classify_service_tier({"name": "Shahdara", "location_type": "zonal_library"}), "zonal_library")
        self.assertEqual(classify_service_tier({"name": "Braille Library", "location_type": "fixed_library"}), "special_fixed_library")
        self.assertEqual(classify_service_tier({"name": "Kalyan Puri", "location_type": "fixed_library"}), "branch_library")
        self.assertEqual(classify_service_tier({"name": "Narela", "location_type": "sub_branch_library"}), "sub_branch_library")
        self.assertEqual(classify_service_tier({"name": "Mobile Service Point 001", "location_type": "mobile_service_point"}), "mobile_service_point")

    def test_hierarchy_rows_merge_google_assisted_coordinates_and_rank_tiers(self) -> None:
        source_rows = [
            {
                "library_id": "dpl_hq",
                "name": "DPL Head Quarter",
                "location_type": "fixed_library",
                "zone": "central",
                "address": "Delhi Public Library, Delhi",
                "latitude": "28.1",
                "longitude": "77.1",
                "geocode_status": "verified_coordinates",
            },
            {
                "library_id": "dpl_mobile",
                "name": "Mobile Service Point 001",
                "location_type": "mobile_service_point",
                "zone": "mobile",
                "address": "Mayur Vihar, Delhi",
                "latitude": "",
                "longitude": "",
                "geocode_status": "needs_geocode",
            },
        ]
        geocoded_rows = [
            {
                "library_id": "dpl_hq",
                "latitude": "28.1",
                "longitude": "77.1",
                "geocode_confidence": "verified",
                "geocode_provider": "google_maps_embed",
            },
            {
                "library_id": "dpl_mobile",
                "latitude": "28.2",
                "longitude": "77.2",
                "geocode_confidence": "google_approx",
                "geocode_provider": "google:APPROXIMATE",
            },
        ]

        rows = hierarchy_rows(source_rows, geocoded_rows)

        self.assertEqual(rows[0]["service_tier"], "headquarters")
        self.assertEqual(rows[0]["hierarchy_rank"], "10")
        self.assertEqual(rows[0]["physical_access_model"], "fixed_full_service")
        self.assertEqual(rows[1]["service_tier"], "mobile_service_point")
        self.assertEqual(rows[1]["hierarchy_rank"], "60")
        self.assertEqual(rows[1]["coordinate_provenance_group"], "google_geocode")
        self.assertEqual(rows[1]["usable_for_internal_access_model"], "yes")
        self.assertEqual(rows[0]["max_seating_capacity"], "")
        self.assertEqual(rows[0]["opening_hours"], "")
        self.assertEqual(rows[0]["weekly_open_hours"], "")
        self.assertEqual(rows[0]["branch_collection_size"], "")
        self.assertEqual(rows[0]["collection_types"], "")
        self.assertEqual(rows[0]["branch_detail_status"], "missing_branchwise_public_detail")

    def test_summary_counts_real_dpl_tiers_without_flattening_fixed_locations(self) -> None:
        rows = hierarchy_rows(
            [
                {"library_id": "hq", "name": "DPL Head Quarter", "location_type": "fixed_library", "zone": "central", "address": "", "latitude": "", "longitude": ""},
                {"library_id": "zonal", "name": "Shahdara", "location_type": "zonal_library", "zone": "east", "address": "", "latitude": "", "longitude": ""},
                {"library_id": "branch", "name": "Kalyan Puri", "location_type": "fixed_library", "zone": "east", "address": "", "latitude": "", "longitude": ""},
                {"library_id": "sub", "name": "Narela", "location_type": "sub_branch_library", "zone": "north", "address": "", "latitude": "", "longitude": ""},
                {"library_id": "community", "name": "Lodhi Colony", "location_type": "community_library", "zone": "south", "address": "", "latitude": "", "longitude": ""},
                {"library_id": "mobile", "name": "Mobile Service Point 001", "location_type": "mobile_service_point", "zone": "mobile", "address": "", "latitude": "", "longitude": ""},
            ],
            [],
        )

        summary = summarize_hierarchy(rows)

        self.assertEqual(summary["total_locations"], "6")
        self.assertEqual(summary["fixed_physical_locations"], "5")
        self.assertEqual(summary["mobile_service_points"], "1")
        self.assertEqual(summary["headquarters"], "1")
        self.assertEqual(summary["zonal_libraries"], "1")
        self.assertEqual(summary["branch_libraries"], "1")
        self.assertEqual(summary["sub_branch_libraries"], "1")
        self.assertEqual(summary["community_libraries"], "1")


if __name__ == "__main__":
    unittest.main()
