import importlib.util
import unittest
from pathlib import Path

# load the recipe module by path (scripts/ isn't a package)
_spec = importlib.util.spec_from_file_location(
    "parse_budget_finance",
    Path(__file__).resolve().parents[1] / "scripts/recipes/delhi/parse_budget_finance.py",
)
pbf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pbf)


class DelhiFinanceParserHelpersTest(unittest.TestCase):
    """The source budget PDFs are gitignored (local-only), so this tests the pure
    parsing helpers — the bug-prone bits — not the end-to-end PDF run."""

    def test_nums_keeps_plain_and_comma_grouped_numbers_whole(self) -> None:
        # the original bug: '100000.00' split into ['100','000.00']
        self.assertEqual(pbf.nums("Total Expenditure  100000.00"), [100000.00])
        self.assertEqual(pbf.nums("x 1,00,000.50 y 4048.7"), [100000.50, 4048.7])

    def test_last_total_takes_rightmost_on_matched_line(self) -> None:
        text = "junk\n17. Total Expenditure (9+12)  65823.87 76000.00 69500.00 100000.00\nmore"
        self.assertEqual(pbf.last_total(text, "total expenditure ("), 100000.00)

    def test_fy_from_name_uses_be_year_then_leading_year(self) -> None:
        # an explicit BE year wins (the parser extracts the BE column) — and the BE
        # in "RBE" must not be mistaken for it:
        self.assertEqual(pbf.fy_from_name("..._budget_2018-19_Income_RBE_18-19_BE_19-20_South_MCD"), "2019-20")
        # otherwise the leading FY, read through underscores:
        self.assertEqual(pbf.fy_from_name("..._budget_at_a_glance_2025-26_Budget_at_a_Glance_2025-26"), "2025-26")

    def test_plausible_drops_subfloor_misparses(self) -> None:
        self.assertIsNone(pbf.plausible(0.2, 500))      # footnote fragment
        self.assertEqual(pbf.plausible(17011.9, 500), 17011.9)
        self.assertIsNone(pbf.plausible(None, 500))


if __name__ == "__main__":
    unittest.main()
