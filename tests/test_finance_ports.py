import tempfile
import unittest
from pathlib import Path

from sevent4.adapters.finance_filesystem import (
    FileBudgetExplorerInputRepository,
    FileMoneyFlowInputRepository,
    HtmlFileWriter,
)
from sevent4.application.finance import publish_budget_explorer, publish_money_flow
from sevent4.finance.build_budget_explorer import build_budget_explorer_from_files
from sevent4.finance.build_money_flow import build_money_flow_from_files


class FinancePortsTest(unittest.TestCase):
    def test_budget_explorer_application_publishes_through_ports(self) -> None:
        class City:
            name = "Testville"
            source_dir = Path("data/cities/testville/source")

        class Repository:
            def load(self):
                return type(
                    "Input",
                    (),
                    {
                        "city": City(),
                        "headline": [{"year": "2024-25"}],
                        "civic_meta": {"caveats": []},
                        "civic_rows": [],
                    },
                )()

        class Writer:
            def __init__(self) -> None:
                self.html = ""

            def write_html(self, html: str) -> None:
                self.html = html

        writer = Writer()
        result = publish_budget_explorer(
            Repository(),
            writer,
            lambda city, headline, civic_meta, civic_rows: f"{city.name}:{headline[0]['year']}",
        )

        self.assertEqual(writer.html, "Testville:2024-25")
        self.assertEqual(result.html, "Testville:2024-25")

    def test_money_flow_application_publishes_through_ports(self) -> None:
        class City:
            name = "Testville"
            source_dir = Path("data/cities/testville/source")

        class Repository:
            def load(self):
                return type("Input", (), {"city": City()})()

        class Writer:
            def __init__(self) -> None:
                self.html = ""

            def write_html(self, html: str) -> None:
                self.html = html

        writer = Writer()
        result = publish_money_flow(Repository(), writer, lambda city: f"money:{city.name}")

        self.assertEqual(writer.html, "money:Testville")
        self.assertEqual(result.html, "money:Testville")

    def test_budget_explorer_file_repository_loads_city_and_budget_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            city_yaml, _source_dir, _out = _write_finance_fixture(Path(tmp))

            inputs = FileBudgetExplorerInputRepository(city_yaml).load()

            self.assertEqual(inputs.city.name, "Testville")
            self.assertEqual(inputs.headline[0]["year"], "2023-24")
            self.assertEqual(inputs.civic_meta["caveats"][0], "fixture caveat")
            self.assertEqual(inputs.civic_rows[0]["line"], "AMTS")

    def test_finance_clis_build_html_through_file_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            city_yaml, _source_dir, out_dir = _write_finance_fixture(Path(tmp))
            budget_out = out_dir / "finance" / "index.html"
            money_out = out_dir / "money" / "index.html"

            build_budget_explorer_from_files(str(city_yaml), str(budget_out))
            build_money_flow_from_files(str(city_yaml), str(money_out))

            budget_html = budget_out.read_text(encoding="utf-8")
            money_html = money_out.read_text(encoding="utf-8")
            self.assertIn("What Testville city budget funds", budget_html)
            self.assertIn("Who controls the money", money_html)
            for html in (budget_html, money_html):
                self.assertNotIn('data-theme="dark"', html)
                self.assertIn('href="../../../assets/theme.css"', html)
                self.assertIn("localStorage.getItem('atlas-theme')", html)
            self.assertIn("@media (prefers-color-scheme: light)", money_html)
            self.assertIn(":root:not([data-theme=dark])", money_html)
            self.assertIn(":root[data-theme=light]", money_html)

    def test_html_file_writer_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested" / "index.html"

            HtmlFileWriter(out).write_html("hello")

            self.assertEqual(out.read_text(encoding="utf-8"), "hello")

    def test_money_flow_file_repository_loads_city(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            city_yaml, _source_dir, _out = _write_finance_fixture(Path(tmp))

            inputs = FileMoneyFlowInputRepository(city_yaml).load()

            self.assertEqual(inputs.city.name, "Testville")


def _write_finance_fixture(base: Path) -> tuple[Path, Path, Path]:
    repo = base / "repo"
    city_dir = repo / "data" / "cities" / "testville"
    source_dir = city_dir / "source"
    budget_dir = source_dir / "budget"
    out_dir = repo / "public" / "cities" / "testville"
    budget_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
    (city_dir / "city.yaml").write_text(
        "\n".join(
            [
                "id: testville",
                "name: Testville",
                "country: India",
                "state: State",
                "center: [72.0, 23.0]",
                "bbox: [71.0, 22.0, 73.0, 24.0]",
                "crs_metric: EPSG:32643",
                "layers_dir: data/cities/testville/layers",
                "source_dir: data/cities/testville/source",
                "outputs_dir: public/cities/testville",
            ]
        ),
        encoding="utf-8",
    )
    (budget_dir / "amc_budget_22yr.csv").write_text(
        "\n".join(
            [
                "year,amts_cr,mj_library_cr,property_tax_cr,total_cr,confidence,amts_page,notes",
                "2023-24,100,1,50,1000,high,10,",
                "2024-25,120,1.2,60,1100,high,11,",
            ]
        ),
        encoding="utf-8",
    )
    (budget_dir / "amc_civic_lines.json").write_text(
        '{"_meta":{"caveats":["fixture caveat"]},"data":[{"year":"2024-25","line":"AMTS","amount_cr":120}]}',
        encoding="utf-8",
    )
    return city_dir / "city.yaml", source_dir, out_dir


if __name__ == "__main__":
    unittest.main()
