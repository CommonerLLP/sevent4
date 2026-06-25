import ast
import unittest
from pathlib import Path

from sevent4.application.gujarat_transport import extract_gujarat_transport, summary_lines

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "scripts" / "budget_db" / "extract_gujarat_state_transport.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class GujaratTransportRecipeArchitectureTest(unittest.TestCase):
    def test_recipe_routes_through_ports(self) -> None:
        imports = _imports(RECIPE)
        for forbidden in ("subprocess", "json", "re"):
            self.assertNotIn(forbidden, imports, f"recipe should not own {forbidden} IO")
        self.assertIn("sevent4.adapters.gujarat_transport_filesystem", imports)
        self.assertIn("sevent4.application.gujarat_transport", imports)
        # the domain functions the existing extractor test imports must stay re-exported
        self.assertIn("sevent4.domain.gujarat_transport", imports)


class GujaratTransportApplicationTest(unittest.TestCase):
    def test_extract_and_dedupe_across_texts(self) -> None:
        block = (
            "Sub Head : 4217 03 191 12\n"
            "PM-eBus Sewa Scheme for electric bus depot\n"
            "0.0000 15.00 15.00 એકંદર સરવાળો 12 Gross Total 12.00"
        )
        # same text twice -> dedupe collapses to one row
        out = extract_gujarat_transport([("2025-26", "a.pdf", block), ("2025-26", "b.pdf", block)])
        self.assertEqual(len(out["rows"]), 1)
        row = out["rows"][0]
        self.assertEqual(row["entity"], "PM_EBUS_SEWA")
        self.assertEqual(row["amount_total_cr"], 12.0)
        self.assertEqual(row["account_code"], "4217 03 191 12")
        self.assertEqual(out["_meta"]["years_found"], ["2025-26"])

    def test_summary_lines_report_counts(self) -> None:
        out = {"rows": [{"entity": "PM_EBUS_SEWA", "fiscal_year": "2025-26", "amount_total_cr": 12.0,
                         "central_share": None, "description_en": "bus depot"}],
               "_meta": {"years_found": ["2025-26"]}}
        lines = summary_lines(out)
        self.assertTrue(lines[0].startswith("✓ 1 rows"))
        self.assertTrue(any("PM E-bus lines captured: 1" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
