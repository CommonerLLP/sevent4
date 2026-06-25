import ast
import unittest
from pathlib import Path

import pandas as pd

from sevent4.application.rbi_finance import (
    build_rbi_2024_report,
    row_values,
    table_by_title,
)
from sevent4.domain.rbi_finance import (
    STATE_NAMES,
    STATE_TABLE_II_2_YEARS,
    clean_value,
    grouped,
    lakh_to_crore,
    normalized_line,
    num_tokens,
    parse_table_ii_2,
    section,
    state_rows,
    value,
)

ROOT = Path(__file__).resolve().parents[1]
R2024 = ROOT / "scripts" / "research" / "parse_rbi_municipal_finances.py"
R2022 = ROOT / "scripts" / "research" / "parse_rbi_municipal_finances_2022.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class RbiRecipeArchitectureTest(unittest.TestCase):
    def test_recipes_do_not_own_io_and_route_through_ports(self) -> None:
        for path in (R2024, R2022):
            imports = _imports(path)
            for forbidden in ("subprocess", "json", "hashlib", "pandas", "re", "math"):
                self.assertNotIn(forbidden, imports, f"{path.name} should not own {forbidden} IO")
            self.assertIn("sevent4.adapters.rbi_finance_filesystem", imports)
            self.assertIn("sevent4.application.rbi_finance", imports)


class RbiScalarTest(unittest.TestCase):
    def test_value_and_num_tokens(self) -> None:
        self.assertIsNone(value("NA"))
        self.assertEqual(value("1,234"), 1234)
        self.assertEqual(value("12.5"), 12.5)
        self.assertEqual(num_tokens("10  20  NA  3.5"), [10, 20, None, 3.5])

    def test_clean_value_and_lakh_to_crore(self) -> None:
        self.assertIsNone(clean_value("-"))
        self.assertEqual(clean_value("1,00,000"), 100000.0)
        self.assertEqual(lakh_to_crore({"y": 100.0, "z": None}), {"y": 1.0, "z": None})

    def test_normalized_line_and_section(self) -> None:
        self.assertEqual(normalized_line("  a’b  "), "a'b")
        self.assertEqual(section("xxSTARTmidENDyy", "START", "END"), "STARTmid")

    def test_grouped(self) -> None:
        out = grouped([1, 2, 3, 4], ["y1", "y2"], ["a", "b"])
        self.assertEqual(out, {"y1": {"a": 1, "b": 2}, "y2": {"a": 3, "b": 4}})


class RbiStateTableTest(unittest.TestCase):
    def test_state_rows_requires_every_state(self) -> None:
        block = "\n".join(f"{name} 10 20 30 40 50" for name in STATE_NAMES)
        rows = state_rows(block, 5)
        self.assertEqual(rows["Gujarat"], [10, 20, 30, 40, 50])
        # one missing state -> raise
        partial = "\n".join(f"{name} 1 2 3 4 5" for name in STATE_NAMES[:-1])
        with self.assertRaisesRegex(ValueError, "Missing state rows"):
            state_rows(partial, 5)

    def test_parse_table_ii_2_groups_three_years_three_fields(self) -> None:
        body = "\n".join(f"{name} " + " ".join(str(i) for i in range(1, 10)) for name in STATE_NAMES)
        text = f"Table II.2: State-wise Municipal Corporations\n{body}\nTable II.3:"
        out = parse_table_ii_2(text)
        guj = out["Gujarat"]
        self.assertEqual(list(guj.keys()), STATE_TABLE_II_2_YEARS)
        self.assertEqual(guj[STATE_TABLE_II_2_YEARS[0]]["revenue_receipts_inr_crore"], 1)
        self.assertEqual(guj[STATE_TABLE_II_2_YEARS[2]]["surplus_deficit_inr_crore"], 9)


class Rbi2022ApplicationTest(unittest.TestCase):
    def test_row_values_and_table_by_title(self) -> None:
        df = pd.DataFrame(
            [["Table II.1: Revenue Receipts", "a", "b", "c"],
             ["Revenue Receipts", "1.0", "2.0", "3.0"]]
        )
        found = table_by_title([df], "Table II.1: Revenue Receipts", max_cols=4, min_rows=2)
        self.assertIs(found, df)
        vals = row_values(df, "Revenue Receipts", ["y1", "y2", "y3"])
        self.assertEqual(vals, {"y1": 1.0, "y2": 2.0, "y3": 3.0})
        with self.assertRaisesRegex(ValueError, "Missing row"):
            row_values(df, "Nope", ["y1"])


class Rbi2024ReportTest(unittest.TestCase):
    def test_build_report_shapes_source_block(self) -> None:
        # full table text so parse_rbi_2024_tables succeeds
        def states(n):
            return "\n".join(f"{name} " + " ".join(str(i) for i in range(1, n + 1)) for name in STATE_NAMES)

        text = (
            "RBI Report on Municipal Finances cover\f more\n"
            f"Table II.2: State-wise Municipal Corporations\n{states(9)}\nTable II.3:"
            f" Ratio of Municipal Corporations\n{states(5)}\nTable II.4: Revenue Receipts\n"
            "Revenue Receipts 1 2 3 4 5\nI. Own Tax Revenue 1 2 3 4 5\n"
            "Of which: Property Tax 1 2 3 4 5\nOf which: Water Tax 1 2 3 4 5\n"
            "II. Own Non-Tax Revenue 1 2 3 4 5\nOf which: Fees and User Charges 1 2 3 4 5\n"
            "Of which: Income from Investment 1 2 3 4 5\nIII. Transfers 1 2 3 4 5\n"
            f"Table II.5: Ratio of Municipal Corporations\n{states(10)}\nTable II.6:\n"
            "Table II.7: Grants to Urban Local Bodies\n"
            "Total Grants from the Central Government to the MCs@ 1 2 3 4\n"
            "Finance Commission Grants as Reported by the Municipal Corporations 1 2 3 4\n"
            "Grants from Central Government other than Finance Commission Grants 1 2 3 4\n"
            "Total Grants from the State Governments to the MCs@ 1 2 3 4\n"
            "State Finance Commission Grants as Reported by the Municipal Corporations 1 2 3 4\n"
            "Finance Commission Grants to ULBs as reported in the Union Budget 1 2 3 4\n"
            "Grants from the State Governments other than State Finance Commission 1 2 3 4 Grants\n"
            "Table II.8: Municipal Corporations\n"
            "Own Revenue / Total Revenue Receipts 1 2 3 4 5\n"
            "Tax Revenue / Total Revenue Receipts 1 2 3 4 5\n"
            "Property Tax Collection / Total Revenue Receipts 1 2 3 4 5\n"
            "States' Transfer / Total Revenue Receipts 1 2 3 4 5\n"
            "Central Government's Transfer / Total Revenue Receipts 1 2 3 4 5\n"
            "Combined (Centre plus States) Transfer / Total Revenue Receipts 1 2 3 4 5\n"
            "Table II.9:"
        )
        report = build_rbi_2024_report(text, "/x/rbi.pdf", "deadbeef")
        self.assertEqual(report["source"]["path"], "/x/rbi.pdf")
        self.assertEqual(report["source"]["sha256"], "deadbeef")
        self.assertTrue(report["source"]["cover_text"].startswith("RBI Report on Municipal Finances"))
        self.assertIn("ii_2_state_revenue_receipts_expenditure", report["tables"])
        self.assertIn("Gujarat", report["tables"]["ii_3_mc_revenue_to_state_revenue_ratio"])


if __name__ == "__main__":
    unittest.main()
