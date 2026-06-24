import ast
import unittest
from pathlib import Path

from sevent4.application.amc_budget import build_budget_lines
from sevent4.domain.amc_budget import BudgetLineBuilder, load_civic_lines

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "scripts" / "budget_db" / "build_budget_db.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class AmcBudgetRecipeArchitectureTest(unittest.TestCase):
    def test_recipe_routes_through_ports(self) -> None:
        imports = _imports(RECIPE)
        for forbidden in ("json", "csv", "sqlite3", "subprocess", "re", "os", "pandas", "duckdb"):
            self.assertNotIn(forbidden, imports, f"recipe should not own {forbidden} IO")
        self.assertIn("sevent4.adapters.amc_budget_filesystem", imports)
        self.assertIn("sevent4.application.amc_budget", imports)


class AmcBudgetDomainTest(unittest.TestCase):
    def test_builder_dedupes_on_identity(self) -> None:
        b = BudgetLineBuilder()
        self.assertTrue(b.add("2023-24", "BE", "revenue", "expenditure", "grant", "Grant X", 1.0, entity="E"))
        self.assertFalse(b.add("2023-24", "BE", "revenue", "expenditure", "grant", "Grant X", 9.9, entity="E"))
        self.assertEqual(len(b.rows), 1)
        self.assertEqual(b.rows[0]["amount_cr"], 1.0)  # first loader wins

    def test_civic_loader_picks_basis_and_maps_entity(self) -> None:
        b = BudgetLineBuilder()
        load_civic_lines(b, {"data": [
            {"line": "AMTS", "year": "2023-24", "amount_cr": 10.0, "account_head": "Actual spend"},
            {"line": "library_mj", "year": "2023-24", "amount_cr": 2.0, "account_head": "Revised estimate"},
        ]})
        amts = next(r for r in b.rows if r["entity"] == "AMTS")
        mj = next(r for r in b.rows if r["entity"] == "MJ_LIBRARY")
        self.assertEqual(amts["estimate_basis"], "actual")
        self.assertEqual(amts["head_name"], "Loan/support to AMTS (city bus)")
        self.assertEqual(mj["estimate_basis"], "RE")


class AmcBudgetApplicationTest(unittest.TestCase):
    def test_build_budget_lines_runs_all_loaders(self) -> None:
        civic = {"data": [{"line": "AMTS", "year": "2023-24", "amount_cr": 10.0, "account_head": "actual"}]}
        ie = {"amts_income_expenditure": [{"year": "2023-24", "source": "s",
              "income_total_cr": 5.0, "total_budget_cr": 20.0}], "audited_cumulative_cross_check": {}}
        csv_rows = [{"year": "2024-25", "amts_cr": "12.5", "total_cr": "5000", "confidence": "medium", "amts_page": "7"}]
        grant_texts = [("2022-23", "g.pdf", "Grant to ABC Trust Rs. 2.5 crore")]

        rows, extracted = build_budget_lines(civic, ie, csv_rows, grant_texts)
        self.assertEqual(extracted, 1)
        grant = next(r for r in rows if r["head_name"] == "Grant to ABC Trust")
        self.assertEqual(grant["confidence"], "low")
        self.assertEqual(grant["extraction_method"], "text")
        self.assertEqual(grant["amount_cr"], 2.5)
        self.assertTrue(any(r["head_name"] == "AMTS total budget" for r in rows))
        self.assertTrue(any(r["fiscal_year"] == "2024-25" and r["entity"] == "AMTS" for r in rows))


if __name__ == "__main__":
    unittest.main()
