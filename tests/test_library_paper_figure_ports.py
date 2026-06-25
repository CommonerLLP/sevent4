import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AHMEDABAD_RECIPE = ROOT / "scripts" / "make_ahmedabad_library_paper_figures.py"
DELHI_RECIPE = ROOT / "scripts" / "make_delhi_library_paper_figures.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class LibraryPaperFigureArchitectureTest(unittest.TestCase):
    def test_ahmedabad_figure_recipe_routes_through_ports(self) -> None:
        imports = _imports(AHMEDABAD_RECIPE)
        for forbidden in (
            "os",
            "pathlib",
            "geopandas",
            "matplotlib",
            "matplotlib.pyplot",
            "matplotlib.lines",
            "matplotlib.patches",
            "pandas",
            "shapely.ops",
        ):
            self.assertNotIn(forbidden, imports, f"{AHMEDABAD_RECIPE} should route {forbidden} through ports")
        self.assertIn("sevent4.adapters.ahmedabad_library_paper_figures_geospatial", imports)
        self.assertIn("sevent4.application.ahmedabad_library_paper_figures", imports)
        self.assertIn("sevent4.domain.ahmedabad_library_paper_figures", imports)

    def test_delhi_figure_recipe_routes_through_ports(self) -> None:
        imports = _imports(DELHI_RECIPE)
        for forbidden in (
            "pathlib",
            "matplotlib",
            "matplotlib.pyplot",
            "matplotlib.ticker",
            "pandas",
        ):
            self.assertNotIn(forbidden, imports, f"{DELHI_RECIPE} should route {forbidden} through ports")
        self.assertIn("sevent4.adapters.delhi_library_paper_figures_matplotlib", imports)
        self.assertIn("sevent4.application.delhi_library_paper_figures", imports)
        self.assertIn("sevent4.domain.delhi_library_paper_figures", imports)

    def test_delhi_adapter_forces_headless_matplotlib_backend_before_pyplot(self) -> None:
        adapter = ROOT / "sevent4" / "adapters" / "delhi_library_paper_figures_matplotlib.py"
        text = adapter.read_text(encoding="utf-8")
        self.assertIn('mpl.use("Agg")', text)
        self.assertLess(text.index('mpl.use("Agg")'), text.index("import matplotlib.pyplot as plt"))


class AhmedabadLibraryPaperFiguresApplicationTest(unittest.TestCase):
    def test_application_builds_three_figure_stats_without_plotting_imports(self) -> None:
        from sevent4.application.ahmedabad_library_paper_figures import build_ahmedabad_library_paper_figures

        class Store:
            fig = "docs/figures"

            def read_layers(self):
                return ("wards", "libraries", "stops", "metro_stations", "metro_lines", "amts", "brts", "schools", "universities")

            def render_access_proxy(self, wards, libraries):
                self.access_args = (wards, libraries)
                return {"ward_count": 48}

            def render_transit_context(self, *layers):
                self.transit_layers = layers
                return {"bus_stop_400m": 80}

            def render_exclusion_cross(self, wards, libraries):
                self.exclusion_args = (wards, libraries)
                return {"double_locked_wards": 10}

        store = Store()
        result = build_ahmedabad_library_paper_figures(store)

        self.assertEqual(store.access_args, ("wards", "libraries"))
        self.assertEqual(store.transit_layers[2], "stops")
        self.assertEqual(store.exclusion_args, ("wards", "libraries"))
        self.assertEqual(result["access"]["ward_count"], 48)
        self.assertEqual(result["transit"]["bus_stop_400m"], 80)
        self.assertEqual(result["exclusion"]["double_locked_wards"], 10)


class DelhiLibraryPaperFiguresApplicationTest(unittest.TestCase):
    def test_application_renders_decline_and_finance_from_loaded_metrics(self) -> None:
        from sevent4.application.delhi_library_paper_figures import build_delhi_library_paper_figures

        rows = [
            {"year": "2021-22", "total_issues": 100, "total_members": 20, "grant_received_rs": 10_000_000, "total_expenditure_rs": 8_000_000, "closing_unspent_rs": 2_000_000, "returned_to_ministry_rs": 0},
            {"year": "2022-23", "total_issues": 160, "total_members": 25, "grant_received_rs": 20_000_000, "total_expenditure_rs": 10_000_000, "closing_unspent_rs": 6_000_000, "returned_to_ministry_rs": 1_000_000},
            {"year": "2023-24", "total_issues": 80, "total_members": 22, "grant_received_rs": None, "total_expenditure_rs": None, "closing_unspent_rs": None, "returned_to_ministry_rs": None},
        ]

        class Store:
            fig = "docs/figures"

            def load_metrics(self):
                return rows

            def render_decline(self, loaded_rows, stats):
                self.decline = (loaded_rows, stats)

            def render_finance(self, loaded_rows, stats):
                self.finance = (loaded_rows, stats)

        store = Store()
        result = build_delhi_library_paper_figures(store)

        self.assertEqual(store.decline[0], rows)
        self.assertEqual(store.decline[1]["peak_year"], "2022-23")
        self.assertEqual(store.finance[1]["finance_years"], ["2021-22", "2022-23"])
        self.assertEqual(result["decline"]["latest_issues"], 80)
        self.assertEqual(result["finance"]["returned_to_ministry_cr"], 0.1)


if __name__ == "__main__":
    unittest.main()
