import tempfile
import unittest
import zipfile
import json
import subprocess
from pathlib import Path

import scripts.recipes.transit.build_bmrcl_iudx_gtfs_from_exports as bmrcl_iudx_recipe
import scripts.recipes.transit.build_bmtc_iudx_gtfs_from_exports as bmtc_iudx_recipe
import scripts.recipes.transit.preflight_iudx_bengaluru_exports as preflight_iudx_recipe
from sevent4.transit.iudx_gtfs_export import (
    load_static_gtfs_tables_from_json_dir,
    summarize_static_gtfs_quality,
    write_static_gtfs_zip_from_tables,
)


class IudxGtfsExportTest(unittest.TestCase):
    def test_writes_static_gtfs_zip_from_iudx_table_rows(self) -> None:
        rows_by_file = {
            "agency.txt": [
                {
                    "agency_id": "BMTC",
                    "agency_name": "Bangalore Metropolitan Transport Corporation",
                    "agency_url": "https://mybmtc.karnataka.gov.in",
                    "agency_timezone": "Asia/Kolkata",
                }
            ],
            "calendar.txt": [
                {
                    "service_id": "weekday",
                    "monday": "1",
                    "tuesday": "1",
                    "wednesday": "1",
                    "thursday": "1",
                    "friday": "1",
                    "saturday": "0",
                    "sunday": "0",
                    "start_date": "20260704",
                    "end_date": "20261231",
                }
            ],
            "routes.txt": [
                {
                    "route_id": "500D",
                    "agency_id": "BMTC",
                    "route_short_name": "500D",
                    "route_long_name": "Central Silk Board - Hebbal",
                    "route_type": "3",
                }
            ],
            "stops.txt": [
                {"stop_id": "S1", "stop_name": "Central Silk Board", "stop_lat": "12.917", "stop_lon": "77.623"},
                {"stop_id": "S2", "stop_name": "Hebbal", "stop_lat": "13.035", "stop_lon": "77.598"},
            ],
            "trips.txt": [
                {"route_id": "500D", "service_id": "weekday", "trip_id": "T1"},
            ],
            "stop_times.txt": [
                {
                    "trip_id": "T1",
                    "arrival_time": "08:00:00",
                    "departure_time": "08:00:00",
                    "stop_id": "S1",
                    "stop_sequence": "1",
                },
                {
                    "trip_id": "T1",
                    "arrival_time": "08:40:00",
                    "departure_time": "08:40:00",
                    "stop_id": "S2",
                    "stop_sequence": "2",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            out_zip = Path(tmp) / "bmtc_iudx.zip"

            result = write_static_gtfs_zip_from_tables(rows_by_file, out_zip)

            self.assertEqual(
                result,
                {
                    "agency.txt": 1,
                    "calendar.txt": 1,
                    "routes.txt": 1,
                    "stops.txt": 2,
                    "trips.txt": 1,
                    "stop_times.txt": 2,
                },
            )
            with zipfile.ZipFile(out_zip) as zf:
                self.assertEqual(
                    sorted(zf.namelist()),
                    [
                        "agency.txt",
                        "calendar.txt",
                        "routes.txt",
                        "stop_times.txt",
                        "stops.txt",
                        "trips.txt",
                    ],
                )
                self.assertIn("Central Silk Board", zf.read("stops.txt").decode("utf-8"))
                self.assertTrue(
                    zf.read("stop_times.txt")
                    .decode("utf-8")
                    .startswith("trip_id,arrival_time,departure_time,stop_id,stop_sequence\n")
                )

    def test_rejects_export_without_stop_times(self) -> None:
        rows_by_file = {
            "agency.txt": [{"agency_id": "BMTC"}],
            "calendar.txt": [{"service_id": "weekday"}],
            "routes.txt": [{"route_id": "500D"}],
            "stops.txt": [{"stop_id": "S1"}],
            "trips.txt": [{"trip_id": "T1"}],
        }

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "stop_times.txt"):
                write_static_gtfs_zip_from_tables(rows_by_file, Path(tmp) / "bmtc_iudx.zip")

    def test_rejects_stop_times_with_no_two_stop_trip_sequences(self) -> None:
        rows_by_file = {
            "agency.txt": [{"agency_id": "BMTC"}],
            "calendar.txt": [{"service_id": "weekday"}],
            "routes.txt": [{"route_id": "500D"}],
            "stops.txt": [{"stop_id": "S1"}, {"stop_id": "S2"}],
            "trips.txt": [{"trip_id": "T1"}, {"trip_id": "T2"}],
            "stop_times.txt": [
                {"trip_id": "T1", "stop_id": "S1", "stop_sequence": "1"},
                {"trip_id": "T2", "stop_id": "S2", "stop_sequence": "1"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "at least one trip with two stops"):
                write_static_gtfs_zip_from_tables(rows_by_file, Path(tmp) / "bmtc_iudx.zip")

    def test_summarizes_static_gtfs_quality_for_route_geometry_readiness(self) -> None:
        rows_by_file = {
            "agency.txt": [{"agency_id": "BMTC"}],
            "calendar.txt": [{"service_id": "weekday"}],
            "routes.txt": [{"route_id": "500D"}],
            "stops.txt": [{"stop_id": "S1"}, {"stop_id": "S2"}],
            "trips.txt": [{"trip_id": "T1"}],
            "stop_times.txt": [
                {"trip_id": "T1", "stop_id": "S1", "stop_sequence": "1"},
                {"trip_id": "T1", "stop_id": "S2", "stop_sequence": "2"},
            ],
        }

        quality = summarize_static_gtfs_quality(rows_by_file)

        self.assertEqual(
            quality,
            {
                "route_geometry_ready": True,
                "stop_count": 2,
                "route_count": 1,
                "trip_count": 1,
                "stop_time_count": 2,
                "trips_with_two_or_more_stops": 1,
                "max_stops_per_trip": 2,
            },
        )

    def test_loads_static_gtfs_tables_from_json_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "agency.json").write_text('[{"agency_id":"BMTC"}]', encoding="utf-8")
            (base / "calendar.json").write_text('[{"service_id":"weekday"}]', encoding="utf-8")
            (base / "routes.json").write_text('[{"route_id":"500D"}]', encoding="utf-8")
            (base / "stops.json").write_text('[{"stop_id":"S1"}]', encoding="utf-8")
            (base / "trips.json").write_text('[{"trip_id":"T1"}]', encoding="utf-8")
            (base / "stop_times.json").write_text('[{"trip_id":"T1"}]', encoding="utf-8")

            tables = load_static_gtfs_tables_from_json_dir(base)

            self.assertEqual(sorted(tables), [
                "agency.txt",
                "calendar.txt",
                "routes.txt",
                "stop_times.txt",
                "stops.txt",
                "trips.txt",
            ])
            self.assertEqual(tables["routes.txt"], [{"route_id": "500D"}])

    def test_loads_iudx_result_envelopes_and_flattens_value_wrappers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "agency.json").write_text(
                '{"results":[{"agency_id":{"value":"BMTC"},"agency_name":{"value":"BMTC"}}]}',
                encoding="utf-8",
            )
            (base / "calendar.json").write_text(
                '{"results":[{"service_id":{"value":"weekday"},"monday":{"value":1},"tuesday":{"value":1},"wednesday":{"value":1},"thursday":{"value":1},"friday":{"value":1},"saturday":{"value":0},"sunday":{"value":0},"start_date":{"value":"20260705"},"end_date":{"value":"20261231"}}]}',
                encoding="utf-8",
            )
            (base / "routes.json").write_text(
                '{"results":[{"route_id":{"value":"500D"},"route_short_name":{"value":"500D"},"route_type":{"value":3}}]}',
                encoding="utf-8",
            )
            (base / "stops.json").write_text(
                '{"results":[{"stop_id":{"value":"S1"},"stop_name":{"value":"Central Silk Board"},"stop_lat":{"value":12.917},"stop_lon":{"value":77.623}}]}',
                encoding="utf-8",
            )
            (base / "trips.json").write_text(
                '{"results":[{"route_id":{"value":"500D"},"service_id":{"value":"weekday"},"trip_id":{"value":"T1"}}]}',
                encoding="utf-8",
            )
            (base / "stop_times.json").write_text(
                '{"results":[{"trip_id":{"value":"T1"},"arrival_time":{"value":"08:00:00"},"departure_time":{"value":"08:00:00"},"stop_id":{"value":"S1"},"stop_sequence":{"value":1}}]}',
                encoding="utf-8",
            )

            tables = load_static_gtfs_tables_from_json_dir(base)

            self.assertEqual(tables["agency.txt"], [{"agency_id": "BMTC", "agency_name": "BMTC"}])
            self.assertEqual(tables["routes.txt"][0]["route_type"], 3)
            self.assertEqual(tables["stop_times.txt"][0]["stop_sequence"], 1)

    def test_bmtc_preflight_flags_missing_stop_times_before_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmtc"
            input_dir.mkdir()
            (input_dir / "agency.json").write_text(
                '[{"agency_id":"BMTC","agency_name":"BMTC","agency_url":"https://mybmtc.karnataka.gov.in","agency_timezone":"Asia/Kolkata"}]',
                encoding="utf-8",
            )
            (input_dir / "calendar.json").write_text(
                '[{"service_id":"weekday","monday":"1","tuesday":"1","wednesday":"1","thursday":"1","friday":"1","saturday":"1","sunday":"1","start_date":"20260705","end_date":"20261231"}]',
                encoding="utf-8",
            )
            (input_dir / "routes.json").write_text(
                '[{"route_id":"500D","agency_id":"BMTC","route_short_name":"500D","route_long_name":"Central Silk Board - Hebbal","route_type":"3"}]',
                encoding="utf-8",
            )
            (input_dir / "stops.json").write_text(
                '[{"stop_id":"S1","stop_name":"Central Silk Board","stop_lat":"12.917","stop_lon":"77.623"}]',
                encoding="utf-8",
            )
            (input_dir / "trips.json").write_text(
                '[{"route_id":"500D","service_id":"weekday","trip_id":"T1"}]',
                encoding="utf-8",
            )

            result = preflight_iudx_recipe.preflight_bmtc_export_dir(input_dir)

        self.assertEqual(
            result,
            {
                "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
                "input_dir": str(input_dir),
                "required_input_files": [
                    "agency.json",
                    "calendar.json",
                    "routes.json",
                    "stops.json",
                    "trips.json",
                    "stop_times.json",
                ],
                "present_input_files": [
                    "agency.json",
                    "calendar.json",
                    "routes.json",
                    "stops.json",
                    "trips.json",
                ],
                "missing_input_files": ["stop_times.json"],
                "empty_input_files": [],
                "missing_required_fields": [],
                "invalid_field_values": [],
                "input_errors": [],
                "row_counts": {},
                "quality_checks": {},
                "ready_to_build": False,
                "remaining_gates": ["missing_input_files", "stop_times_or_equivalent_stop_sequence"],
            },
        )

    def test_bmrcl_preflight_requires_scheduled_operational_yellow_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmrcl"
            input_dir.mkdir()
            (input_dir / "stations.json").write_text(
                json.dumps(
                    [
                        {"stop_code": "PP01", "stop_name": "Purple One", "location": {"coordinates": [77.60, 12.90]}},
                        {"stop_code": "PP02", "stop_name": "Purple Two", "location": {"coordinates": [77.61, 12.91]}},
                        {"stop_code": "GR01", "stop_name": "Green One", "location": {"coordinates": [77.58, 13.00]}},
                        {"stop_code": "GR02", "stop_name": "Green Two", "location": {"coordinates": [77.59, 13.01]}},
                        {"stop_code": "YL01", "stop_name": "Yellow One", "location": {"coordinates": [77.62, 12.88]}},
                        {"stop_code": "YL02", "stop_name": "Yellow Two", "location": {"coordinates": [77.63, 12.89]}},
                    ]
                ),
                encoding="utf-8",
            )
            (input_dir / "lines.json").write_text(
                json.dumps(
                    [
                        {
                            "route_id": "Line 1",
                            "route_short_name": "Purple Line",
                            "route_long_name": "Purple corridor",
                            "routeStopSequence": ["PP01", "PP02"],
                            "location": {"coordinates": [[77.60, 12.90], [77.61, 12.91]]},
                        },
                        {
                            "route_id": "Line 2",
                            "route_short_name": "Green Line",
                            "route_long_name": "Green corridor",
                            "routeStopSequence": ["GR01", "GR02"],
                            "location": {"coordinates": [[77.58, 13.00], [77.59, 13.01]]},
                        },
                        {
                            "route_id": "Line 3",
                            "route_short_name": "Yellow Line",
                            "route_long_name": "Yellow corridor",
                            "routeStopSequence": ["YL01", "YL02"],
                            "location": {"coordinates": [[77.62, 12.88], [77.63, 12.89]]},
                        },
                    ]
                ),
                encoding="utf-8",
            )
            (input_dir / "schedule.json").write_text(
                json.dumps(
                    [
                        {"route_id": "Line 1", "train_id": 101, "stationCode": "PP01", "arrival_time": "06:00:00", "departure_time": "06:00:30"},
                        {"route_id": "Line 1", "train_id": 101, "stationCode": "PP02", "arrival_time": "06:05:00", "departure_time": "06:05:30"},
                        {"route_id": "Line 2", "train_id": 201, "stationCode": "GR01", "arrival_time": "06:10:00", "departure_time": "06:10:30"},
                        {"route_id": "Line 2", "train_id": 201, "stationCode": "GR02", "arrival_time": "06:16:00", "departure_time": "06:16:30"},
                    ]
                ),
                encoding="utf-8",
            )

            result = preflight_iudx_recipe.preflight_bmrcl_export_dir(
                input_dir,
                generated_at="2026-07-05T01:48:00Z",
            )

        self.assertEqual(result["feed_id"], "bengaluru_bmrcl_iudx_full_network_schedule")
        self.assertEqual(result["missing_input_files"], [])
        self.assertEqual(result["row_counts"]["routes.txt"], 3)
        self.assertEqual(result["quality_checks"]["missing_scheduled_operational_route_short_names"], ["Yellow Line"])
        self.assertFalse(result["ready_to_build"])
        self.assertEqual(result["remaining_gates"], ["purple_green_yellow_scheduled_two_stop_trips"])

    def test_preflight_cli_runs_from_repo_root_with_missing_export_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/recipes/transit/preflight_iudx_bengaluru_exports.py",
                    "--bmtc-input-dir",
                    str(base / "missing-bmtc"),
                    "--bmrcl-input-dir",
                    str(base / "missing-bmrcl"),
                    "--generated-at",
                    "2026-07-05T01:46:12Z",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)

        self.assertEqual(payload["schema"], "sevent4.bengaluru_iudx_export_preflight.v1")
        self.assertEqual([feed["feed_id"] for feed in payload["feeds"]], [
            "bengaluru_bmtc_iudx_full_gtfs",
            "bengaluru_bmrcl_iudx_full_network_schedule",
        ])
        self.assertEqual(payload["feeds"][0]["missing_input_files"][-1], "stop_times.json")
        self.assertEqual(payload["feeds"][1]["missing_input_files"], ["stations.json", "lines.json", "schedule.json"])

    def test_preflight_cli_strict_exits_nonzero_when_any_feed_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/recipes/transit/preflight_iudx_bengaluru_exports.py",
                    "--bmtc-input-dir",
                    str(base / "missing-bmtc"),
                    "--generated-at",
                    "2026-07-05T01:46:12Z",
                    "--strict",
                ],
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 1)
        self.assertFalse(payload["feeds"][0]["ready_to_build"])
        self.assertEqual(payload["feeds"][0]["remaining_gates"], [
            "missing_input_files",
            "stop_times_or_equivalent_stop_sequence",
        ])
        self.assertEqual(completed.stderr, "")

    def test_preflight_cli_strict_reports_malformed_json_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmtc"
            input_dir.mkdir()
            (input_dir / "agency.json").write_text(
                '[{"agency_id":"BMTC","agency_name":"BMTC","agency_url":"https://mybmtc.karnataka.gov.in","agency_timezone":"Asia/Kolkata"}]',
                encoding="utf-8",
            )
            (input_dir / "calendar.json").write_text(
                '[{"service_id":"weekday","monday":"1","tuesday":"1","wednesday":"1","thursday":"1","friday":"1","saturday":"1","sunday":"1","start_date":"20260705","end_date":"20261231"}]',
                encoding="utf-8",
            )
            (input_dir / "routes.json").write_text(
                '[{"route_id":"500D","agency_id":"BMTC","route_short_name":"500D","route_long_name":"Central Silk Board - Hebbal","route_type":"3"}]',
                encoding="utf-8",
            )
            (input_dir / "stops.json").write_text(
                '[{"stop_id":"S1","stop_name":"Central Silk Board","stop_lat":"12.917","stop_lon":"77.623"}]',
                encoding="utf-8",
            )
            (input_dir / "trips.json").write_text(
                '[{"route_id":"500D","service_id":"weekday","trip_id":"T1"}]',
                encoding="utf-8",
            )
            (input_dir / "stop_times.json").write_text('[{"trip_id":"T1"', encoding="utf-8")
            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/recipes/transit/preflight_iudx_bengaluru_exports.py",
                    "--bmtc-input-dir",
                    str(input_dir),
                    "--generated-at",
                    "2026-07-05T01:46:12Z",
                    "--strict",
                ],
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(payload["feeds"][0]["input_errors"][0]["file"], "stop_times.json")
        self.assertEqual(payload["feeds"][0]["remaining_gates"], ["invalid_input_json"])
        self.assertFalse(payload["feeds"][0]["ready_to_build"])
        self.assertNotIn("Traceback", completed.stderr)

    def test_preflight_cli_strict_reports_empty_required_input_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmtc"
            input_dir.mkdir()
            (input_dir / "agency.json").write_text(
                '[{"agency_id":"BMTC","agency_name":"BMTC","agency_url":"https://mybmtc.karnataka.gov.in","agency_timezone":"Asia/Kolkata"}]',
                encoding="utf-8",
            )
            (input_dir / "calendar.json").write_text(
                '[{"service_id":"weekday","monday":"1","tuesday":"1","wednesday":"1","thursday":"1","friday":"1","saturday":"1","sunday":"1","start_date":"20260705","end_date":"20261231"}]',
                encoding="utf-8",
            )
            (input_dir / "routes.json").write_text(
                '[{"route_id":"500D","agency_id":"BMTC","route_short_name":"500D","route_long_name":"Central Silk Board - Hebbal","route_type":"3"}]',
                encoding="utf-8",
            )
            (input_dir / "stops.json").write_text(
                '[{"stop_id":"S1","stop_name":"Central Silk Board","stop_lat":"12.917","stop_lon":"77.623"}]',
                encoding="utf-8",
            )
            (input_dir / "trips.json").write_text(
                '[{"route_id":"500D","service_id":"weekday","trip_id":"T1"}]',
                encoding="utf-8",
            )
            (input_dir / "stop_times.json").write_text("[]", encoding="utf-8")
            completed = subprocess.run(
                [
                    ".venv/bin/python",
                    "scripts/recipes/transit/preflight_iudx_bengaluru_exports.py",
                    "--bmtc-input-dir",
                    str(input_dir),
                    "--generated-at",
                    "2026-07-05T01:46:12Z",
                    "--strict",
                ],
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(payload["feeds"][0]["empty_input_files"], ["stop_times.json"])
        self.assertEqual(payload["feeds"][0]["remaining_gates"], [
            "empty_input_files",
            "stop_times_or_equivalent_stop_sequence",
        ])
        self.assertFalse(payload["feeds"][0]["ready_to_build"])
        self.assertEqual(completed.stderr, "")

    def test_bmtc_preflight_requires_core_static_gtfs_table_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmtc"
            input_dir.mkdir()
            (input_dir / "agency.json").write_text('[{"agency_id":"BMTC"}]', encoding="utf-8")
            (input_dir / "calendar.json").write_text('[{"service_id":"weekday"}]', encoding="utf-8")
            (input_dir / "routes.json").write_text('[{"route_id":"500D"}]', encoding="utf-8")
            (input_dir / "stops.json").write_text(
                '[{"stop_id":"S1"},{"stop_id":"S2"}]',
                encoding="utf-8",
            )
            (input_dir / "trips.json").write_text('[{"trip_id":"T1"}]', encoding="utf-8")
            (input_dir / "stop_times.json").write_text(
                '[{"trip_id":"T1","arrival_time":"08:00:00","departure_time":"08:00:00","stop_id":"S1","stop_sequence":"1"},{"trip_id":"T1","arrival_time":"08:40:00","departure_time":"08:40:00","stop_id":"S2","stop_sequence":"2"}]',
                encoding="utf-8",
            )

            result = preflight_iudx_recipe.preflight_bmtc_export_dir(input_dir)

        self.assertEqual(
            result["missing_required_fields"],
            [
                {"file": "agency.json", "missing_fields": ["agency_name", "agency_url", "agency_timezone"]},
                {
                    "file": "calendar.json",
                    "missing_fields": [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                        "start_date",
                        "end_date",
                    ],
                },
                {"file": "routes.json", "missing_fields": ["agency_id", "route_short_name", "route_long_name", "route_type"]},
                {"file": "stops.json", "missing_fields": ["stop_name", "stop_lat", "stop_lon"]},
                {"file": "trips.json", "missing_fields": ["route_id", "service_id"]},
            ],
        )
        self.assertFalse(result["ready_to_build"])
        self.assertEqual(result["remaining_gates"], ["missing_required_fields"])

    def test_bmtc_preflight_rejects_rows_missing_required_gtfs_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmtc"
            input_dir.mkdir()
            (input_dir / "agency.json").write_text(
                '[{"agency_id":"BMTC","agency_name":"BMTC","agency_url":"https://mybmtc.karnataka.gov.in","agency_timezone":"Asia/Kolkata"}]',
                encoding="utf-8",
            )
            (input_dir / "calendar.json").write_text(
                '[{"service_id":"weekday","monday":"1","tuesday":"1","wednesday":"1","thursday":"1","friday":"1","saturday":"1","sunday":"1","start_date":"20260705","end_date":"20261231"}]',
                encoding="utf-8",
            )
            (input_dir / "routes.json").write_text(
                '[{"route_id":"500D","agency_id":"BMTC","route_short_name":"500D","route_long_name":"Central Silk Board - Hebbal","route_type":"3"}]',
                encoding="utf-8",
            )
            (input_dir / "stops.json").write_text(
                '[{"stop_id":"S1","stop_name":"Central Silk Board","stop_lat":"12.917","stop_lon":"77.623"},{"stop_id":"S2","stop_name":"Hebbal","stop_lat":"13.035","stop_lon":"77.598"}]',
                encoding="utf-8",
            )
            (input_dir / "trips.json").write_text(
                '[{"route_id":"500D","service_id":"weekday","trip_id":"T1"}]',
                encoding="utf-8",
            )
            (input_dir / "stop_times.json").write_text(
                '[{"trip_id":"T1","stop_id":"S1"},{"trip_id":"T1","stop_id":"S2","stop_sequence":"2"}]',
                encoding="utf-8",
            )

            result = preflight_iudx_recipe.preflight_bmtc_export_dir(input_dir)

        self.assertEqual(
            result["missing_required_fields"],
            [
                {
                    "file": "stop_times.json",
                    "missing_fields": ["arrival_time", "departure_time", "stop_sequence"],
                }
            ],
        )
        self.assertFalse(result["ready_to_build"])
        self.assertIn("missing_required_fields", result["remaining_gates"])

    def test_bmtc_preflight_rejects_invalid_core_gtfs_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmtc"
            input_dir.mkdir()
            (input_dir / "agency.json").write_text(
                '[{"agency_id":"BMTC","agency_name":"BMTC","agency_url":"not-a-url","agency_timezone":"Asia/Kolkata"}]',
                encoding="utf-8",
            )
            (input_dir / "calendar.json").write_text(
                '[{"service_id":"weekday","monday":"2","tuesday":"1","wednesday":"1","thursday":"1","friday":"1","saturday":"1","sunday":"1","start_date":"2026-07-05","end_date":"20261231"}]',
                encoding="utf-8",
            )
            (input_dir / "routes.json").write_text(
                '[{"route_id":"500D","agency_id":"BMTC","route_short_name":"500D","route_long_name":"Central Silk Board - Hebbal","route_type":"bus"}]',
                encoding="utf-8",
            )
            (input_dir / "stops.json").write_text(
                '[{"stop_id":"S1","stop_name":"Central Silk Board","stop_lat":"99","stop_lon":"77.623"},{"stop_id":"S2","stop_name":"Hebbal","stop_lat":"13.035","stop_lon":"east"}]',
                encoding="utf-8",
            )
            (input_dir / "trips.json").write_text(
                '[{"route_id":"500D","service_id":"weekday","trip_id":"T1"}]',
                encoding="utf-8",
            )
            (input_dir / "stop_times.json").write_text(
                '[{"trip_id":"T1","arrival_time":"8am","departure_time":"08:00:00","stop_id":"S1","stop_sequence":"0"},{"trip_id":"T1","arrival_time":"08:40:00","departure_time":"25:00","stop_id":"S2","stop_sequence":"2"}]',
                encoding="utf-8",
            )

            result = preflight_iudx_recipe.preflight_bmtc_export_dir(input_dir)

        self.assertEqual(
            result["invalid_field_values"],
            [
                {"file": "agency.json", "invalid_fields": ["agency_url"]},
                {"file": "calendar.json", "invalid_fields": ["monday", "start_date"]},
                {"file": "routes.json", "invalid_fields": ["route_type"]},
                {"file": "stops.json", "invalid_fields": ["stop_lat", "stop_lon"]},
                {"file": "stop_times.json", "invalid_fields": ["arrival_time", "departure_time", "stop_sequence"]},
            ],
        )
        self.assertFalse(result["ready_to_build"])
        self.assertIn("invalid_field_values", result["remaining_gates"])

    def test_bmrcl_preflight_rejects_rows_missing_required_iudx_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmrcl"
            input_dir.mkdir()
            (input_dir / "stations.json").write_text(
                json.dumps([{"stop_code": "PP01", "stop_name": "Purple One", "location": {"coordinates": [77.60, 12.90]}}]),
                encoding="utf-8",
            )
            (input_dir / "lines.json").write_text(
                json.dumps(
                    [
                        {
                            "route_id": "Line 1",
                            "route_short_name": "Purple Line",
                            "route_long_name": "Purple corridor",
                            "location": {"coordinates": [[77.60, 12.90], [77.61, 12.91]]},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (input_dir / "schedule.json").write_text(
                json.dumps([{"route_id": "Line 1", "train_id": 101, "stationCode": "PP01", "arrival_time": "06:00:00"}]),
                encoding="utf-8",
            )

            result = preflight_iudx_recipe.preflight_bmrcl_export_dir(
                input_dir,
                generated_at="2026-07-05T02:05:00Z",
            )

        self.assertEqual(
            result["missing_required_fields"],
            [
                {"file": "lines.json", "missing_fields": ["routeStopSequence"]},
                {"file": "schedule.json", "missing_fields": ["departure_time"]},
            ],
        )
        self.assertFalse(result["ready_to_build"])
        self.assertIn("missing_required_fields", result["remaining_gates"])

    def test_bmrcl_preflight_rejects_invalid_coordinates_and_times(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmrcl"
            input_dir.mkdir()
            (input_dir / "stations.json").write_text(
                json.dumps(
                    [
                        {"stop_code": "PP01", "stop_name": "Purple One", "location": {"coordinates": [77.60, 91]}},
                        {"stop_code": "PP02", "stop_name": "Purple Two", "location": {"coordinates": ["east", 12.91]}},
                    ]
                ),
                encoding="utf-8",
            )
            (input_dir / "lines.json").write_text(
                json.dumps(
                    [
                        {
                            "route_id": "Line 1",
                            "route_short_name": "Purple Line",
                            "route_long_name": "Purple corridor",
                            "routeStopSequence": ["PP01", "PP02"],
                            "location": {"coordinates": [[77.60, 12.90], [77.61, 12.91]]},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (input_dir / "schedule.json").write_text(
                json.dumps(
                    [
                        {"route_id": "Line 1", "train_id": 101, "stationCode": "PP01", "arrival_time": "06:00", "departure_time": "06:00:30"},
                        {"route_id": "Line 1", "train_id": 101, "stationCode": "PP02", "arrival_time": "06:05:00", "departure_time": "24:61:00"},
                    ]
                ),
                encoding="utf-8",
            )

            result = preflight_iudx_recipe.preflight_bmrcl_export_dir(
                input_dir,
                generated_at="2026-07-05T02:12:00Z",
            )

        self.assertEqual(
            result["invalid_field_values"],
            [
                {"file": "stations.json", "invalid_fields": ["location"]},
                {"file": "schedule.json", "invalid_fields": ["arrival_time", "departure_time"]},
            ],
        )
        self.assertFalse(result["ready_to_build"])
        self.assertIn("invalid_field_values", result["remaining_gates"])

    def test_recipe_exports_bmtc_iudx_json_tables_with_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "tables"
            input_dir.mkdir()
            (input_dir / "agency.json").write_text('[{"agency_id":"BMTC","agency_name":"BMTC"}]', encoding="utf-8")
            (input_dir / "calendar.json").write_text(
                '[{"service_id":"weekday","monday":"1","tuesday":"1","wednesday":"1","thursday":"1","friday":"1","saturday":"0","sunday":"0","start_date":"20260705","end_date":"20261231"}]',
                encoding="utf-8",
            )
            (input_dir / "routes.json").write_text(
                '[{"route_id":"500D","agency_id":"BMTC","route_short_name":"500D","route_type":"3"}]',
                encoding="utf-8",
            )
            (input_dir / "stops.json").write_text(
                '[{"stop_id":"S1","stop_name":"Central Silk Board","stop_lat":"12.917","stop_lon":"77.623"},{"stop_id":"S2","stop_name":"Hebbal","stop_lat":"13.035","stop_lon":"77.598"}]',
                encoding="utf-8",
            )
            (input_dir / "trips.json").write_text('[{"route_id":"500D","service_id":"weekday","trip_id":"T1"}]', encoding="utf-8")
            (input_dir / "stop_times.json").write_text(
                '[{"trip_id":"T1","arrival_time":"08:00:00","departure_time":"08:00:00","stop_id":"S1","stop_sequence":"1"},{"trip_id":"T1","arrival_time":"08:40:00","departure_time":"08:40:00","stop_id":"S2","stop_sequence":"2"}]',
                encoding="utf-8",
            )
            out_zip = base / "bengaluru_bmtc_iudx_full_gtfs.zip"
            provenance = base / "bengaluru_bmtc_iudx_full_gtfs.sources.json"
            manifest_row = base / "bengaluru_bmtc_iudx_full_gtfs.feed.json"
            feed_manifest = base / "bengaluru_bmtc_iudx_full_gtfs.manifest.json"

            result = bmtc_iudx_recipe.build_bmtc_iudx_gtfs_from_exports(
                input_dir=input_dir,
                out_zip=out_zip,
                provenance_path=provenance,
                manifest_row_path=manifest_row,
                feed_manifest_path=feed_manifest,
                generated_at="2026-07-05T00:55:00Z",
            )

            self.assertEqual(result["row_counts"]["stop_times.txt"], 2)
            with zipfile.ZipFile(out_zip) as zf:
                self.assertIn("stop_times.txt", zf.namelist())
            source_doc = json.loads(provenance.read_text(encoding="utf-8"))
            self.assertEqual(source_doc["feed_id"], "bengaluru_bmtc_iudx_full_gtfs")
            self.assertEqual(source_doc["status"], "iudx_policy_approved_export")
            self.assertEqual(source_doc["row_counts"]["routes.txt"], 1)
            self.assertEqual(
                source_doc["quality_checks"],
                {
                    "route_geometry_ready": True,
                    "stop_count": 2,
                    "route_count": 1,
                    "trip_count": 1,
                    "stop_time_count": 2,
                    "trips_with_two_or_more_stops": 1,
                    "max_stops_per_trip": 2,
                },
            )
            self.assertEqual(source_doc["required_input_tables"][-1], "stop_times.json")
            feed_row = json.loads(manifest_row.read_text(encoding="utf-8"))
            self.assertEqual(feed_row["feed_id"], "bengaluru_bmtc_iudx_full_gtfs")
            self.assertEqual(feed_row["status"], "ok")
            self.assertTrue(feed_row["quality_checks"]["route_geometry_ready"])
            manifest = json.loads(feed_manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "sevent4.multimodal_transit.manifest.v1")
            self.assertEqual(manifest["feeds"], [feed_row])

    def test_builds_manifest_feed_row_from_ready_bmtc_iudx_provenance(self) -> None:
        provenance = {
            "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
            "status": "iudx_policy_approved_export",
            "gtfs_zip": "data/cities/bengaluru/source/transit/gtfs/bengaluru_bmtc_iudx_full_gtfs.zip",
            "quality_checks": {
                "route_geometry_ready": True,
                "stop_count": 4433,
                "route_count": 4271,
                "trip_count": 100,
                "stop_time_count": 900,
                "trips_with_two_or_more_stops": 100,
                "max_stops_per_trip": 48,
            },
        }

        row = bmtc_iudx_recipe.build_bmtc_iudx_manifest_feed_row(provenance)

        self.assertEqual(
            row,
            {
                "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
                "city": "bengaluru",
                "mode": "bus",
                "operator": "Bangalore Metropolitan Transport Corporation",
                "status": "ok",
                "source_url": "https://catalogue.iudx.org.in/bengaluru",
                "license": "IUDX policy-approved BMTC static GTFS export.",
                "path": "data/cities/bengaluru/source/transit/gtfs/bengaluru_bmtc_iudx_full_gtfs.zip",
                "stop_layer": "bus_stops",
                "route_layer": "bus_routes",
                "stop_features": 4433,
                "route_features": 4271,
                "quality_checks": provenance["quality_checks"],
                "notes": "Replace the gated BMTC IUDX row only after this exported GTFS has been converted into public stop and route layers.",
            },
        )

    def test_manifest_feed_row_rejects_non_ready_bmtc_iudx_provenance(self) -> None:
        provenance = {
            "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
            "gtfs_zip": "data/cities/bengaluru/source/transit/gtfs/bengaluru_bmtc_iudx_full_gtfs.zip",
            "quality_checks": {
                "route_geometry_ready": False,
                "stop_count": 4433,
                "route_count": 4271,
                "trip_count": 100,
                "stop_time_count": 100,
                "trips_with_two_or_more_stops": 0,
                "max_stops_per_trip": 1,
            },
        }

        with self.assertRaisesRegex(ValueError, "route_geometry_ready"):
            bmtc_iudx_recipe.build_bmtc_iudx_manifest_feed_row(provenance)

    def test_recipe_exports_bmrcl_iudx_schedule_and_network_with_yellow_line_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "bmrcl"
            input_dir.mkdir()
            (input_dir / "stations.json").write_text(
                json.dumps(
                    [
                        {"stop_code": "PP01", "stop_name": "Purple One", "location": {"coordinates": [77.60, 12.90]}},
                        {"stop_code": "PP02", "stop_name": "Purple Two", "location": {"coordinates": [77.61, 12.91]}},
                        {"stop_code": "GR01", "stop_name": "Green One", "location": {"coordinates": [77.58, 13.00]}},
                        {"stop_code": "GR02", "stop_name": "Green Two", "location": {"coordinates": [77.59, 13.01]}},
                        {"stop_code": "YL01", "stop_name": "Yellow One", "location": {"coordinates": [77.62, 12.88]}},
                        {"stop_code": "YL02", "stop_name": "Yellow Two", "location": {"coordinates": [77.63, 12.89]}},
                    ]
                ),
                encoding="utf-8",
            )
            (input_dir / "lines.json").write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "route_id": "Line 1",
                                "route_short_name": "Purple Line",
                                "route_long_name": "Purple corridor",
                                "routeStopSequence": ["PP01", "PP02"],
                                "location": {"coordinates": [[77.60, 12.90], [77.61, 12.91]]},
                            },
                            {
                                "route_id": "Line 2",
                                "route_short_name": "Green Line",
                                "route_long_name": "Green corridor",
                                "routeStopSequence": ["GR01", "GR02"],
                                "location": {"coordinates": [[77.58, 13.00], [77.59, 13.01]]},
                            },
                            {
                                "route_id": "Line 3",
                                "route_short_name": "Yellow Line",
                                "route_long_name": "Yellow corridor",
                                "routeStopSequence": ["YL01", "YL02"],
                                "location": {"coordinates": [[77.62, 12.88], [77.63, 12.89]]},
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (input_dir / "schedule.json").write_text(
                json.dumps(
                    [
                        {"route_id": "Line 1", "train_id": 101, "stationCode": "PP01", "arrival_time": "06:00:00", "departure_time": "06:00:30"},
                        {"route_id": "Line 1", "train_id": 101, "stationCode": "PP02", "arrival_time": "06:05:00", "departure_time": "06:05:30"},
                        {"route_id": "Line 2", "train_id": 201, "stationCode": "GR01", "arrival_time": "06:10:00", "departure_time": "06:10:30"},
                        {"route_id": "Line 2", "train_id": 201, "stationCode": "GR02", "arrival_time": "06:16:00", "departure_time": "06:16:30"},
                        {"route_id": "Line 3", "train_id": 301, "stationCode": "YL01", "arrival_time": "06:20:00", "departure_time": "06:20:30"},
                        {"route_id": "Line 3", "train_id": 301, "stationCode": "YL02", "arrival_time": "06:26:00", "departure_time": "06:26:30"},
                    ]
                ),
                encoding="utf-8",
            )
            out_zip = base / "bengaluru_bmrcl_iudx_full_network_schedule.zip"
            provenance = base / "bmrcl.sources.json"
            manifest_row = base / "bmrcl.feed.json"
            feed_manifest = base / "bmrcl.manifest.json"

            result = bmrcl_iudx_recipe.build_bmrcl_iudx_gtfs_from_exports(
                input_dir=input_dir,
                out_zip=out_zip,
                provenance_path=provenance,
                manifest_row_path=manifest_row,
                feed_manifest_path=feed_manifest,
                generated_at="2026-07-05T01:25:00Z",
            )

            self.assertEqual(result["feed_id"], "bengaluru_bmrcl_iudx_full_network_schedule")
            self.assertEqual(result["quality_checks"]["route_short_names"], ["Purple Line", "Green Line", "Yellow Line"])
            self.assertEqual(result["quality_checks"]["missing_operational_route_short_names"], [])
            self.assertTrue(result["quality_checks"]["route_geometry_ready"])
            with zipfile.ZipFile(out_zip) as zf:
                self.assertIn("stop_times.txt", zf.namelist())
                self.assertIn("shapes.txt", zf.namelist())
                self.assertIn("Yellow Line", zf.read("routes.txt").decode("utf-8"))
            feed_row = json.loads(manifest_row.read_text(encoding="utf-8"))
            self.assertEqual(feed_row["feed_id"], "bengaluru_bmrcl_iudx_full_network_schedule")
            self.assertEqual(feed_row["status"], "ok")
            self.assertEqual(feed_row["route_features"], 3)
            manifest = json.loads(feed_manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest["feeds"], [feed_row])

    def test_bmrcl_manifest_feed_row_rejects_missing_yellow_line(self) -> None:
        provenance = {
            "gtfs_zip": "data/cities/bengaluru/source/transit/gtfs/bengaluru_bmrcl_iudx_full_network_schedule.zip",
            "quality_checks": {
                "route_geometry_ready": True,
                "stop_count": 45,
                "route_count": 2,
                "trip_count": 4,
                "stop_time_count": 40,
                "route_short_names": ["Purple Line", "Green Line"],
                "missing_operational_route_short_names": ["Yellow Line"],
            },
        }

        with self.assertRaisesRegex(ValueError, "Yellow Line"):
            bmrcl_iudx_recipe.build_bmrcl_iudx_manifest_feed_row(provenance)

    def test_bmrcl_quality_requires_scheduled_trips_for_each_operational_line(self) -> None:
        tables = bmrcl_iudx_recipe.build_bmrcl_gtfs_tables(
            stations=[
                {"stop_code": "PP01", "stop_name": "Purple One", "location": {"coordinates": [77.60, 12.90]}},
                {"stop_code": "PP02", "stop_name": "Purple Two", "location": {"coordinates": [77.61, 12.91]}},
                {"stop_code": "GR01", "stop_name": "Green One", "location": {"coordinates": [77.58, 13.00]}},
                {"stop_code": "GR02", "stop_name": "Green Two", "location": {"coordinates": [77.59, 13.01]}},
                {"stop_code": "YL01", "stop_name": "Yellow One", "location": {"coordinates": [77.62, 12.88]}},
                {"stop_code": "YL02", "stop_name": "Yellow Two", "location": {"coordinates": [77.63, 12.89]}},
            ],
            lines=[
                {
                    "route_id": "Line 1",
                    "route_short_name": "Purple Line",
                    "route_long_name": "Purple corridor",
                    "routeStopSequence": ["PP01", "PP02"],
                    "location": {"coordinates": [[77.60, 12.90], [77.61, 12.91]]},
                },
                {
                    "route_id": "Line 2",
                    "route_short_name": "Green Line",
                    "route_long_name": "Green corridor",
                    "routeStopSequence": ["GR01", "GR02"],
                    "location": {"coordinates": [[77.58, 13.00], [77.59, 13.01]]},
                },
                {
                    "route_id": "Line 3",
                    "route_short_name": "Yellow Line",
                    "route_long_name": "Yellow corridor",
                    "routeStopSequence": ["YL01", "YL02"],
                    "location": {"coordinates": [[77.62, 12.88], [77.63, 12.89]]},
                },
            ],
            schedule=[
                {"route_id": "Line 1", "train_id": 101, "stationCode": "PP01", "arrival_time": "06:00:00", "departure_time": "06:00:30"},
                {"route_id": "Line 1", "train_id": 101, "stationCode": "PP02", "arrival_time": "06:05:00", "departure_time": "06:05:30"},
                {"route_id": "Line 2", "train_id": 201, "stationCode": "GR01", "arrival_time": "06:10:00", "departure_time": "06:10:30"},
                {"route_id": "Line 2", "train_id": 201, "stationCode": "GR02", "arrival_time": "06:16:00", "departure_time": "06:16:30"},
            ],
            generated_at="2026-07-05T01:25:00Z",
        )

        quality = bmrcl_iudx_recipe.summarize_bmrcl_quality(tables)

        self.assertEqual(quality["route_short_names"], ["Purple Line", "Green Line", "Yellow Line"])
        self.assertEqual(quality["missing_operational_route_short_names"], [])
        self.assertEqual(quality["scheduled_operational_route_short_names"], ["Purple Line", "Green Line"])
        self.assertEqual(quality["missing_scheduled_operational_route_short_names"], ["Yellow Line"])
        self.assertFalse(quality["coverage_complete"])
        self.assertFalse(quality["route_geometry_ready"])
        with self.assertRaisesRegex(ValueError, "Yellow Line"):
            bmrcl_iudx_recipe.build_bmrcl_iudx_manifest_feed_row(
                {
                    "gtfs_zip": "data/cities/bengaluru/source/transit/gtfs/bengaluru_bmrcl_iudx_full_network_schedule.zip",
                    "quality_checks": quality,
                }
            )


if __name__ == "__main__":
    unittest.main()
