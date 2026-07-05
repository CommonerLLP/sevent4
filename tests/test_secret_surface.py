from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

TRACKED_TEXT_GLOBS = (
    "scripts/**/*.py",
    "sevent4/**/*.py",
    "tests/**/*.py",
    "public/**/*.json",
    "public/**/*.html",
)

FORBIDDEN_LITERAL_PARTS = (
    ("iudx-portal-client", "-secret"),
    ("iudx-portal-client", "-id"),
    ("secret-token", "-value"),
    ("provided portal client", " credentials"),
    ("resource-server", " consumer token"),
)


class SecretSurfaceTest(unittest.TestCase):
    def test_tracked_text_does_not_expose_iudx_secret_surface(self) -> None:
        offenders: list[str] = []
        for pattern in TRACKED_TEXT_GLOBS:
            for path in ROOT.glob(pattern):
                if path.name == "maplibre-gl.js":
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for literal in ("".join(parts) for parts in FORBIDDEN_LITERAL_PARTS):
                    if literal in text:
                        offenders.append(f"{path.relative_to(ROOT)}: {literal}")

        self.assertEqual(offenders, [])
