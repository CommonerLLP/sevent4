import json
import unittest
from pathlib import Path


class CityRegistryTest(unittest.TestCase):
    def test_public_city_rosters_match_console_directories(self) -> None:
        consoles = {
            path.parent.name
            for path in Path("public/cities").glob("*/index.html")
        }
        registry = {
            row["id"]
            for row in json.loads(Path("public/cities/registry.json").read_text())
        }
        scorecard = set(
            json.loads(Path("public/cities/scorecard.json").read_text())
        )

        self.assertEqual(consoles, registry)
        self.assertEqual(consoles, scorecard)


if __name__ == "__main__":
    unittest.main()
