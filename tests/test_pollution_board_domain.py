import unittest

from sevent4.domain.pollution import PollutionBoardCapacityRecord


class PollutionBoardDomainTest(unittest.TestCase):
    def test_capacity_record_derives_capacity_and_finance_claims(self) -> None:
        record = PollutionBoardCapacityRecord.from_dict(
            "bengaluru",
            {
                "board": "KSPCB",
                "facts": [
                    {"metric": "posts_sanctioned", "value": 723, "year": "2025-03", "confidence": "high"},
                    {"metric": "posts_vacant", "value": 437, "year": "2025-03", "confidence": "high"},
                ],
                "finance": {
                    "finance_year": "2023-24",
                    "cash_opening_balance_cr": 1292.45,
                },
            },
        )

        self.assertEqual(record.sanctioned, 723)
        self.assertEqual(record.vacant, 437)
        self.assertEqual(record.vacancy_pct, 60)
        self.assertEqual(record.status, "live")
        self.assertEqual(record.tier, "primary")
        self.assertEqual(record.capacity_claim_id, "claim-why-air-kspcb-vacancy-2025")
        self.assertEqual(record.finance_claim_id, "claim-why-air-kspcb-finance-2023-24")

    def test_capacity_record_keeps_missing_capacity_pending(self) -> None:
        record = PollutionBoardCapacityRecord.from_dict("delhi", {"board": "DPCC", "facts": []})

        self.assertIsNone(record.vacancy_pct)
        self.assertEqual(record.status, "pending")
        self.assertEqual(record.tier, "pending")
        self.assertIsNone(record.capacity_claim_id)


if __name__ == "__main__":
    unittest.main()
