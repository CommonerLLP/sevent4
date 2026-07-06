import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_RECIPE = ROOT / "scripts" / "recipes" / "bengaluru" / "acquire_boundaries.py"
FINANCE_RECIPE = ROOT / "scripts" / "recipes" / "bengaluru" / "acquire_finance.py"
JURISDICTION_ACQUIRE_RECIPE = ROOT / "scripts" / "recipes" / "bengaluru" / "acquire_opencity_jurisdiction.py"
JURISDICTION_BUILD_RECIPE = ROOT / "scripts" / "recipes" / "bengaluru" / "build_opencity_jurisdiction_layers.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class BengaluruOpenCityAcquisitionArchitectureTest(unittest.TestCase):
    def test_acquisition_recipes_route_through_ports(self) -> None:
        for recipe in (BOUNDARY_RECIPE, FINANCE_RECIPE, JURISDICTION_ACQUIRE_RECIPE, JURISDICTION_BUILD_RECIPE):
            imports = _imports(recipe)
            for forbidden in (
                "hashlib",
                "json",
                "os",
                "re",
                "requests",
                "sys",
                "geopandas",
                "shapely",
                "urllib.request",
                "pyogrio.raw",
            ):
                self.assertNotIn(forbidden, imports, f"{recipe} should route {forbidden} through ports")
            self.assertIn("sevent4.adapters.bengaluru_opencity_filesystem", imports)
            self.assertIn("sevent4.application.bengaluru_opencity", imports)
            self.assertIn("sevent4.domain.bengaluru_opencity", imports)


