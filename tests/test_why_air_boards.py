"""Tests for the published WHY/air board table."""

import json
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
