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


if __name__ == "__main__":
    unittest.main()