class BengaluruOpenCityAcquisitionApplicationTest(unittest.TestCase):
    def test_acquire_finance_downloads_only_kept_machine_readable_resources(self) -> None:
        from sevent4.application.bengaluru_opencity import acquire_finance_resources

        class Store:
            def __init__(self) -> None:
                self.downloads = []

            def archive_exists(self) -> bool:
                return True

            def read_catalogue(self) -> dict:
                return {
                    "datasets": [
                        {
                            "name": "bbmp-budget",
                            "title": "BBMP Budget",
                            "organization": "OpenCity",
                            "url": "https://data.opencity.in/dataset/bbmp-budget",
                            "resources": [
                                {"name": "Budget CSV", "format": "CSV", "url": "https://example.test/budget.csv"},
                                {"name": "Budget PDF", "format": "PDF", "url": "https://example.test/budget.pdf"},
                            ],
                        }
                    ]
                }

            def fetch_finance_resource(self, slug: str, filename: str, url: str) -> int:
                self.downloads.append((slug, filename, url))
                return 123

            def write_finance_manifest(self, manifest: list[dict[str, str]]) -> None:
                self.manifest = manifest

        store = Store()
        result = acquire_finance_resources(store, slugs=["bbmp-budget"])

        self.assertEqual(store.downloads, [("bbmp-budget", "Budget_CSV.csv", "https://example.test/budget.csv")])
        self.assertEqual(result["jobs"], 1)
        self.assertEqual(result["done"], 1)
        self.assertEqual(store.manifest[0]["format"], "CSV")
        self.assertEqual(store.manifest[0]["bytes"], 123)

    def test_acquire_finance_falls_back_to_package_show_for_catalogue_miss(self) -> None:
        from sevent4.application.bengaluru_opencity import acquire_finance_resources

        class Store:
            def archive_exists(self) -> bool:
                return True

            def read_catalogue(self) -> dict:
                return {"datasets": []}

            def package_show(self, slug: str) -> dict:
                self.slug = slug
                return {
                    "success": True,
                    "result": {
                        "name": slug,
                        "title": "GBA Corporation Budgets 2026-27",
                        "organization": {"title": "Greater Bengaluru Authority (GBA)"},
                        "resources": [
                            {
                                "name": "Bengaluru Central City Corporation Budget Tables",
                                "format": "XLSX",
                                "url": "https://example.test/bccc.xlsx",
                                "last_modified": "2026-06-17T04:12:04.107941",
                            },
                            {
                                "name": "Budget Book - Bengaluru Central City Corporation",
                                "format": "PDF",
                                "url": "https://example.test/bccc.pdf",
                            },
                        ],
                    },
                }

            def fetch_finance_resource(self, slug: str, filename: str, url: str) -> int:
                self.fetch = (slug, filename, url)
                return 456

            def write_finance_manifest(self, manifest: list[dict[str, str]]) -> None:
                self.manifest = manifest

        store = Store()
        result = acquire_finance_resources(store, slugs=["gba-corporation-budgets-2026-27"])

        self.assertEqual(store.slug, "gba-corporation-budgets-2026-27")
        self.assertEqual(
            store.fetch,
            (
                "gba-corporation-budgets-2026-27",
                "Bengaluru_Central_City_Corporation_Budget_Tables.xlsx",
                "https://example.test/bccc.xlsx",
            ),
        )
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["done"], 1)
        self.assertEqual(store.manifest[0]["publisher_org"], "Greater Bengaluru Authority (GBA)")

    def test_acquire_boundary_spine_fetches_converts_and_writes_credit(self) -> None:
        from sevent4.application.bengaluru_opencity import acquire_boundary_spine

        class Store:
            def __init__(self) -> None:
                self.fetched = []
                self.converted = []

            def fetch_boundary_resource(self, layer_id: str, url: str) -> int:
                self.fetched.append((layer_id, url))
                return 2048

            def convert_boundary_resource(self, layer_id: str, target: str) -> dict:
                self.converted.append((layer_id, target))
                return {"features": 2, "columns": ["Name", "geometry"]}

            def write_boundary_sources(self, provenance: list[dict[str, object]]) -> None:
                self.provenance = provenance

            def write_boundary_credits(self, provenance: list[dict[str, object]]) -> None:
                self.credits = provenance

        spine = {
            "wards": {
                "target": "wards.geojson",
                "dataset": "https://data.opencity.in/dataset/gba",
                "resource": "https://example.test/wards.kml",
                "publisher": "GBA",
                "label": "GBA wards",
            }
        }
        store = Store()
        result = acquire_boundary_spine(store, spine=spine)

        self.assertEqual(store.fetched, [("wards", "https://example.test/wards.kml")])
        self.assertEqual(store.converted, [("wards", "wards.geojson")])
        self.assertEqual(result["layers"], 1)
        self.assertEqual(result["features"], 2)
        self.assertEqual(store.provenance[0]["publisher_org"], "GBA")
        self.assertIs(store.credits, store.provenance)

    def test_acquire_jurisdiction_resources_uses_package_metadata_and_hashing_adapter(self) -> None:
        from sevent4.application.bengaluru_opencity import acquire_jurisdiction_resources

        class Store:
            def package_show(self, slug: str) -> dict:
                self.slug = slug
                return {
                    "success": True,
                    "result": {
                        "organization": {"title": "BDA"},
                        "license_title": "CC-BY",
                        "resources": [
                            {"id": "r1", "name": "BDA Zones", "format": "GEOJSON", "url": "https://example.test/bda.geojson"},
                            {"id": "r2", "name": "Readme", "format": "PDF", "url": "https://example.test/readme.pdf"},
                        ],
                    },
                }

            def fetch_jurisdiction_resource(self, slug: str, filename: str, url: str) -> dict:
                self.fetch = (slug, filename, url)
                return {"bytes": 55, "sha256": "abc", "status": "ok"}

            def write_jurisdiction_manifest(self, summary: dict) -> None:
                self.summary = summary

        store = Store()
        result = acquire_jurisdiction_resources(store, slugs=["bda-jurisdiction-and-boundary"])

        self.assertEqual(store.slug, "bda-jurisdiction-and-boundary")
        self.assertEqual(store.fetch, ("bda-jurisdiction-and-boundary", "BDA_Zones.geojson", "https://example.test/bda.geojson"))
        self.assertEqual(result["downloaded"], 1)
        self.assertEqual(store.summary["resources"][0]["sha256"], "abc")

    def test_build_jurisdiction_layers_records_missing_and_built_layers(self) -> None:
        from sevent4.application.bengaluru_opencity import build_jurisdiction_layers

        class Store:
            def source_exists(self, spec: dict) -> bool:
                return spec["id"] == "gba_corporations"

            def build_curated_layer(self, spec: dict) -> dict:
                self.built = spec["id"]
                return {"status": "ok", "features": 5, "geom_types": {"Polygon": 5}, "attrs": ["Name"], "bytes": 500}

            def write_jurisdiction_build_report(self, rows: list[dict]) -> None:
                self.report = rows

        curated = [
            {"id": "gba_corporations", "slug": "gba", "file": "gba.kml", "pub": "GBA"},
            {"id": "missing_layer", "slug": "missing", "file": "missing.kml", "pub": "BDA"},
        ]
        store = Store()
        result = build_jurisdiction_layers(store, curated=curated)

        self.assertEqual(store.built, "gba_corporations")
        self.assertEqual(result["ok"], 1)
        self.assertEqual(result["total"], 2)
        self.assertEqual(store.report[1]["status"], "missing_raw")


if __name__ == "__main__":
    unittest.main()
