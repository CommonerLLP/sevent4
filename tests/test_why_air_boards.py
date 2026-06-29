"""Tests for the published WHY/air board table."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.recipes.build_why_air_table import build


BOARDS_PATH = Path("public/why/air/boards.json")


class WhyAirBoardsTest(unittest.TestCase):
    def test_bengaluru_kspcb_finance_fields_remain_published(self) -> None:
        data = json.loads(BOARDS_PATH.read_text(encoding="utf-8"))
        boards = {row["city"]: row for row in data["boards"]}
        kspcb = boards["bengaluru"]

        self.assertEqual(kspcb["board"], "KSPCB")
        self.assertEqual(kspcb["finance_year"], "2023-24")
        self.assertAlmostEqual(kspcb["cash_opening_balance_cr"], 1292.45)
        self.assertAlmostEqual(kspcb["receipts_cr"], 348.7)
        self.assertAlmostEqual(kspcb["expenditure_cr"], 78.85)
        self.assertAlmostEqual(kspcb["interest_cr"], 66.86)
        self.assertEqual(kspcb["labs"], 9)
        self.assertEqual(kspcb["inspections"], 20124)
        self.assertEqual(kspcb["samples"], 114167)
        self.assertEqual(kspcb["finance_source"], "KSPCB Annual Report 2023-24")

    def test_builder_publishes_capacity_claim_ids_for_live_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            city_dir = root / "data" / "cities" / "bengaluru" / "source" / "pollution"
            city_dir.mkdir(parents=True)
            (city_dir / "capacity.json").write_text(
                json.dumps(
                    {
                        "city": "bengaluru",
                        "board": "KSPCB",
                        "facts": [
                            {
                                "metric": "posts_sanctioned",
                                "value": 723,
                                "year": "2025-03",
                                "confidence": "high",
                            },
                            {
                                "metric": "posts_vacant",
                                "value": 437,
                                "year": "2025-03",
                                "confidence": "high",
                            },
                            {
                                "metric": "vacancy_pct",
                                "value": 60,
                                "year": "2025-03",
                                "confidence": "high",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "public" / "why" / "air" / "boards.json"

            build(cities_dir=root / "data" / "cities", out=out, verbose=False)

            boards = json.loads(out.read_text(encoding="utf-8"))["boards"]
            self.assertEqual(boards[0]["city"], "bengaluru")
            self.assertEqual(boards[0]["capacity_claim_id"], "claim-why-air-kspcb-vacancy-2025")

    def test_published_table_matches_fresh_builder_output(self) -> None:
        # Reproducing the published table needs every city's capacity source. Those
        # records are gitignored, so require the complete set the table was built
        # from — a partial checkout would otherwise rebuild a smaller table and
        # fail the comparison against the committed five-city boards.json.
        expected_cities = {row["city"] for row in json.loads(BOARDS_PATH.read_text(encoding="utf-8"))["boards"]}
        present_cities = {
            path.parent.parent.parent.name
            for path in Path("data/cities").glob("*/source/pollution/capacity.json")
        }
        if not expected_cities <= present_cities:
            self.skipTest("pollution capacity records live under gitignored data/; full source set absent on this checkout")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "boards.json"
            build(out=out, verbose=False)
            self.assertEqual(
                json.loads(BOARDS_PATH.read_text(encoding="utf-8")),
                json.loads(out.read_text(encoding="utf-8")),
            )


if __name__ == "__main__":
    unittest.main()
