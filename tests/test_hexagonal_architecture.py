import ast
import importlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_DOC = ROOT / "docsx" / "system-architecture-2026-06-22.md"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class HexagonalArchitectureTest(unittest.TestCase):
    def test_layer_packages_are_explicit(self) -> None:
        for module in (
            "sevent4.domain.evidence",
            "sevent4.domain.pollution",
            "sevent4.domain.budget",
            "sevent4.ports.acquisition",
            "sevent4.ports.budget",
            "sevent4.ports.evidence",
            "sevent4.ports.finance",
            "sevent4.ports.jurisdiction",
            "sevent4.ports.library_access",
            "sevent4.ports.metrics",
            "sevent4.ports.publication",
            "sevent4.ports.representatives",
            "sevent4.ports.transit",
            "sevent4.ports.city_build",
            "sevent4.application.city_console",
            "sevent4.application.acquisition",
            "sevent4.application.city_build",
            "sevent4.application.finance",
            "sevent4.application.jurisdiction",
            "sevent4.application.library_access",
            "sevent4.application.metrics",
            "sevent4.application.public_site",
            "sevent4.application.representatives",
            "sevent4.application.transit",
            "sevent4.application.why_air",
            "sevent4.application.budget",
            "sevent4.adapters.budget_filesystem",
            "sevent4.adapters.budget_http",
            "sevent4.adapters.budget_ocr",
            "sevent4.adapters.finance_filesystem",
            "sevent4.adapters.jurisdiction_geospatial",
            "sevent4.adapters.library_access_filesystem",
            "sevent4.adapters.acquisition_filesystem",
            "sevent4.adapters.filesystem",
            "sevent4.adapters.metrics_filesystem",
            "sevent4.adapters.representatives_filesystem",
            "sevent4.adapters.transit_filesystem",
            "sevent4.adapters.city_build_filesystem",
        ):
            importlib.import_module(module)

    def test_domain_layer_has_no_adapter_or_io_imports(self) -> None:
        forbidden_roots = {
            "pathlib",
            "shutil",
            "subprocess",
            "requests",
            "playwright",
            "selenium",
            "scripts",
            "sevent4.adapters",
            "sevent4.application",
        }
        for path in (ROOT / "sevent4" / "domain").glob("*.py"):
            if path.name == "__init__.py":
                continue
            bad = {
                name
                for name in _imports(path)
                if name in forbidden_roots or any(name.startswith(f"{root}.") for root in forbidden_roots)
            }
            self.assertEqual(bad, set(), f"{path} imports adapter/IO modules: {sorted(bad)}")

    def test_application_layer_has_no_recipe_or_network_imports(self) -> None:
        forbidden_roots = {
            "requests",
            "playwright",
            "selenium",
            "subprocess",
            "scripts",
            "sevent4.adapters",
        }
        for path in (ROOT / "sevent4" / "application").glob("*.py"):
            if path.name == "__init__.py":
                continue
            bad = {
                name
                for name in _imports(path)
                if name in forbidden_roots or any(name.startswith(f"{root}.") for root in forbidden_roots)
            }
            self.assertEqual(bad, set(), f"{path} imports adapter modules: {sorted(bad)}")

    def test_library_comparator_recipes_reuse_csv_filesystem_adapter(self) -> None:
        for path in (
            ROOT / "scripts" / "recipes" / "comparators" / "build_library_access_comparison.py",
            ROOT / "scripts" / "recipes" / "comparators" / "build_library_ifla_audit.py",
            ROOT / "scripts" / "recipes" / "comparators" / "build_delhi_toronto_library_comparison.py",
            ROOT / "scripts" / "recipes" / "comparators" / "extract_toronto_public_library.py",
        ):
            imports = _imports(path)
            self.assertNotIn("csv", imports, f"{path} should use the library filesystem adapter for CSV IO")
            self.assertIn("sevent4.adapters.library_access_filesystem", imports)

    def test_devolution_scorecard_recipe_uses_publication_ports(self) -> None:
        path = ROOT / "scripts" / "recipes" / "build_devolution_scorecard.py"
        imports = _imports(path)

        self.assertNotIn("json", imports, f"{path} should not own scorecard JSON IO")
        self.assertIn("sevent4.adapters.filesystem", imports)
        self.assertIn("sevent4.application.public_site", imports)

    def test_jurisdiction_crosswalk_recipes_use_geospatial_adapter(self) -> None:
        for path in (
            ROOT / "scripts" / "recipes" / "build_jurisdiction_crosswalk.py",
            ROOT / "scripts" / "recipes" / "ahmedabad" / "build_jurisdiction_crosswalk.py",
        ):
            imports = _imports(path)
            self.assertNotIn("json", imports, f"{path} should not own crosswalk JSON IO")
            self.assertNotIn("geopandas", imports, f"{path} should not own geospatial joins")
            self.assertIn("sevent4.adapters.jurisdiction_geospatial", imports)
            self.assertIn("sevent4.application.jurisdiction", imports)

    def test_ahmedabad_service_metric_recipes_use_metrics_adapter(self) -> None:
        for path in (
            ROOT / "scripts" / "recipes" / "ahmedabad" / "build_ward_transit_frequency.py",
            ROOT / "scripts" / "recipes" / "ahmedabad" / "build_service_access_composite.py",
        ):
            imports = _imports(path)
            self.assertNotIn("json", imports, f"{path} should not own GeoJSON/JSON IO")
            self.assertNotIn("csv", imports, f"{path} should not own GTFS CSV IO")
            self.assertIn("sevent4.adapters.metrics_filesystem", imports)
            self.assertIn("sevent4.application.metrics", imports)

    def test_ahmedabad_representative_recipes_use_representative_adapter(self) -> None:
        for path in (
            ROOT / "scripts" / "recipes" / "ahmedabad" / "fetch_city_representatives.py",
            ROOT / "scripts" / "recipes" / "ahmedabad" / "parse_city_representatives.py",
        ):
            imports = _imports(path)
            self.assertNotIn("json", imports, f"{path} should not own representative JSON IO")
            self.assertNotIn("csv", imports, f"{path} should not own councillor CSV IO")
            self.assertNotIn("subprocess", imports, f"{path} should not own representative subprocess IO")
            self.assertIn("sevent4.adapters.representatives_filesystem", imports)
            self.assertIn("sevent4.application.representatives", imports)

    def test_generic_city_build_recipe_uses_city_build_adapter(self) -> None:
        path = ROOT / "scripts" / "recipes" / "build_city.py"
        imports = _imports(path)

        self.assertNotIn("json", imports, f"{path} should not own city-build JSON IO")
        self.assertNotIn("csv", imports, f"{path} should not own councillor CSV IO")
        self.assertIn("sevent4.adapters.city_build_filesystem", imports)
        self.assertIn("sevent4.application.city_build", imports)

    def test_why_air_application_builds_roster_without_filesystem_writer(self) -> None:
        from sevent4.application.why_air import build_pollution_board_roster
        from sevent4.domain.pollution import PollutionBoardCapacityRecord

        rows = build_pollution_board_roster(
            [
                PollutionBoardCapacityRecord.from_dict(
                    "bengaluru",
                    {
                        "board": "KSPCB",
                        "facts": [
                            {"metric": "posts_sanctioned", "value": 723, "year": "2025-03", "confidence": "high"},
                            {"metric": "posts_vacant", "value": 437, "year": "2025-03", "confidence": "high"},
                        ],
                        "finance": {
                            "finance_year": "2023-24",
                            "cash_opening_balance_cr": 1292.45,
                        },
                    },
                )
            ]
        )

        self.assertEqual(rows[0]["city"], "bengaluru")
        self.assertEqual(rows[0]["vacancy_pct"], 60)
        self.assertEqual(rows[0]["tier"], "primary")
        self.assertEqual(rows[0]["finance_claim_id"], "claim-why-air-kspcb-finance-2023-24")

    def test_pollution_board_filesystem_adapter_returns_domain_records(self) -> None:
        from sevent4.adapters.filesystem import FilePollutionBoardCapacityRepository
        from sevent4.domain.pollution import PollutionBoardCapacityRecord

        records = FilePollutionBoardCapacityRepository(ROOT / "data" / "cities").list_capacity_records()

        self.assertTrue(records)
        self.assertTrue(all(isinstance(record, PollutionBoardCapacityRecord) for record in records))
        self.assertIn("bengaluru", {record.city for record in records})
        self.assertIn("KSPCB", {record.board for record in records})

    def test_why_air_application_publishes_through_evidence_port(self) -> None:
        from sevent4.application.why_air import build_pollution_board_table
        from sevent4.domain.pollution import PollutionBoardCapacityRecord

        class Repository:
            def list_capacity_records(self):
                return [
                    PollutionBoardCapacityRecord.from_dict(
                        "bengaluru",
                        {
                            "board": "KSPCB",
                            "facts": [
                                {"metric": "posts_sanctioned", "value": 723, "year": "2025-03", "confidence": "high"},
                                {"metric": "posts_vacant", "value": 437, "year": "2025-03", "confidence": "high"},
                            ],
                            "finance": {
                                "finance_year": "2023-24",
                                "cash_opening_balance_cr": 1292.45,
                            },
                        },
                    )
                ]

        document = build_pollution_board_table(Repository())

        self.assertEqual(document["boards"][0]["city"], "bengaluru")
        self.assertEqual(document["boards"][0]["vacancy_pct"], 60)
        self.assertEqual(document["boards"][0]["finance_claim_id"], "claim-why-air-kspcb-finance-2023-24")

    def test_public_site_application_builds_route_graph_without_reading_files(self) -> None:
        from sevent4.application.public_site import build_public_route_graph

        graph = build_public_route_graph(
            {
                "": ["why/index.html", "findings/"],
                "why/": ["../index.html", "air/index.html"],
                "why/air/": ["../../findings/index.html"],
                "findings/": ["../index.html"],
            }
        )

        self.assertEqual(graph[""], {"why/", "findings/"})
        self.assertEqual(graph["why/"], {"", "why/air/"})
        self.assertEqual(graph["why/air/"], {"findings/"})

    def test_city_console_application_publishes_through_surface_port(self) -> None:
        from sevent4.application.city_console import publish_city_console

        class FakeSurface:
            output_dir = Path("public/cities/test")

            def __init__(self) -> None:
                self.events: list[str] = []
                self.html = ""

            def prepare(self) -> None:
                self.events.append("prepare")

            def publish_layers(self, city, manifest) -> None:
                self.events.append(f"layers:{city.id}:{len(manifest.layers)}")

            def write_index(self, html: str) -> None:
                self.events.append("write")
                self.html = html

        class City:
            id = "test"
            name = "Test City"

        class Manifest:
            layers: tuple = ()

        surface = FakeSurface()
        result = publish_city_console(
            City(),
            Manifest(),
            surface,
            lambda city, manifest, output_dir: f"{city.name} -> {output_dir.as_posix()}",
        )

        self.assertEqual(surface.events, ["prepare", "layers:test:0", "write"])
        self.assertEqual(surface.html, "Test City -> public/cities/test")
        self.assertEqual(result.html, "Test City -> public/cities/test")

    def test_city_console_application_publishes_through_input_repository(self) -> None:
        from sevent4.application.city_console import publish_city_console_from_repository
        from sevent4.ports.publication import CityConsoleInput

        class FakeSurface:
            output_dir = Path("public/cities/test")

            def __init__(self) -> None:
                self.events: list[str] = []
                self.html = ""

            def prepare(self) -> None:
                self.events.append("prepare")

            def publish_layers(self, city, manifest) -> None:
                self.events.append(f"layers:{city.id}:{len(manifest.layers)}")

            def write_index(self, html: str) -> None:
                self.events.append("write")
                self.html = html

        class City:
            id = "test"
            name = "Test City"
            layers_dir = Path("data/cities/test/layers")

        class Manifest:
            layers: tuple = ()

        class Repository:
            def load(self) -> CityConsoleInput:
                return CityConsoleInput(city=City(), manifest=Manifest())

        surface = FakeSurface()
        result = publish_city_console_from_repository(
            Repository(),
            surface,
            lambda city, manifest, output_dir: f"{city.name} -> {output_dir.as_posix()}",
        )

        self.assertEqual(surface.events, ["prepare", "layers:test:0", "write"])
        self.assertEqual(result.output_dir, Path("public/cities/test"))
        self.assertEqual(result.html, "Test City -> public/cities/test")

    def test_architecture_doc_names_operational_layers(self) -> None:
        text = ARCHITECTURE_DOC.read_text(encoding="utf-8")

        for name in (
            "sevent4.domain.evidence",
            "sevent4.domain.pollution",
            "sevent4.domain.budget",
            "sevent4.application.why_air",
            "sevent4.application.budget",
            "sevent4.application.city_console",
            "sevent4.application.acquisition",
            "sevent4.application.finance",
            "sevent4.application.jurisdiction",
            "sevent4.application.library_access",
            "sevent4.application.metrics",
            "sevent4.application.public_site",
            "sevent4.application.representatives",
            "sevent4.application.transit",
            "sevent4.ports.acquisition",
            "sevent4.ports.city_build",
            "sevent4.ports.evidence",
            "sevent4.ports.finance",
            "sevent4.ports.jurisdiction",
            "sevent4.ports.library_access",
            "sevent4.ports.metrics",
            "sevent4.ports.publication",
            "sevent4.ports.representatives",
            "sevent4.ports.transit",
            "sevent4.ports.budget",
            "sevent4.adapters.finance_filesystem",
            "sevent4.adapters.acquisition_filesystem",
            "sevent4.adapters.budget_filesystem",
            "sevent4.adapters.budget_http",
            "sevent4.adapters.budget_ocr",
            "sevent4.adapters.city_build_filesystem",
            "sevent4.adapters.filesystem",
            "sevent4.adapters.jurisdiction_geospatial",
            "sevent4.adapters.library_access_filesystem",
            "sevent4.adapters.metrics_filesystem",
            "sevent4.adapters.representatives_filesystem",
            "sevent4.adapters.transit_filesystem",
            "commoner-probe",
            "partial-recall",
            "public-finance",
        ):
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
