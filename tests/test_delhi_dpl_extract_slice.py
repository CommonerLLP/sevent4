import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sevent4.domain.delhi_dpl_extract import ANNUAL_FIELDS

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "scripts" / "recipes" / "delhi" / "extract_dpl_library.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class DelhiDplExtractArchitectureTest(unittest.TestCase):
    def test_recipe_routes_through_extract_ports(self) -> None:
        imports = _imports(RECIPE)
        for forbidden in ("csv", "html", "re"):
            self.assertNotIn(forbidden, imports, f"recipe should not own {forbidden} parsing/IO")
        self.assertIn("sevent4.adapters.delhi_dpl_extract_filesystem", imports)
        self.assertIn("sevent4.application.delhi_dpl_extract", imports)
        self.assertIn("sevent4.domain.delhi_dpl_extract", imports)


class DelhiDplExtractApplicationTest(unittest.TestCase):
    def test_build_dpl_library_writes_manifest_locations_and_metric_tables(self) -> None:
        from sevent4.application.delhi_dpl_extract import build_dpl_library

        class Store:
            def __init__(self) -> None:
                self.writes: dict[str, tuple[list[dict[str, str]], list[str]]] = {}

            def read_tsv(self, path: Path) -> list[dict[str, str]]:
                self.tsv_path = path
                return [
                    {
                        "kind": "annual",
                        "text": "Annual report",
                        "url": "https://example.test/dpl-2023-24.pdf",
                        "local_path": "targeted/text/annual__2023-24.txt",
                        "status": "200",
                        "bytes": "123",
                        "sha256": "abc",
                    }
                ]

            def build_manifest_rows(self, source_dir: Path, manifest: list[dict[str, str]]) -> list[dict[str, str]]:
                self.manifest_source_dir = source_dir
                return [{**manifest[0], "valid_pdf": "", "repo_storage": "manifest_only", "notes": "test"}]

            def extract_dpl_locations(self, html_dir: Path, source_by_stem: dict[str, str]) -> list[dict[str, str]]:
                self.html_dir = html_dir
                self.source_by_stem = source_by_stem
                return [
                    {
                        "source_record_id": "dpl_location_0001",
                        "source_file": "operations__central_zone.html",
                        "source_url": "",
                        "library_id": "dpl_central_library_0001",
                        "name": "Central Library",
                        "normalized_name": "central library",
                        "location_type": "zonal_library",
                        "zone": "central",
                        "address": "Delhi Public Library, Delhi-110006",
                        "latitude": "",
                        "longitude": "",
                        "coordinate_source": "",
                        "map_url": "",
                        "geocode_status": "needs_geocode",
                        "confidence": "medium",
                        "notes": "test",
                    }
                ]

            def extract_annual_rows(self, text_dir: Path, source_by_stem: dict[str, str]) -> list[dict[str, str]]:
                self.text_dir = text_dir
                row = {field: "" for field in ANNUAL_FIELDS}
                row.update(
                    {
                        "year": "2023-24",
                        "source_file": "annual__2023-24.txt",
                        "source_url": source_by_stem["annual__2023-24"],
                        "total_members": "100",
                        "total_issues": "50",
                        "collection_total": "1000",
                        "books_added_to_stock": "10",
                        "total_expenditure_rs": "2000",
                        "confidence": "high",
                        "notes": "test",
                    }
                )
                return [row]

            def primary_delhi_population(self) -> int:
                return 1_000_000

            def write_csv(self, path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
                self.writes[path.name] = (rows, fieldnames)

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = Store()
            result = build_dpl_library(store, root / "source", root / "out", root / "geocode")

        self.assertEqual(store.tsv_path.name, "selected_finance_operations_links.tsv")
        self.assertEqual(store.html_dir.name, "html")
        self.assertEqual(store.text_dir.name, "text")
        self.assertEqual(store.source_by_stem, {"annual__2023-24": "https://example.test/dpl-2023-24.pdf"})
        self.assertEqual(result["annual_rows"], 1)
        self.assertEqual(result["location_rows"], 1)
        self.assertEqual(result["geocode_cache_rows"], 1)
        self.assertEqual(result["ten_year_rows"], 10)
        self.assertEqual(result["online_rows"], 15)
        self.assertIn("dpl_fetch_manifest.csv", store.writes)
        self.assertIn("dpl_library_locations.csv", store.writes)
        self.assertIn("geocode_cache.csv", store.writes)
        self.assertIn("dpl_annual_metrics.csv", store.writes)
        self.assertIn("dpl_ten_year_time_series.csv", store.writes)
        self.assertIn("dpl_online_annual_time_series.csv", store.writes)
        self.assertIn("dpl_metrics_long.csv", store.writes)


if __name__ == "__main__":
    unittest.main()
