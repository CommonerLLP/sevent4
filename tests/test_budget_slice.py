import ast
import unittest
from pathlib import Path

from sevent4.application.budget import (
    discover_finance_links,
    finance_manifest,
    finance_row,
    ocr_budget_pdf,
    parse_budget_ocr,
)
from sevent4.domain.budget import (
    FinanceBookLink,
    count_numeric_tokens,
    finance_book_filename,
    finance_link_year,
    numbers,
    parse_ocr_lines,
    parse_year_from_filename,
    select_dense_pages,
)

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "scripts" / "recipes" / "ahmedabad"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class BudgetRecipeArchitectureTest(unittest.TestCase):
    def test_budget_recipes_do_not_own_io_and_route_through_ports(self) -> None:
        forbidden = {
            "fetch_city_budget.py": ("json", "subprocess", "shutil", "urllib.request", "re"),
            "ocr_city_budget.py": ("subprocess", "shutil", "re"),
            "parse_city_budget.py": ("csv", "re"),
        }
        for name, banned in forbidden.items():
            imports = _imports(RECIPES / name)
            for module in banned:
                self.assertNotIn(module, imports, f"{name} should not own {module} IO")
            self.assertTrue(
                any(module.startswith("sevent4.adapters.budget") for module in imports),
                f"{name} should route through a budget adapter",
            )
            self.assertIn("sevent4.application.budget", imports, f"{name} should use the budget application")


class BudgetDomainTest(unittest.TestCase):
    def test_numbers_translates_gujarati_and_drops_zero(self) -> None:
        self.assertEqual(numbers("કુલ ૧,૨૩૪ અને 0 અને 56.5"), [1234.0, 56.5])

    def test_parse_ocr_lines_matches_first_labelled_line(self) -> None:
        labels = {"grand_total": r"એકંદરે?\s*કુલ"}
        record = parse_ocr_lines(["preamble", "એકંદર કુલ 9,99,999", "એકંદર કુલ 1"], labels)
        self.assertEqual(record["grand_total"]["numbers"], [999999.0])

    def test_year_helpers(self) -> None:
        self.assertEqual(parse_year_from_filename("ahmedabad_budget_2021-22.pdf"), "2021-22")
        self.assertEqual(parse_year_from_filename("amc 21-22.pdf"), "2021-22")
        self.assertEqual(finance_link_year("Budget 2020-21"), "2020-21")
        self.assertEqual(finance_link_year("Balance Sheet 31-03-2021"), "2020-21")

    def test_finance_book_filename_dedupes(self) -> None:
        link = FinanceBookLink(kind="budget", year="2021-22", label="Budget Book", url="x")
        seen: set[str] = set()
        first = finance_book_filename("ahmedabad", link, seen)
        second = finance_book_filename("ahmedabad", link, seen)
        self.assertEqual(first, "ahmedabad_budget_2021-22_budget-book.pdf")
        self.assertEqual(second, "ahmedabad_budget_2021-22_budget-book_2.pdf")

    def test_select_dense_pages_keeps_top_in_page_order(self) -> None:
        scored = [(1, 2), (2, 20), (3, 9), (4, 15)]
        self.assertEqual(select_dense_pages(scored, top_pages=2, min_numbers=8), [2, 4])
        self.assertEqual(select_dense_pages(scored, top_pages=4, min_numbers=8), [2, 3, 4])

    def test_count_numeric_tokens_counts_gujarati(self) -> None:
        self.assertEqual(count_numeric_tokens("૧૨૩ and 4567 and 12"), 2)


class BudgetApplicationTest(unittest.TestCase):
    def test_discover_finance_links_filters_and_tags_year(self) -> None:
        html = (
            '<a href="/files/budget-2021-22.pdf">Budget 2021-22</a>'
            '<a href="/about">About</a>'
            '<a href="/files/budget-2020-21.pdf">Budget 2020-21</a>'
        )
        links = discover_finance_links(html, "budget", "https://x.gov/SP/Budget", ("budget",))
        self.assertEqual([link.year for link in links], ["2021-22", "2020-21"])
        self.assertTrue(links[0].url.startswith("https://x.gov/"))

    def test_finance_row_and_manifest_shape(self) -> None:
        link = FinanceBookLink(kind="budget", year="2021-22", label="B", url="http://x/y.pdf")
        row = finance_row("ahmedabad", "budget", link, "data/cities/ahmedabad/source/budget/pdfs/y.pdf")
        self.assertEqual(row["year"], "2021-22")
        manifest = finance_manifest("ahmedabad", "budget", "http://x", [row])
        self.assertEqual(manifest["items"], [row])
        self.assertEqual(manifest["source_page"], "http://x")

    def test_parse_budget_ocr_builds_columns_rows_found(self) -> None:
        labels = {"grand_total": r"એકંદરે?\s*કુલ"}
        columns, rows, found = parse_budget_ocr(
            [("2021-22", ["એકંદર કુલ 1,00,000"]), ("2020-21", ["nothing here"])], labels
        )
        self.assertEqual(columns, ["year", "grand_total_candidates", "grand_total_raw"])
        self.assertEqual(rows[0]["grand_total_candidates"], "100000.0")
        self.assertEqual(rows[1]["grand_total_candidates"], "")
        self.assertEqual(found, [("2021-22", ["grand_total"]), ("2020-21", [])])

    def test_ocr_budget_pdf_selects_dense_pages_via_engine(self) -> None:
        class FakeEngine:
            def page_count(self, pdf):
                return 3

            def page_text(self, pdf, page):
                return {1: "1 2", 2: "111 222 333 444 555 666 777 888 999", 3: "x"}[page]

            def ocr_page(self, pdf, page, dpi, lang):
                return f"OCR page {page}: 1234 5678 9012"

        text, page_count, numlines, keep = ocr_budget_pdf(
            FakeEngine(), "x.pdf", top_pages=16, min_numbers=8, dpi=230, lang="guj+eng"
        )
        self.assertEqual(page_count, 3)
        self.assertEqual(keep, [2])
        self.assertIn("=== page 2 ===", text)
        self.assertEqual(numlines, 3)

    def test_ocr_budget_pdf_returns_none_when_no_dense_page(self) -> None:
        class FakeEngine:
            def page_count(self, pdf):
                return 1

            def page_text(self, pdf, page):
                return "1 2"

            def ocr_page(self, pdf, page, dpi, lang):
                raise AssertionError("should not OCR when no dense page")

        text, page_count, numlines, keep = ocr_budget_pdf(
            FakeEngine(), "x.pdf", top_pages=16, min_numbers=8, dpi=230, lang="guj+eng"
        )
        self.assertIsNone(text)
        self.assertEqual((page_count, numlines, keep), (1, 0, []))


if __name__ == "__main__":
    unittest.main()
