import ast
import unittest
from pathlib import Path

# Importing these proves the new layer modules load (explicit-package contract).
from sevent4.application.roads import mine_road_spend
from sevent4.domain.roads import classify_page, scan_book_pages

ROOT = Path(__file__).resolve().parents[1]
MINE = ROOT / "scripts" / "recipes" / "ahmedabad" / "mine_amc_road_spend.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class RoadsRecipeArchitectureTest(unittest.TestCase):
    def test_mine_recipe_does_not_own_io_and_routes_through_ports(self) -> None:
        imports = _imports(MINE)
        for forbidden in ("csv", "json", "re", "os", "pypdf"):
            self.assertNotIn(forbidden, imports, f"mine_amc_road_spend.py should not own {forbidden} IO")
        self.assertIn("sevent4.adapters.roads_filesystem", imports)
        self.assertIn("sevent4.application.roads", imports)


class RoadsMiningDomainTest(unittest.TestCase):
    def test_classify_page_tags(self) -> None:
        self.assertIn("code-table", classify_page("foo 64401 bar"))
        self.assertIn("narrative", classify_page("RESURFACing works"))
        self.assertIn("contractor-candidate", classify_page("the contractor and tender"))
        self.assertIn("ward-table", classify_page("Ward No 3 Resurface Zonewise"))

    def test_scan_book_pages_extracts_codes_and_dept_totals(self) -> None:
        pages = [
            "381 ROADS,STREETS, PAVEMENTS\n64401 resurfacing 1000\n",
            "962 ZONAL CAPITAL WORKS 123456789\nnarrative resurfac here\n",
        ]
        scan = scan_book_pages("2023-24-EN", pages)
        codes = {r["code"] for r in scan.rows}
        self.assertIn("64401", codes)
        self.assertIn("DEPT962", codes)  # dept-of-interest total line
        row = next(r for r in scan.rows if r["code"] == "64401")
        self.assertEqual(row["dept"], "381")
        self.assertEqual(row["page"], 1)
        self.assertEqual(scan.classification["pages"], 2)
        self.assertTrue(scan.dump_pages)  # page 2 is narrative -> dumped


class RoadsMiningApplicationTest(unittest.TestCase):
    def test_mine_road_spend_accumulates_and_writes_dumps(self) -> None:
        class FakeSource:
            def iter_books(self):
                yield "2023-24-EN", "/x/Budget_2023_24_English.pdf", [
                    "381 ROADS\n64401 1000\n",          # code-table only -> not dumped
                    "narrative resurfac here\n",         # narrative -> dumped
                ]

        class FakeArchive:
            def __init__(self):
                self.dumps = []

            def write_dump(self, year, page, text):
                self.dumps.append((year, page))

        archive = FakeArchive()
        rows, page_index, log_lines = mine_road_spend(FakeSource(), archive)
        self.assertIn("64401", {r["code"] for r in rows})
        self.assertEqual(page_index["2023-24-EN"]["pdf"], "/x/Budget_2023_24_English.pdf")
        self.assertEqual(archive.dumps, [("2023-24-EN", 2)])
        self.assertEqual(len(log_lines), 1)


if __name__ == "__main__":
    unittest.main()
