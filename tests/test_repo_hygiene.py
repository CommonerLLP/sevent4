import subprocess
import unittest
from pathlib import Path


class RepoHygieneTest(unittest.TestCase):
    def test_tracked_files_do_not_reference_private_repo_topology(self) -> None:
        forbidden = {
            b"twenty" + b"27": "private sibling repo name",
            b"m1" + b"-storage": "personal local volume name",
            b"the" + b"-" + b"road" + b"-money": (
                "removed internal investigation filename"
            ),
            b"ahmedabad" + b"-road" + b"-contractors": (
                "removed internal investigation filename"
            ),
            b"road" + b"-contractor" + b" investigation": (
                "internal investigation label"
            ),
        }
        tracked = subprocess.run(
            ["git", "ls-files", "-z"],
            check=True,
            capture_output=True,
        ).stdout.split(b"\0")

        violations = []
        for raw_path in tracked:
            if not raw_path:
                continue
            path = Path(raw_path.decode("utf-8"))
            content = path.read_bytes()
            for needle, reason in forbidden.items():
                if needle in content:
                    violations.append(f"{path}: {reason}")

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
