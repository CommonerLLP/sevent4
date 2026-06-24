import ast
import unittest
from pathlib import Path

import pandas as pd

from sevent4.application.delhi_acquire import (
    acquire_gtfs_layers,
    acquire_opencity,
    acquire_osm_layers,
)
from sevent4.domain.delhi_acquire import (
    boundary_credits_md,
    build_routes_from_stop_times,
    build_stops,
    merge_layer_entries,
    osm_lines,
    osm_points,
    overpass_query,
    skipped_opencity_formats,
    slugify,
    usable_opencity_rows,
)

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "scripts" / "recipes" / "delhi"
NAMES = ["acquire_boundaries.py", "acquire_opencity.py", "acquire_osm.py", "acquire_gtfs.py"]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class DelhiAcquireArchitectureTest(unittest.TestCase):
    def test_recipes_do_not_own_io_and_route_through_ports(self) -> None:
        for name in NAMES:
            imports = _imports(RECIPES / name)
            for forbidden in ("requests", "geopandas", "pandas", "json", "csv", "zipfile", "hashlib"):
                self.assertNotIn(forbidden, imports, f"{name} should not own {forbidden} IO")
            self.assertTrue(
                any(m.startswith("sevent4.adapters.delhi_acquire") for m in imports),
                f"{name} should route through the delhi-acquire adapter",
            )
            self.assertIn("sevent4.application.delhi_acquire", imports, f"{name} should use the application")


class DelhiAcquireDomainTest(unittest.TestCase):
    def test_slugify(self) -> None:
        self.assertEqual(slugify("A b/c!", "fb"), "A_b_c")
        self.assertEqual(slugify("", "fb"), "fb")

    def test_overpass_query_appends_bbox(self) -> None:
        q = overpass_query('node["x"];', bbox=(1, 2, 3, 4))
        self.assertTrue(q.startswith("[out:json][timeout:90];("))
        self.assertIn('node["x"](1,2,3,4);', q)
        self.assertTrue(q.endswith(");out geom;"))

    def test_osm_points_and_lines(self) -> None:
        data = {"elements": [
            {"type": "node", "lon": 1.0, "lat": 2.0, "tags": {"name": "P"}},
            {"type": "way", "geometry": [{"lon": 1.0, "lat": 2.0}, {"lon": 3.0, "lat": 4.0}], "tags": {"name": "L"}},
        ]}
        pts = osm_points(data, "name")
        lns = osm_lines(data, "name")
        self.assertEqual(len(pts["features"]), 1)
        self.assertEqual(pts["features"][0]["geometry"]["coordinates"], [1.0, 2.0])
        self.assertEqual(len(lns["features"]), 1)
        self.assertEqual(lns["features"][0]["properties"]["name"], "L")

    def test_merge_layer_entries_is_idempotent(self) -> None:
        manifest = {"layers": [{"id": "a"}]}
        merge_layer_entries(manifest, [{"id": "a", "v": 1}, {"id": "b", "v": 2}])
        merge_layer_entries(manifest, [{"id": "b", "v": 3}])
        ids = [layer["id"] for layer in manifest["layers"]]
        self.assertEqual(ids, ["a", "b"])
        self.assertEqual(manifest["layers"][1]["v"], 3)

    def test_opencity_filters(self) -> None:
        rows = [
            {"resource_format": "CSV", "resource_url": "u"},
            {"resource_format": "PDF", "resource_url": "u"},
            {"resource_format": "CSV", "resource_url": ""},
        ]
        self.assertEqual(len(usable_opencity_rows(rows)), 1)
        self.assertEqual(skipped_opencity_formats(rows), ["PDF"])

    def test_boundary_credits_md(self) -> None:
        from sevent4.domain.delhi_acquire import BOUNDARY_SOURCES

        md = boundary_credits_md(BOUNDARY_SOURCES, {"acs": 70, "pcs": 7, "wards": 290, "districts": 0})
        self.assertIn("| ACs | 70 |", md)
        self.assertIn("Ward caveat", md)


class DelhiAcquireApplicationTest(unittest.TestCase):
    def test_acquire_osm_layers_writes_and_registers(self) -> None:
        manifest = {"layers": []}
        written = {}

        def post(query):
            return {"elements": [{"type": "node", "lon": 1.0, "lat": 2.0, "tags": {"name": "x"}},
                                 {"type": "way", "geometry": [{"lon": 1, "lat": 2}, {"lon": 3, "lat": 4}]}]}

        def write_layer(fc, lid):
            written[lid] = len(fc["features"])
            return len(fc["features"])

        counts = acquire_osm_layers(post, write_layer, manifest)
        self.assertIn("metro_lines", counts)
        self.assertIn("metro", counts)
        self.assertTrue(any(layer["id"] == "metro" for layer in manifest["layers"]))

    def test_acquire_gtfs_layers_reconstructs_from_stop_times(self) -> None:
        tables = {
            "routes": pd.DataFrame([{"route_id": "R1", "route_short_name": "1", "route_long_name": "L",
                                     "agency_id": "A", "route_type": "3"}]),
            "trips": pd.DataFrame([{"trip_id": "T1", "route_id": "R1"}]),
            "stops": pd.DataFrame([{"stop_id": "S1", "stop_lon": "1.0", "stop_lat": "2.0", "stop_name": "a", "stop_code": ""},
                                   {"stop_id": "S2", "stop_lon": "3.0", "stop_lat": "4.0", "stop_name": "b", "stop_code": ""}]),
            "stop_times": pd.DataFrame([{"trip_id": "T1", "stop_id": "S1", "stop_sequence": "1"},
                                        {"trip_id": "T1", "stop_id": "S2", "stop_sequence": "2"}]),
        }
        written = {}
        n_routes, n_stops, method = acquire_gtfs_layers(
            tables, lambda fc, base: written.setdefault(base, len(fc["features"])) or len(fc["features"]), "bus"
        )
        self.assertEqual(method, "reconstructed from stop_times")
        self.assertEqual(n_stops, 2)
        self.assertEqual(n_routes, 1)

    def test_acquire_opencity_records_status(self) -> None:
        rows = [{"resource_format": "CSV", "resource_url": "u", "dataset_name": "DS", "dataset_title": "DS T",
                 "resource_name": "r", "resource_id": "rid", "organization": "org", "axis_labels": "decides"}]

        def fetch(url, dest):
            return 10, "abc"

        manifest, skipped = acquire_opencity(rows, fetch, lambda ds, fn: (f"/x/{ds}/{fn}", f"rel/{ds}/{fn}"))
        self.assertEqual(manifest["downloaded"], 1)
        self.assertEqual(manifest["resources"][0]["sha256"], "abc")


if __name__ == "__main__":
    unittest.main()
