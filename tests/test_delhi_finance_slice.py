import ast
import unittest
from pathlib import Path

from sevent4.application.delhi_finance import parse_delhi_finance
from sevent4.domain.delhi_finance import gnctd_row, ndmc_row, parse_mcd_rows

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "scripts" / "recipes" / "delhi" / "parse_budget_finance.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class DelhiFinanceArchitectureTest(unittest.TestCase):
    def test_recipe_routes_through_ports(self) -> None:
        imports = _imports(RECIPE)
        for forbidden in ("csv", "json", "subprocess", "re"):
            self.assertNotIn(forbidden, imports, f"recipe should not own {forbidden} IO")
        self.assertIn("sevent4.adapters.delhi_finance_filesystem", imports)
        self.assertIn("sevent4.application.delhi_finance", imports)
        self.assertIn("sevent4.domain.delhi_finance", imports)  # re-export for the existing test


class DelhiFinanceDomainTest(unittest.TestCase):
    def test_gnctd_row_uses_glance_and_floors(self) -> None:
        text = "Total Receipts (1+4)  60000.00 76000.00\nTotal Expenditure (9+12)  59000.00 70000.00"
        row = gnctd_row(text, "budget_at_a_glance_2025-26.pdf", False, {}, "data/x.pdf")
        self.assertEqual(row["fy"], "2025-26")
        self.assertEqual(row["total_receipts_cr"], 76000.00)
        self.assertEqual(row["total_expenditure_cr"], 70000.00)
        # non-glance -> None
        self.assertIsNone(gnctd_row(text, "something_2025-26.pdf", False, {}, "x"))

    def test_gnctd_vision_overlay_overrides(self) -> None:
        row = gnctd_row("Total Receipts 9999999", "glance_2018-19.pdf", True,
                        {"2018-19": {"rec": 50000, "exp": 48000}}, "x")
        self.assertEqual(row["total_receipts_cr"], 50000)
        self.assertTrue(row["vision_verified"])
        self.assertFalse(row["ocr_sourced"])

    def test_mcd_rows_lakh_to_crore_and_scope(self) -> None:
        docs = [("Grand Total  5000000\nProperty Tax  300000", "mcd_income_2020-21_South_MCD.pdf", "p1.pdf")]
        rows = parse_mcd_rows(docs)
        self.assertEqual(rows[0]["total_income_cr"], 50000.0)   # 5,000,000 lakh /100
        self.assertEqual(rows[0]["property_tax_cr"], 3000.0)
        self.assertEqual(rows[0]["scope"], "South MCD only (trifurcation era)")

    def test_ndmc_row(self) -> None:
        row = ndmc_row("Total Receipt 1200\nTotal Expenditure 1300", "n.pdf")
        self.assertEqual(row["total_receipts_cr"], 1200)
        self.assertEqual(row["council"], "nominated (no elected member)")


class DelhiFinanceApplicationTest(unittest.TestCase):
    def test_parse_delhi_finance_combines_bodies(self) -> None:
        class FakeSource:
            def vision_overlay(self):
                return {}

            def gnctd_docs(self):
                yield "Total Receipts (1+4) 60000\nTotal Expenditure (9+12) 59000", "glance_2024-25.pdf", False, "g.pdf"

            def mcd_docs(self):
                yield "Grand Total 5000000", "mcd_income_2024-25.pdf", "m.pdf"

            def ndmc_doc(self):
                return ("Total Receipt 1200\nTotal Expenditure 1300", "n.pdf")

        rows, meta = parse_delhi_finance(FakeSource())
        bodies = {r["body"] for r in rows}
        self.assertEqual(bodies, {"GNCTD", "MCD", "NDMC"})
        self.assertEqual(meta["city"], "delhi")
        self.assertEqual(meta["rows"], rows)


if __name__ == "__main__":
    unittest.main()
