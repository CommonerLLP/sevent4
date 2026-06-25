import subprocess
import sys
import unittest

from scripts.research.run_dpl_parliament_probe import dpl_filter, _parse_session_range


class DplParliamentProbeTest(unittest.TestCase):
    def test_import_does_not_load_commoner_probe(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "import scripts.research.run_dpl_parliament_probe; "
                    "print(any(name.startswith('commoner_probe') for name in sys.modules))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual("False", result.stdout.strip())

    def test_dpl_filter_keeps_exact_library_questions(self) -> None:
        self.assertTrue(dpl_filter("Delhi Public Library staffing", "vacant posts"))
        self.assertTrue(dpl_filter("Culture grant", "Delhi Library Board"))

    def test_dpl_filter_keeps_delhi_capacity_context(self) -> None:
        self.assertTrue(dpl_filter("Library branches in Delhi", "staff vacancies"))
        self.assertFalse(dpl_filter("Public libraries in Kerala", "staff vacancies"))

    def test_parse_session_range_accepts_ranges_and_singletons(self) -> None:
        self.assertEqual(_parse_session_range("214-216,220"), [214, 215, 216, 220])


if __name__ == "__main__":
    unittest.main()
