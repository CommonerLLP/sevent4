import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, Polygon

from sevent4.application.metrics import build_ward_service_access
from sevent4.metrics.ward_service_access import build_metrics
from sevent4.ports.metrics import WardServiceAccessInput


class MetricsPortsTest(unittest.TestCase):
    def test_ward_service_access_application_builds_rows_without_file_io(self) -> None:
        class Writer:
            def __init__(self) -> None:
                self.rows = None

            def write_rows(self, rows) -> None:
                self.rows = rows

        inputs = WardServiceAccessInput(
            wards=_wards(),
            crs_metric="EPSG:3857",
            service_points={
                "libraries": _points((0.25, 0.25)),
                "schools": _points((0.25, 0.25), (2.25, 0.25)),
                "health": _points((2.25, 0.25)),
                "toilets": _points(),
                "police": _points(),
                "fire": _points(),
                "universities": _points(),
                "gtfs_stops": _points((0.25, 0.25), (2.25, 0.25)),
            },
            builtup=None,
            population=None,
        )
        writer = Writer()

        result = build_ward_service_access(inputs, writer)

        self.assertEqual(writer.rows, result.rows)
        by_name = {row["Name"]: row for row in result.rows}
        self.assertEqual(by_name["North"]["libraries"], 1)
        self.assertEqual(by_name["North"]["schools"], 1)
        self.assertEqual(by_name["South"]["libraries"], 0)
        self.assertEqual(by_name["South"]["schools"], 1)
        self.assertEqual(by_name["South"]["health"], 1)
        self.assertIn("service_priority", by_name["North"])

    def test_build_metrics_cli_boundary_uses_file_adapter_and_writes_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            city_yaml, out = _write_city_fixture(Path(tmp))

            build_metrics(str(city_yaml), str(out))

            text = out.read_text(encoding="utf-8")
            self.assertIn("Name,ward_area_km2,builtup_km2,population_cells_proxy", text)
            self.assertIn("North", text)
            self.assertIn("South", text)


def _wards() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"Name": ["North", "South"]},
        geometry=[
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
        ],
        crs=4326,
    )


def _points(*coords: tuple[float, float]) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(geometry=[Point(lon, lat) for lon, lat in coords], crs=4326)


def _write_city_fixture(base: Path) -> tuple[Path, Path]:
    repo = base / "repo"
    city_dir = repo / "data" / "cities" / "testville"
    source_dir = city_dir / "source"
    out_dir = repo / "public" / "cities" / "testville"
    (source_dir / "amc").mkdir(parents=True)
    (source_dir / "services").mkdir(parents=True)
    (source_dir / "transit").mkdir(parents=True)
    out_dir.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
    _wards().to_file(source_dir / "amc" / "Wards.geojson", driver="GeoJSON")
    _points((0.25, 0.25)).to_file(source_dir / "amc" / "Library.geojson", driver="GeoJSON")
    (source_dir / "services" / "schools.json").write_text('[{"lon":0.25,"lat":0.25}]', encoding="utf-8")
    (source_dir / "services" / "health.json").write_text('[{"lon":2.25,"lat":0.25}]', encoding="utf-8")
    (source_dir / "services" / "toilets.json").write_text("[]", encoding="utf-8")
    (source_dir / "services" / "police.json").write_text("[]", encoding="utf-8")
    (source_dir / "services" / "emergency.json").write_text("[]", encoding="utf-8")
    (source_dir / "services" / "civic.json").write_text('{"university":[],"college":[]}', encoding="utf-8")
    (source_dir / "transit" / "gtfs_stops.json").write_text('[{"lon":0.25,"lat":0.25}]', encoding="utf-8")
    (city_dir / "city.yaml").write_text(
        "\n".join(
            [
                "id: testville",
                "name: Testville",
                "country: India",
                "state: State",
                "center: [72.0, 23.0]",
                "bbox: [71.0, 22.0, 73.0, 24.0]",
                "crs_metric: EPSG:3857",
                "layers_dir: data/cities/testville/layers",
                "source_dir: data/cities/testville/source",
                "outputs_dir: public/cities/testville",
            ]
        ),
        encoding="utf-8",
    )
    return city_dir / "city.yaml", out_dir / "ward_service_access.csv"


if __name__ == "__main__":
    unittest.main()
