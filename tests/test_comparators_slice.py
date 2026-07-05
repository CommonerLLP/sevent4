import ast
import unittest
from pathlib import Path

from sevent4.application.comparators import build_opencity_catalogue, build_suburban_rail
from sevent4.domain.opencity_catalogue import build_catalogue, human_bytes, to_int
from sevent4.domain.suburban_rail import (
    BBOX,
    collect_ways,
    line_features,
    q_rail,
    rail_sources,
    station_features,
    tiles,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "scripts" / "recipes" / "opencity_catalogue.py"
RAIL = ROOT / "scripts" / "recipes" / "transit" / "pull_suburban_rail.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class ComparatorsArchitectureTest(unittest.TestCase):
    def test_recipes_route_through_ports(self) -> None:
        for path, dom in ((CATALOGUE, "sevent4.domain.opencity_catalogue"), (RAIL, "sevent4.domain.suburban_rail")):
            imports = _imports(path)
            for forbidden in ("json", "csv", "urllib.request", "urllib.parse", "requests"):
                self.assertNotIn(forbidden, imports, f"{path.name} should not own {forbidden} IO")
            self.assertIn("sevent4.adapters.comparators_filesystem", imports)
            self.assertIn("sevent4.application.comparators", imports)
            self.assertIn(dom, imports)


class OpenCityCatalogueDomainTest(unittest.TestCase):
    def test_to_int_and_human_bytes(self) -> None:
        self.assertEqual(to_int("12.0"), 12)
        self.assertIsNone(to_int("None"))
        self.assertEqual(human_bytes(0), "?")
        self.assertEqual(human_bytes(2048), "2.0KB")

    def test_build_catalogue_counts_and_formats(self) -> None:
        pkgs = [{
            "name": "d1", "title": "D1", "organization": {"name": "org"}, "groups": [{"name": "delhi"}],
            "tags": [], "notes": "", "metadata_modified": "x",
            "resources": [{"id": "r", "name": "n", "format": "csv", "url": "u", "size": "1024"}],
        }]
        cat = build_catalogue(pkgs)
        self.assertEqual(cat["dataset_count"], 1)
        self.assertEqual(cat["resource_count"], 1)
        self.assertEqual(cat["formats"], {"CSV": 1})  # .strip().upper() repaired
        self.assertEqual(cat["datasets_per_group"], {"delhi": 1})
        self.assertEqual(cat["known_bytes"], 1024)
        _cat, md = build_opencity_catalogue(pkgs)
        self.assertIn("# data.opencity.in — catalogue", md)


class SuburbanRailDomainTest(unittest.TestCase):
    def test_tiles_and_query(self) -> None:
        ts = list(tiles((0, 0, 3, 3), nx=3, ny=3))
        self.assertEqual(len(ts), 9)
        self.assertIn("mumbai", BBOX)
        self.assertIn('railway"="rail"', q_rail((0, 0, 1, 1)))
        self.assertIn("(0,0,1,1)", q_rail((0, 0, 1, 1)))

    def test_collect_and_shape(self) -> None:
        ways: dict = {}
        collect_ways([
            {"type": "way", "id": 1, "geometry": [{"lon": 1, "lat": 2}, {"lon": 3, "lat": 4}], "tags": {"name": "L"}},
            {"type": "way", "id": 1, "geometry": [{"lon": 9, "lat": 9}]},  # dup id ignored
            {"type": "node", "id": 2},  # not a way
        ], ways)
        self.assertEqual(len(ways), 1)
        feats = line_features(ways)
        self.assertEqual(feats[0]["properties"]["name"], "L")
        self.assertEqual(feats[0]["properties"]["decided_by"], "Union (Indian Railways)")
        stations = station_features({5: {"lon": 1.0, "lat": 2.0, "tags": {"name": "Stn"}}})
        self.assertEqual(stations[0]["properties"]["name"], "Stn")
        self.assertEqual(rail_sources("bengaluru")["under_construction"], True)


class ComparatorsApplicationTest(unittest.TestCase):
    def test_build_suburban_rail_with_fake_overpass(self) -> None:
        def fake_overpass(query):
            if 'railway"="rail"' in query:
                return {"elements": [{"type": "way", "id": 1, "geometry": [{"lon": 1, "lat": 2}, {"lon": 3, "lat": 4}], "tags": {}}]}
            return {"elements": [{"type": "node", "id": 9, "lon": 1.0, "lat": 2.0, "tags": {"name": "S"}}]}

        lines_fc, stations_fc, sources, (n_lines, n_stations) = build_suburban_rail("kolkata", fake_overpass)
        self.assertEqual(n_lines, 1)
        self.assertEqual(n_stations, 1)
        self.assertEqual(lines_fc["type"], "FeatureCollection")
        self.assertEqual(sources["layer"], "suburban_rail")


if __name__ == "__main__":
    unittest.main()
