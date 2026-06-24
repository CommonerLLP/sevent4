import ast
import unittest
from pathlib import Path

from sevent4.application.kanpur import analyze_kanpur_wards
from sevent4.domain.kanpur_wards import (
    COVERAGE_NOTE,
    HEAT_FIELD_KEYS,
    apply_fields,
    feat_area_km2,
    heat_index,
    tertile_cut,
)

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "scripts" / "recipes" / "kanpur" / "build_ward_analysis.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _square(lon0, lat0, d):
    return {"type": "Polygon", "coordinates": [[
        [lon0, lat0], [lon0 + d, lat0], [lon0 + d, lat0 + d], [lon0, lat0 + d], [lon0, lat0],
    ]]}


class KanpurRecipeArchitectureTest(unittest.TestCase):
    def test_recipe_routes_through_ports(self) -> None:
        imports = _imports(RECIPE)
        for forbidden in ("json", "math"):
            self.assertNotIn(forbidden, imports, f"recipe should not own {forbidden} IO")
        self.assertIn("sevent4.adapters.kanpur_filesystem", imports)
        self.assertIn("sevent4.application.kanpur", imports)


class KanpurDomainTest(unittest.TestCase):
    def test_feat_area_and_tertile(self) -> None:
        self.assertIsNone(feat_area_km2(None))
        area = feat_area_km2(_square(80.0, 26.45, 0.02))
        self.assertGreater(area, 0)
        self.assertLess(area, 12)  # ~4 km2 -> not suspect
        self.assertEqual(tertile_cut([1, 2, 3]), 2)
        self.assertIsNone(tertile_cut([None, None]))

    def test_heat_index(self) -> None:
        heat = {"features": [{"properties": {"ward_no": 5, "id": "x", "mean_lst_c": 40, "max_lst_c": 45}}]}
        self.assertEqual(heat_index(heat)[(5, "x")], (40, 45))

    def test_apply_fields_matches_on_ward_and_id(self) -> None:
        wards = {"features": [{"properties": {"ward_no": 1, "id": "a", "population_2020": 99, "extra": "no"}}]}
        target = {"features": [{"properties": {"ward_no": 1, "id": "a"}}]}
        apply_fields(target, wards, HEAT_FIELD_KEYS)
        self.assertEqual(target["features"][0]["properties"]["population_2020"], 99)
        self.assertNotIn("extra", target["features"][0]["properties"])  # only named keys copied


class KanpurApplicationTest(unittest.TestCase):
    def test_analyze_flags_suspect_and_vulnerability(self) -> None:
        wards = {"features": [
            {"properties": {"ward_no": 1, "id": "a", "population_2020": 10000},
             "geometry": _square(80.0, 26.45, 0.02)},   # ~4 km2 clean
            {"properties": {"ward_no": 2, "id": "b", "population_2020": 50000},
             "geometry": _square(80.2, 26.45, 0.06)},   # ~> 12 km2 suspect
        ]}
        heat = {"features": [{"properties": {"ward_no": 1, "id": "a", "mean_lst_c": 41.0, "max_lst_c": 46.0}}]}
        result = analyze_kanpur_wards(wards, heat)

        clean, suspect = wards["features"][0]["properties"], wards["features"][1]["properties"]
        self.assertFalse(clean["geometry_suspect"])
        self.assertTrue(suspect["geometry_suspect"])
        self.assertEqual(clean["ward_coverage"], COVERAGE_NOTE)
        self.assertIn("OVERSIZED", suspect["ward_coverage"])
        self.assertIsNotNone(clean["pop_density_km2"])
        self.assertEqual(clean["mean_lst_c"], 41.0)
        self.assertTrue(clean["heat_vulnerable"])      # only clean ward -> its own tertile cut
        self.assertFalse(suspect["heat_vulnerable"])   # suspect never vulnerable
        self.assertTrue(any("No city total reported" in line for line in result.summary_lines))


if __name__ == "__main__":
    unittest.main()
