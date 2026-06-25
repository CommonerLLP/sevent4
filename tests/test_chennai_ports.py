import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINANCE_RECIPE = ROOT / "scripts" / "recipes" / "chennai" / "build_finance.py"
WATER_ACQUIRE_RECIPE = ROOT / "scripts" / "recipes" / "chennai" / "acquire_opencity_water.py"
WATER_BUILD_RECIPE = ROOT / "scripts" / "recipes" / "chennai" / "build_opencity_water_layers.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class ChennaiRecipeArchitectureTest(unittest.TestCase):
    def test_finance_recipe_routes_through_ports(self) -> None:
        imports = _imports(FINANCE_RECIPE)
        for forbidden in (
            "csv",
            "json",
            "os",
            "pathlib",
            "re",
            "sys",
            "urllib.request",
            "geopandas",
        ):
            self.assertNotIn(forbidden, imports, f"{FINANCE_RECIPE} should route {forbidden} through ports")
        self.assertIn("sevent4.adapters.chennai_finance_filesystem", imports)
        self.assertIn("sevent4.application.chennai_finance", imports)
        self.assertIn("sevent4.domain.chennai_finance", imports)

    def test_water_recipes_route_through_ports(self) -> None:
        expectations = {
            WATER_ACQUIRE_RECIPE: (
                "sevent4.adapters.chennai_opencity_water_filesystem",
                "sevent4.application.chennai_opencity_water",
                "sevent4.domain.chennai_opencity_water",
            ),
            WATER_BUILD_RECIPE: (
                "sevent4.adapters.chennai_opencity_water_filesystem",
                "sevent4.application.chennai_opencity_water",
                "sevent4.domain.chennai_opencity_water",
            ),
        }
        for recipe, required in expectations.items():
            imports = _imports(recipe)
            for forbidden in (
                "hashlib",
                "json",
                "pathlib",
                "re",
                "requests",
                "geopandas",
                "shapely",
                "pyogrio.raw",
            ):
                self.assertNotIn(forbidden, imports, f"{recipe} should route {forbidden} through ports")
            for module in required:
                self.assertIn(module, imports)


class ChennaiFinanceApplicationTest(unittest.TestCase):
    def test_build_finance_layer_acquires_sources_and_writes_zone_outputs(self) -> None:
        from sevent4.application.chennai_finance import build_finance_layer

        class Store:
            def read_catalogue(self) -> dict:
                return {
                    "datasets": [
                        {
                            "title": "Great Chennai Corporation Finances",
                            "resources": [
                                {"name": "Zones 1 Capital", "url": "https://example.test/zones.csv"},
                                {"name": "Summary Statement", "url": "https://example.test/summary.csv"},
                            ],
                        }
                    ]
                }

            def fetch_finance_resource(self, filename: str, url: str) -> int:
                self.fetch = getattr(self, "fetch", [])
                self.fetch.append((filename, url))
                return 200

            def read_finance_tables(self, resources: list[dict]) -> list[tuple[str, object]]:
                self.resources = resources
                return [
                    (
                        "Zones 1 Capital",
                        [
                            {
                                "Zone": "Zone I",
                                "2013-14  Actuals": "1,000",
                                "Account Head": "Roads",
                                "Minor Account": "",
                            },
                            {
                                "Zone": "Zone I",
                                "2013-14  Actuals": "250",
                                "Account Head": "GoTN Specific Grants",
                                "Minor Account": "Specific Grants",
                            },
                        ],
                    ),
                    ("Summary Statement", [["", "Revenue Receipts", "", "", "12,500"]]),
                ]

            def read_zone_features(self) -> list[dict]:
                return [
                    {
                        "zone_no": "I",
                        "zone_name": "Zone I",
                        "geometry": {"type": "Point", "coordinates": [80.2, 13.0]},
                    }
                ]

            def write_zone_finance_layer(self, feature_collection: dict) -> None:
                self.feature_collection = feature_collection

            def write_budget_summary(self, budget: dict) -> None:
                self.budget = budget

            def write_finance_sources(self, sources: dict) -> None:
                self.sources = sources

        store = Store()
        result = build_finance_layer(store)

        self.assertEqual(store.fetch[0], ("Zones_1_Capital.csv", "https://example.test/zones.csv"))
        feature = store.feature_collection["features"][0]
        self.assertEqual(feature["properties"]["capex_lakh"], 1250.0)
        self.assertEqual(feature["properties"]["capex_cr"], 12.5)
        self.assertEqual(feature["properties"]["state_grant_pct"], 20)
        self.assertEqual(store.budget["lines"]["Revenue Receipts"], 12500.0)
        self.assertEqual(store.sources["layer"], "zone_finance")
        self.assertEqual(result["zones"], 1)


class ChennaiOpenCityWaterApplicationTest(unittest.TestCase):
    def test_acquire_water_resources_downloads_only_machine_readable_geo(self) -> None:
        from sevent4.application.chennai_opencity_water import acquire_water_resources

        class Store:
            def package_show(self, slug: str) -> dict:
                self.slug = slug
                return {
                    "success": True,
                    "result": {
                        "organization": {"title": "Greater Chennai Corporation"},
                        "license_title": "Public Domain",
                        "resources": [
                            {"id": "k1", "name": "Flood Map", "format": "KML", "url": "https://example.test/flood.kml"},
                            {"id": "p1", "name": "Ward PDF", "format": "PDF", "url": "https://example.test/ward.pdf"},
                        ],
                    },
                }

            def fetch_water_resource(self, slug: str, filename: str, url: str) -> dict:
                self.fetch = (slug, filename, url)
                return {"bytes": 99, "sha256": "abc", "status": "ok"}

            def write_water_manifest(self, summary: dict) -> None:
                self.summary = summary

        store = Store()
        result = acquire_water_resources(store, slugs=["chennai-flooding-data"])

        self.assertEqual(store.slug, "chennai-flooding-data")
        self.assertEqual(store.fetch, ("chennai-flooding-data", "Flood_Map.kml", "https://example.test/flood.kml"))
        self.assertEqual(result["downloaded"], 1)
        self.assertEqual(store.summary["resources"][0]["license"], "Public Domain")

    def test_build_water_layers_records_missing_and_built_layers(self) -> None:
        from sevent4.application.chennai_opencity_water import build_water_layers

        class Store:
            def source_exists(self, spec: dict) -> bool:
                return spec["id"] == "flood_hazard"

            def build_curated_layer(self, spec: dict) -> dict:
                self.built = spec["id"]
                return {"status": "ok", "features": 3, "geom_types": {"Polygon": 3}, "attrs": ["CATEGORY"], "bytes": 400}

            def write_water_build_report(self, rows: list[dict]) -> None:
                self.report = rows

        curated = [
            {"id": "flood_hazard", "slug": "chennai-flooding-data", "file": "Flood.kml", "pub": "GCC"},
            {"id": "missing_layer", "slug": "missing", "file": "Missing.kml", "pub": "GCC"},
        ]
        store = Store()
        result = build_water_layers(store, curated=curated)

        self.assertEqual(store.built, "flood_hazard")
        self.assertEqual(result["ok"], 1)
        self.assertEqual(result["total"], 2)
        self.assertEqual(store.report[1]["status"], "missing_raw")


if __name__ == "__main__":
    unittest.main()
