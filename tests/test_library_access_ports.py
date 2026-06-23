import tempfile
import unittest
from pathlib import Path

from sevent4.adapters.library_access_filesystem import (
    CsvLibraryComparisonWriter,
    CsvLibraryLocationRepository,
    CsvLibrarySummaryWriter,
    FileLibraryComparisonInputRepository,
    read_csv,
)
from sevent4.application.library_access import (
    build_library_access_comparison,
    build_library_service_detail_audit,
    build_toronto_library_headline_rows,
    build_city_library_summary,
    haversine_m,
    library_pair_key,
    nearest_library_access,
    threshold_share,
    weighted_quantile,
)
from sevent4.ports.library_access import (
    CityLibraryComparisonInput,
    CityLibraryServiceDetailInput,
    CityLibrarySummaryInput,
    LIBRARY_COMPARISON_FIELDS,
    LIBRARY_SERVICE_DETAIL_FIELDS,
)


class LibraryAccessPortsTest(unittest.TestCase):
    def test_application_computes_weighted_access_without_file_io(self) -> None:
        rows = [
            {"minutes": 5.0, "population": 10.0},
            {"minutes": 20.0, "population": 80.0},
            {"minutes": 60.0, "population": 10.0},
        ]

        self.assertEqual(weighted_quantile(rows, "minutes", "population", 0.50), 20.0)
        self.assertEqual(weighted_quantile(rows, "minutes", "population", 0.90), 60.0)
        self.assertEqual(threshold_share(rows, "minutes", "population", 30.0), 90.0)

    def test_application_computes_nearest_library_walk_minutes(self) -> None:
        origins = [
            {"origin_id": "near", "latitude": "28.6599438", "longitude": "77.2291808", "population": "100"},
            {"origin_id": "far", "latitude": "28.6100", "longitude": "77.2000", "population": "50"},
        ]
        libraries = [
            {"library_id": "central", "latitude": "28.6599438", "longitude": "77.2291808", "name": "Central"},
            {"library_id": "south", "latitude": "28.5754", "longitude": "77.1939", "name": "South"},
        ]

        rows = nearest_library_access(origins, libraries, walk_speed_kmph=4.8)

        self.assertGreater(haversine_m(28.6599438, 77.2291808, 28.6572918, 77.2303200), 250.0)
        self.assertEqual(rows[0]["nearest_library_id"], "central")
        self.assertEqual(rows[0]["walk_minutes_to_nearest_library"], 0.0)
        self.assertEqual(rows[1]["nearest_library_id"], "south")
        self.assertGreater(rows[1]["walk_minutes_to_nearest_library"], 20.0)

    def test_application_builds_city_summary_from_location_rows(self) -> None:
        result = build_city_library_summary(
            CityLibrarySummaryInput(
                city="delhi",
                source_path="data/cities/delhi/source/libraries/dpl_library_locations.csv",
                rows=[
                    {"library_id": "a", "latitude": "28.6", "longitude": "77.2", "location_type": "fixed"},
                    {"library_id": "b", "latitude": "", "longitude": "", "location_type": "mobile_service_point"},
                    {"library_id": "c", "latitude": "28.7", "longitude": "77.3", "location_type": "mobile_service_point"},
                ],
                fixed_library_policy="exclude_mobile_service_points",
                pending_status="geocoding_required",
                complete_status="ready_for_population_origins",
                notes="DPL-published addresses parsed.",
            )
        )

        self.assertEqual(result.rows[0]["library_locations"], "3")
        self.assertEqual(result.rows[0]["fixed_library_locations"], "1")
        self.assertEqual(result.rows[0]["mobile_service_points"], "2")
        self.assertEqual(result.rows[0]["coordinate_verified_locations"], "2")
        self.assertEqual(result.rows[0]["access_status"], "geocoding_required")
        self.assertEqual(result.rows[0]["confidence"], "medium")

    def test_filesystem_adapters_read_locations_and_write_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "locations.csv"
            out = root / "summary.csv"
            source.write_text(
                "library_id,latitude,longitude,location_type\n"
                "a,28.6,77.2,fixed\n"
                "b,,,mobile_service_point\n",
                encoding="utf-8",
            )

            repository = CsvLibraryLocationRepository(
                source,
                city="delhi",
                source_path="data/cities/delhi/source/libraries/dpl_library_locations.csv",
                fixed_library_policy="exclude_mobile_service_points",
                pending_status="geocoding_required",
                complete_status="ready_for_population_origins",
                notes="DPL-published addresses parsed.",
            )
            result = build_city_library_summary(repository.load())
            CsvLibrarySummaryWriter(out).write(result)

            self.assertIn("library_locations", out.read_text(encoding="utf-8"))
            self.assertEqual(result.rows[0]["city"], "delhi")

    def test_filesystem_csv_reader_handles_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.csv"
            path.write_text("\ufeffyear,value\n2024,10\n", encoding="utf-8")

            self.assertEqual(read_csv(path), [{"year": "2024", "value": "10"}])

    def test_application_builds_library_access_comparison_rows(self) -> None:
        result = build_library_access_comparison(
            CityLibraryComparisonInput(
                cities=["ahmedabad", "delhi", "toronto"],
                summaries={
                    "ahmedabad": {
                        "city": "ahmedabad",
                        "library_locations": "83",
                        "access_status": "population_origins_required",
                    },
                    "delhi": {
                        "city": "delhi",
                        "library_locations": "111",
                        "access_status": "geocoding_required",
                    },
                },
            )
        )

        self.assertEqual(result.fields, LIBRARY_COMPARISON_FIELDS)
        self.assertEqual(library_pair_key("toronto", "ahmedabad"), "ahmedabad_toronto")
        self.assertEqual(result.rows[0]["pair"], "ahmedabad_delhi")
        self.assertEqual(result.rows[0]["comparison_status"], "available")
        self.assertEqual(result.rows[1]["pair"], "ahmedabad_toronto")
        self.assertEqual(result.rows[1]["comparison_status"], "missing_city_summary")

    def test_filesystem_adapters_load_and_write_library_comparisons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ahmedabad = root / "cities" / "ahmedabad" / "derived" / "library_access"
            delhi = root / "cities" / "delhi" / "derived" / "library_access"
            out = root / "comparators" / "library_access"
            ahmedabad.mkdir(parents=True)
            delhi.mkdir(parents=True)
            ahmedabad.joinpath("library_access_summary.csv").write_text(
                "city,library_locations,access_status\nahmedabad,83,population_origins_required\n",
                encoding="utf-8",
            )
            delhi.joinpath("library_access_summary.csv").write_text(
                "city,library_locations,access_status\ndelhi,111,geocoding_required\n",
                encoding="utf-8",
            )

            result = build_library_access_comparison(
                FileLibraryComparisonInputRepository(root / "cities", ["ahmedabad", "delhi", "toronto"]).load()
            )
            CsvLibraryComparisonWriter(out).write(result)

            self.assertEqual(result.rows[0]["pair"], "ahmedabad_delhi")
            self.assertTrue((out / "library_access_summary.csv").exists())
            self.assertTrue((out / "ahmedabad_delhi_access_comparison.csv").exists())
            self.assertIn("missing_city_summary", (out / "library_access_summary.csv").read_text(encoding="utf-8"))

    def test_application_builds_library_service_detail_audit_rows(self) -> None:
        rows = build_library_service_detail_audit(
            [
                CityLibraryServiceDetailInput(
                    city="ahmedabad",
                    library_system="Sheth M.J. Library / Ahmedabad municipal library network",
                    total_locations="83",
                    source_path="data/cities/ahmedabad/source/libraries/ahmedabad_library_locations.csv",
                    values={
                        "max_seating_capacity": "",
                        "opening_hours": "",
                        "branch_collection_size": "",
                        "collection_types": "",
                    },
                ),
                CityLibraryServiceDetailInput(
                    city="delhi",
                    library_system="Delhi Public Library",
                    total_locations="111",
                    source_path="data/cities/delhi/derived/library_access/dpl_service_hierarchy_summary.csv",
                    values={
                        "max_seating_capacity": "12",
                        "opening_hours": "0",
                        "branch_collection_size": "8",
                        "collection_types": "",
                    },
                ),
            ]
        )

        self.assertEqual(list(rows[0].keys()), LIBRARY_SERVICE_DETAIL_FIELDS)
        by_city_field = {(row["city"], row["detail_field"]): row for row in rows}
        self.assertEqual(by_city_field[("ahmedabad", "max_seating_capacity")]["locations_with_value"], "0")
        self.assertEqual(by_city_field[("delhi", "max_seating_capacity")]["locations_with_value"], "12")
        self.assertEqual(
            by_city_field[("delhi", "collection_types")]["status"],
            "missing_branchwise_public_detail",
        )

    def test_application_builds_toronto_headline_rows(self) -> None:
        rows = build_toronto_library_headline_rows(physical_branches=99, total_square_feet=2_500_000.7)
        by_metric = {row["metric_name"]: row for row in rows}

        self.assertEqual(len(rows), 22)
        self.assertEqual(by_metric["branches"]["value"], "99")
        self.assertEqual(by_metric["branch_square_feet"]["value"], "2500000")
        self.assertEqual(by_metric["gross_expenditure"]["unit"], "CAD")
        self.assertEqual(by_metric["bookmobiles"]["source_url"], "https://tpl.ca/about-the-library/")


if __name__ == "__main__":
    unittest.main()
