import json
import tempfile
import unittest
from pathlib import Path

from sevent4.application.metrics import build_service_access_composite, build_ward_transit_frequency
from sevent4.adapters.metrics_filesystem import (
    FileServiceAccessCompositeInputRepository,
    FileWardTransitFrequencyInputRepository,
    GeoJsonServiceAccessCompositeWriter,
    GeoJsonWardTransitFrequencyWriter,
)
from sevent4.ports.metrics import ServiceAccessCompositeInput, WardTransitFrequencyInput


class AhmedabadMetricsPortsTest(unittest.TestCase):
    def test_transit_frequency_application_scores_wards_without_file_io(self) -> None:
        class Writer:
            def __init__(self) -> None:
                self.document = None

            def write_wards(self, document) -> None:
                self.document = document

        writer = Writer()
        result = build_ward_transit_frequency(
            WardTransitFrequencyInput(
                wards=_ward_document(),
                gtfs_routes=[{"route_id": "r1", "agency_id": "AMTS"}, {"route_id": "r2", "agency_id": "AJL"}],
                gtfs_trips=[{"route_id": "r1", "trip_id": "t1"}, {"route_id": "r2", "trip_id": "t2"}],
                gtfs_stops=[
                    {"stop_id": "inside", "stop_lon": "0.5", "stop_lat": "0.5"},
                    {"stop_id": "near", "stop_lon": "1.99", "stop_lat": "0.01"},
                    {"stop_id": "far", "stop_lon": "20", "stop_lat": "20"},
                ],
                gtfs_stop_times=[
                    {"trip_id": "t1", "stop_id": "inside"},
                    {"trip_id": "t1", "stop_id": "inside"},
                    {"trip_id": "t1", "stop_id": "near"},
                    {"trip_id": "t1", "stop_id": "far"},
                    {"trip_id": "t2", "stop_id": "inside"},
                ],
                buffer_m=2_500,
            ),
            writer,
        )

        self.assertEqual(writer.document, result.document)
        by_name = {feature["properties"]["Name"]: feature for feature in result.document["features"]}
        self.assertEqual(by_name["Core"]["properties"]["amts_buses_day"], 2)
        self.assertEqual(by_name["Core"]["properties"]["brts_stops"], 1)
        self.assertEqual(by_name["Edge"]["properties"]["amts_buses_day"], 1)
        self.assertEqual(by_name["Edge"]["properties"]["amts_buses_day_core"], 0)
        self.assertEqual(result.summary["strict_assigned_stops"], 1)
        self.assertEqual(result.summary["outside_ward_stops"], 2)
        self.assertEqual(result.summary["reassigned_stops"], 1)

    def test_transit_frequency_excludes_non_numeric_deprivation(self) -> None:
        gtfs = dict(
            gtfs_routes=[{"route_id": "r1", "agency_id": "AMTS"}, {"route_id": "r2", "agency_id": "AJL"}],
            gtfs_trips=[{"route_id": "r1", "trip_id": "t1"}, {"route_id": "r2", "trip_id": "t2"}],
            gtfs_stops=[{"stop_id": "inside", "stop_lon": "0.5", "stop_lat": "0.5"}],
            gtfs_stop_times=[{"trip_id": "t1", "stop_id": "inside"}],
            buffer_m=2_500,
        )

        class _W:
            def write_wards(self, document) -> None:  # noqa: D401
                self.document = document

        baseline = build_ward_transit_frequency(
            WardTransitFrequencyInput(wards=_ward_document(), **gtfs), _W()
        )

        with_blank = _ward_document()
        with_blank["features"].append(
            {
                "type": "Feature",
                "properties": {"Name": "Blank", "deprivation": "N/A"},
                "geometry": {"type": "Polygon", "coordinates": [[(9, 9), (10, 9), (10, 10), (9, 10), (9, 9)]]},
            }
        )
        with_na = build_ward_transit_frequency(
            WardTransitFrequencyInput(wards=with_blank, **gtfs), _W()
        )

        # A non-numeric deprivation ward must be dropped from the equity stats,
        # not coerced to 0.0 (which would read as least-deprived).
        self.assertEqual(
            with_na.summary["deprivation_quartiles"], baseline.summary["deprivation_quartiles"]
        )

    def test_service_access_composite_application_rolls_wards_up_to_acs(self) -> None:
        class Writer:
            def __init__(self) -> None:
                self.wards = None
                self.acs = None

            def write_documents(self, wards, acs) -> None:
                self.wards = wards
                self.acs = acs

        wards = _ward_document()
        wards["features"][0]["properties"].update(
            {"libraries": 2, "schools": 2, "health": 1, "buses_per_stop": 4}
        )
        wards["features"][1]["properties"].update(
            {"libraries": 0, "schools": 1, "health": 0, "buses_per_stop": 1}
        )
        acs = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {"ac_name": "AC Core", "representative": "A", "party": "P"}},
                {"type": "Feature", "properties": {"ac_name": "AC Edge", "representative": "B", "party": "Q"}},
            ],
        }
        writer = Writer()

        result = build_service_access_composite(
            ServiceAccessCompositeInput(
                wards=wards,
                acs=acs,
                crosswalk_records=[
                    {"ward_name": "Core", "ac_name": "AC Core", "overlap_area_m2": 100},
                    {"ward_name": "Edge", "ac_name": "AC Edge", "overlap_area_m2": 100},
                ],
            ),
            writer,
        )

        self.assertEqual(writer.wards, result.wards)
        self.assertEqual(writer.acs, result.acs)
        ward_props = {f["properties"]["Name"]: f["properties"] for f in result.wards["features"]}
        self.assertEqual(ward_props["Core"]["composite_access"], 1.0)
        self.assertEqual(ward_props["Edge"]["composite_gap"], 1.0)
        ac_props = {f["properties"]["ac_name"]: f["properties"] for f in result.acs["features"]}
        self.assertEqual(ac_props["AC Core"]["ac_service_access"], 1.0)
        self.assertEqual(ac_props["AC Edge"]["ac_amc_wards"], 1)

    def test_transit_frequency_filesystem_adapter_loads_gtfs_and_writes_wards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            wards_path = base / "wards.geojson"
            gtfs_dir = base / "gtfs"
            gtfs_dir.mkdir()
            wards_path.write_text(json.dumps(_ward_document()), encoding="utf-8")
            (gtfs_dir / "routes.txt").write_text("route_id,agency_id\nr1,AMTS\n", encoding="utf-8")
            (gtfs_dir / "trips.txt").write_text("route_id,trip_id\nr1,t1\n", encoding="utf-8")
            (gtfs_dir / "stops.txt").write_text(
                "stop_id,stop_lon,stop_lat\ninside,0.5,0.5\n",
                encoding="utf-8",
            )
            (gtfs_dir / "stop_times.txt").write_text("trip_id,stop_id\nt1,inside\n", encoding="utf-8")

            result = build_ward_transit_frequency(
                FileWardTransitFrequencyInputRepository(wards_path, gtfs_dir).load(),
                GeoJsonWardTransitFrequencyWriter(wards_path),
            )

            written = json.loads(wards_path.read_text(encoding="utf-8"))
            self.assertEqual(written, result.document)
            self.assertEqual(written["features"][0]["properties"]["amts_buses_day"], 1)

    def test_transit_frequency_application_accepts_empty_ward_document(self) -> None:
        class Writer:
            def __init__(self) -> None:
                self.document = None

            def write_wards(self, document) -> None:
                self.document = document

        writer = Writer()

        result = build_ward_transit_frequency(
            WardTransitFrequencyInput(
                wards={"type": "FeatureCollection", "features": []},
                gtfs_routes=[],
                gtfs_trips=[],
                gtfs_stops=[],
                gtfs_stop_times=[],
                buffer_m=2_500,
            ),
            writer,
        )

        self.assertEqual(writer.document, {"type": "FeatureCollection", "features": []})
        self.assertEqual(result.summary["service_stops"], 0)
        self.assertEqual(result.summary["deprivation_quartiles"], [])

    def test_service_access_composite_filesystem_adapter_loads_and_writes_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            wards_path = base / "wards.geojson"
            acs_path = base / "acs.geojson"
            crosswalk_path = base / "jurisdiction_crosswalk.json"
            wards = _ward_document()
            wards["features"][0]["properties"].update(
                {"libraries": 1, "schools": 1, "health": 1, "buses_per_stop": 2}
            )
            wards["features"][1]["properties"].update(
                {"libraries": 0, "schools": 0, "health": 0, "buses_per_stop": 0}
            )
            wards_path.write_text(json.dumps(wards), encoding="utf-8")
            acs_path.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [{"type": "Feature", "properties": {"ac_name": "AC Core"}}],
                    }
                ),
                encoding="utf-8",
            )
            crosswalk_path.write_text(
                json.dumps({"records": [{"ward_name": "Core", "ac_name": "AC Core", "overlap_area_m2": 100}]}),
                encoding="utf-8",
            )

            result = build_service_access_composite(
                FileServiceAccessCompositeInputRepository(wards_path, acs_path, crosswalk_path).load(),
                GeoJsonServiceAccessCompositeWriter(wards_path, acs_path),
            )

            self.assertEqual(json.loads(wards_path.read_text(encoding="utf-8")), result.wards)
            self.assertEqual(json.loads(acs_path.read_text(encoding="utf-8")), result.acs)
            self.assertEqual(result.acs["features"][0]["properties"]["ac_service_access"], 1.0)

    def test_service_access_composite_application_accepts_empty_documents(self) -> None:
        class Writer:
            def __init__(self) -> None:
                self.wards = None
                self.acs = None

            def write_documents(self, wards, acs) -> None:
                self.wards = wards
                self.acs = acs

        writer = Writer()

        result = build_service_access_composite(
            ServiceAccessCompositeInput(
                wards={"type": "FeatureCollection", "features": []},
                acs={"type": "FeatureCollection", "features": []},
                crosswalk_records=[],
            ),
            writer,
        )

        self.assertEqual(writer.wards, {"type": "FeatureCollection", "features": []})
        self.assertEqual(writer.acs, {"type": "FeatureCollection", "features": []})
        self.assertEqual(result.summary["wards_scored"], 0)
        self.assertEqual(result.summary["acs_scored"], 0)


def _ward_document() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"Name": "Core", "deprivation": "0.2"},
                "geometry": {"type": "Polygon", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]},
            },
            {
                "type": "Feature",
                "properties": {"Name": "Edge", "deprivation": "0.8"},
                "geometry": {"type": "Polygon", "coordinates": [[(2, 0), (3, 0), (3, 1), (2, 1), (2, 0)]]},
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
