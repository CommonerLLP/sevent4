import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "scripts" / "recipes" / "bengaluru" / "reconcile_wards.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class BengaluruWardAnalysisArchitectureTest(unittest.TestCase):
    def test_reconcile_recipe_routes_through_ports(self) -> None:
        imports = _imports(RECIPE)
        for forbidden in ("json", "re", "geopandas"):
            self.assertNotIn(forbidden, imports, f"recipe should not own {forbidden} reconciliation IO")
        self.assertIn("sevent4.adapters.bengaluru_ward_analysis_geospatial", imports)
        self.assertIn("sevent4.application.bengaluru_ward_analysis", imports)
        self.assertIn("sevent4.domain.bengaluru_ward_analysis", imports)


class BengaluruWardAnalysisApplicationTest(unittest.TestCase):
    def test_reconcile_writes_feature_collection_and_manifest_layer(self) -> None:
        from sevent4.application.bengaluru_ward_analysis import reconcile_ward_analysis

        class Store:
            def ward_analysis_rows(self) -> list[dict]:
                return [
                    {
                        "ward": "Test Ward",
                        "population": 100,
                        "sc_population": 10,
                        "st_population": 5,
                        "assembly": "Test AC",
                        "parliament": "Test PC",
                        "ledger": {
                            "total_nett_cr": 2.5,
                            "top_contractors": [{"name": "Contractor A", "cr": 1.2}],
                            "top_budget_heads": [{"head": "Roads", "cr": 1.2}],
                            "flagged_works": [{"name": "Drain work", "lakh": 12}],
                        },
                        "mean_lst_c": 35.5,
                        "max_lst_c": 42.0,
                        "geometry": {"type": "Point", "coordinates": [77.5, 12.9]},
                    }
                ]

            def write_ward_analysis(self, feature_collection: dict) -> None:
                self.feature_collection = feature_collection

            def read_layer_manifest(self) -> dict:
                return {"layers": []}

            def write_layer_manifest(self, manifest: dict) -> None:
                self.manifest = manifest

        store = Store()
        result = reconcile_ward_analysis(store)

        feature = store.feature_collection["features"][0]
        self.assertEqual(feature["properties"]["sc_st_share_pct"], 15.0)
        self.assertEqual(feature["properties"]["spend_per_resident_rs"], 250000)
        self.assertEqual(store.manifest["layers"][0]["id"], "ward_analysis")
        self.assertEqual(result["wards"], 1)
        self.assertEqual(result["spend_joined"], 1)
        self.assertEqual(result["heat_transferred"], 1)


if __name__ == "__main__":
    unittest.main()
