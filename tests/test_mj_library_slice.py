import ast
import unittest
from pathlib import Path

from sevent4.domain.mj_library import (
    clean_service_rows,
    document_manifest_row,
    governance_rows,
    join_col,
    membership_rows,
    normalize_timing,
    parse_service_locations,
    rti_form_rows,
    rti_officer_rows,
    service_section,
    staff_rows,
)

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "scripts" / "recipes" / "ahmedabad" / "enrich_mj_library_sources.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class MjLibraryRecipeArchitectureTest(unittest.TestCase):
    def test_recipe_routes_through_ports(self) -> None:
        imports = _imports(RECIPE)
        for forbidden in ("csv", "json", "subprocess", "hashlib", "shutil", "scripts.recipes.library_networks"):
            self.assertNotIn(forbidden, imports, f"recipe should not own/keep {forbidden}")
        self.assertIn("sevent4.adapters.mj_library_filesystem", imports)
        self.assertIn("sevent4.application.mj_library", imports)


class MjLibraryDomainTest(unittest.TestCase):
    def test_join_col_and_normalize_timing(self) -> None:
        words = [{"left": 80, "top": 10, "text": "A"}, {"left": 90, "top": 10, "text": "B"}, {"left": 300, "top": 10, "text": "X"}]
        self.assertEqual(join_col(words, 70, 250), "A B")
        self.assertEqual(normalize_timing("Mon to  Fariday  9"), "Mon to Friday 9")

    def test_service_section_boundaries(self) -> None:
        self.assertEqual(service_section(1, 10), "amc_library")
        self.assertEqual(service_section(6, 100), "amc_library")
        self.assertEqual(service_section(6, 200), "amc_balbhavan")
        self.assertEqual(service_section(7, 0), "mj_library_branch")

    def test_parse_service_locations_one_row(self) -> None:
        words = [
            {"page": 1, "left": 50, "top": 10, "text": "1"},
            {"page": 1, "left": 80, "top": 10, "text": "Central"},
            {"page": 1, "left": 260, "top": 10, "text": "ZoneA"},
            {"page": 1, "left": 400, "top": 10, "text": "Addr"},
            {"page": 1, "left": 600, "top": 10, "text": "phone"},
        ]
        rows = parse_service_locations(words)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["section"], "amc_library")
        self.assertEqual(rows[0]["name"], "Central")
        self.assertEqual(rows[0]["area"], "ZoneA")

    def test_clean_service_rows_applies_override(self) -> None:
        rows = clean_service_rows([{"section": "mj_library_branch", "source_record_id": "1",
                                    "name": "x", "area": "", "address": "", "contact": "", "timings_raw": "",
                                    "confidence": "medium", "notes": ""}])
        self.assertEqual(rows[0]["name"], "Sheth Maneklal Jethabhai Pustakalaya")
        self.assertEqual(rows[0]["confidence"], "high")

    def test_hardcoded_rosters(self) -> None:
        staff = staff_rows()
        self.assertEqual(len(staff), 22)
        self.assertEqual(sum(int(r["filled_posts"]) for r in staff), 43)
        self.assertEqual(sum(int(r["sanctioned_posts"]) for r in staff), 118)
        self.assertEqual(len(rti_officer_rows()), 3)
        self.assertEqual(len(rti_form_rows()), 9)

    def test_content_driven_rows(self) -> None:
        content = {f"instruction-{k}": {"eng": "Name Person Mayor of city"} for k in
                   ["79", "80", "84", "81", "82", "83", "85", "86", "45", "196", "197", "199", "201", "275", "281", "303"]}
        gov = governance_rows(content)
        self.assertEqual([r["source_key"] for r in gov][:2], ["instruction-79", "instruction-80"])
        self.assertEqual(gov[0]["role_or_title"], "Mayor, Amdavad Municipal Corporation; Chairman")
        self.assertGreaterEqual(len(membership_rows(content)), 9)

    def test_document_manifest_row(self) -> None:
        row = document_manifest_row({"document_id": "d", "category": "c"}, "p.pdf", "t.txt", "sha", 100, 5, "pdftotext -layout")
        self.assertEqual(row["bytes"], "100")
        self.assertEqual(row["pages"], "5")
        self.assertEqual(row["fetched_or_refreshed_at"], "2026-06-15")


if __name__ == "__main__":
    unittest.main()
