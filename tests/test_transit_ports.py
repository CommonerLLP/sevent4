import json
import tempfile
import unittest
from pathlib import Path

from sevent4.application.transit import build_gtfs_corridors
from sevent4.ports.transit import GtfsCorridorInput
from sevent4.transit.gtfs_corridors import build_corridors


class TransitPortsTest(unittest.TestCase):
    def test_gtfs_corridor_application_builds_geojson_without_file_io(self) -> None:
        class Writer:
            def __init__(self) -> None:
                self.document = None

            def write_geojson(self, document) -> None:
                self.document = document

        inputs = GtfsCorridorInput(
            stops=[
                {"stop_id": "s1", "stop_lon": "72.1", "stop_lat": "23.1"},
                {"stop_id": "s2", "stop_lon": "72.2", "stop_lat": "23.2"},
            ],
            routes=[
                {
                    "route_id": "r1",
                    "route_short_name": "1",
                    "route_long_name": "Main Road",
                    "agency_id": "AMTS",
                }
            ],
            trips=[{"route_id": "r1", "trip_id": "t1", "shape_id": "shape-a"}],
            shapes=[
                {"shape_id": "shape-a", "shape_pt_sequence": "2", "shape_pt_lon": "72.2", "shape_pt_lat": "23.2"},
                {"shape_id": "shape-a", "shape_pt_sequence": "1", "shape_pt_lon": "72.1", "shape_pt_lat": "23.1"},
            ],
            stop_times=[],
        )
        writer = Writer()

        result = build_gtfs_corridors(inputs, writer)

        self.assertEqual(writer.document, result.document)
        feature = result.document["features"][0]
        self.assertEqual(feature["properties"]["route_id"], "r1")
        self.assertEqual(feature["properties"]["agency_id"], "AMTS")
        self.assertEqual(feature["geometry"]["coordinates"], [[72.1, 23.1], [72.2, 23.2]])

    def test_build_corridors_cli_boundary_uses_file_adapter_and_writes_geojson(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            gtfs_dir = _write_gtfs_fixture(base)
            out = base / "out" / "corridors.geojson"

            build_corridors(gtfs_dir, out)

            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["type"], "FeatureCollection")
            self.assertEqual(len(data["features"]), 1)
            self.assertEqual(data["features"][0]["properties"]["route_short_name"], "1")
            self.assertEqual(data["features"][0]["geometry"]["coordinates"], [[72.1, 23.1], [72.2, 23.2]])


def _write_gtfs_fixture(base: Path) -> Path:
    gtfs_dir = base / "gtfs"
    gtfs_dir.mkdir()
    (gtfs_dir / "stops.txt").write_text(
        "stop_id,stop_lon,stop_lat\ns1,72.1,23.1\ns2,72.2,23.2\n",
        encoding="utf-8",
    )
    (gtfs_dir / "routes.txt").write_text(
        "route_id,route_short_name,route_long_name,agency_id\nr1,1,Main Road,AMTS\n",
        encoding="utf-8",
    )
    (gtfs_dir / "trips.txt").write_text(
        "route_id,trip_id,shape_id\nr1,t1,\n",
        encoding="utf-8",
    )
    (gtfs_dir / "stop_times.txt").write_text(
        "trip_id,stop_id,stop_sequence\nt1,s2,2\nt1,s1,1\n",
        encoding="utf-8",
    )
    return gtfs_dir


if __name__ == "__main__":
    unittest.main()
