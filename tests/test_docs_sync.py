import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocsSyncTest(unittest.TestCase):
    def test_readme_and_serve_script_agree_on_static_entrypoints(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        serve = (ROOT / "scripts" / "serve.sh").read_text(encoding="utf-8")

        self.assertIn("scripts/serve.sh", readme)
        self.assertIn("…/index.html", readme)
        self.assertIn("http://127.0.0.1:$PORT/index.html", serve)
        self.assertIn("http://127.0.0.1:$PORT/public/cities/$CITY/index.html", serve)

    def test_readme_documents_browser_smoke_entrypoint(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn(".venv/bin/python -m sevent4.qa.browser_smoke", readme)
        self.assertIn("mobile, tablet, and desktop viewports", readme)
        self.assertIn('sevent4-browser-smoke = "sevent4.qa.browser_smoke:main"', pyproject)

    def test_readme_links_current_architecture_snapshot(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("[Architecture doctrine](docsx/architecture.md)", readme)
        self.assertIn("[System architecture](docsx/system-architecture-2026-06-22.md)", readme)

    def test_readme_advertises_live_public_site(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("https://commonerllp.org/sevent4/", readme)
        self.assertNotIn("no live public site", readme.lower())
        self.assertNotIn("private repo", readme.lower())

    def test_pages_workflow_auto_deploys_public_main(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")

        self.assertIn('branches: ["main"]', workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("PRIVATE", workflow)
        self.assertNotIn("Auto-deploy on push to main is DISABLED", workflow)

    def test_contributing_documents_current_full_suite_count(self) -> None:
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

        self.assertIn("currently 442 tests", contributing)
        self.assertNotIn("currently 330 tests", contributing)
        self.assertNotIn("currently 327 tests", contributing)
        self.assertNotIn("currently 321 tests", contributing)
        self.assertNotIn("currently 319 tests", contributing)
        self.assertNotIn("currently 315 tests", contributing)
        self.assertNotIn("currently 93 tests", contributing)

    def test_public_control_docs_point_to_canonical_architecture_docs(self) -> None:
        required_docs = {
            "SCOPE.md": "The Unelected City owns",
            "ROADMAP.md": "Publication readiness",
            "ARCHITECTURE.md": "docsx/architecture.md",
        }

        for filename, marker in required_docs.items():
            body = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn(marker, body)

    def test_source_policy_distinguishes_official_contacts_from_osm_contacts(self) -> None:
        policy = (ROOT / "docsx" / "source-policy-and-readiness.md").read_text(encoding="utf-8")

        self.assertIn("Official public-functionary contacts", policy)
        self.assertIn("public rosters may be displayed", policy)
        self.assertIn("OSM-derived contact fields need audit", policy)

    def test_public_readiness_audit_records_current_gate_verdict(self) -> None:
        audit = (ROOT / "docsx" / "public-readiness-audit-2026-06-25.md").read_text(encoding="utf-8")

        self.assertIn("Hexagonal refactor status: closed", audit)
        self.assertIn("Public-functionary contacts are allowed", audit)
        self.assertIn("ready for public repository visibility", audit)


if __name__ == "__main__":
    unittest.main()
