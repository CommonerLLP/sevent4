import ast
import unittest
from pathlib import Path

from sevent4.application.library_exclusion import build_library_exclusion
from sevent4.application.transit import split_corridors_by_agency

ROOT = Path(__file__).resolve().parents[1]
GTFS = ROOT / "scripts" / "recipes" / "ahmedabad" / "build_gtfs_corridors.py"
EXCL = ROOT / "scripts" / "recipes" / "ahmedabad" / "build_library_exclusion.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class MiscRecipeArchitectureTest(unittest.TestCase):
    def test_gtfs_recipe_routes_through_transit_ports(self) -> None:
        imports = _imports(GTFS)
        for forbidden in ("json", "csv", "sys"):
            self.assertNotIn(forbidden, imports, f"build_gtfs_corridors should not own {forbidden} IO")
        self.assertIn("sevent4.adapters.transit_filesystem", imports)
        self.assertIn("sevent4.application.transit", imports)

    def test_library_exclusion_recipe_routes_through_ports(self) -> None:
        imports = _imports(EXCL)
        for forbidden in ("csv", "json", "geopandas", "pandas", "math", "statistics"):
            self.assertNotIn(forbidden, imports, f"build_library_exclusion should not own {forbidden} IO")
        self.assertIn("sevent4.adapters.library_exclusion_filesystem", imports)
        self.assertIn("sevent4.application.library_exclusion", imports)
        self.assertIn("sevent4.domain.library_exclusion", imports)


class TransitSplitTest(unittest.TestCase):
    def test_split_corridors_by_agency_filters_and_reshapes(self) -> None:
        document = {
            "features": [
                {"properties": {"agency_id": "AMTS"}, "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}},
                {"properties": {"agency_id": "AJL"}, "geometry": {"type": "LineString", "coordinates": [[2, 2], [3, 3]]}},
                {"properties": {"agency_id": "OTHER"}, "geometry": {"type": "LineString", "coordinates": []}},
            ]
        }
        splits = split_corridors_by_agency(document, {"AMTS": "a.geojson", "AJL": "b.geojson"})
        self.assertEqual(len(splits["a.geojson"]["features"]), 1)
        self.assertEqual(splits["a.geojson"]["features"][0]["properties"], {"kind": "AMTS"})
        self.assertEqual(len(splits["b.geojson"]["features"]), 1)
        self.assertNotIn("OTHER", str(splits))


class LibraryExclusionApplicationTest(unittest.TestCase):
    def test_build_library_exclusion_enriches_and_summarises(self) -> None:
        wards = {
            "crs": {"name": "x"},
            "features": [
                {"properties": {"Name": "A", "deprivation": 0.1, "population_2020": 100}, "geometry": {"type": "Point", "coordinates": [0, 0]}},
                {"properties": {"Name": "B", "deprivation": 0.9, "population_2020": 500}, "geometry": {"type": "Point", "coordinates": [1, 1]}},
            ],
        }
        km = {"A": 0.0, "B": 4.0}
        result = build_library_exclusion(km, wards)
        # B is above both medians -> double-locked; A is below.
        by_name = {r["Name"]: r for r in result.indexed}
        self.assertEqual(by_name["B"]["double_locked"], "True")
        self.assertEqual(by_name["A"]["double_locked"], "False")
        self.assertEqual(result.summary["people_in_double_locked"], 500)
        # additive write-back onto ward properties
        self.assertIn("exclusion_index", wards["features"][1]["properties"])
        self.assertEqual(result.exclusion_layer["crs"], {"name": "x"})
        self.assertTrue(any("double-locked:" in line for line in result.report_lines))


if __name__ == "__main__":
    unittest.main()
