import unittest

from scripts.budget_db.extract_gujarat_state_transport import (
    extract_rows_from_text,
    gross_total_be_amount,
)


class GujaratStateTransportExtractorTest(unittest.TestCase):
    def test_gross_total_amount_reads_only_budget_year_be_column(self) -> None:
        self.assertEqual(
            gross_total_be_amount(
                "153.90    --     73.9497   268.42       130.00        "
                "એકંદર સરવાળો                                                      "
                "02   Gross Total                                              237.55"
            ),
            237.55,
        )
        self.assertIsNone(
            gross_total_be_amount(
                "19.8800                  --                        --              "
                "એકંદર સરવાળો                                       06 Gross Total                                           --"
            )
        )

    def test_demand_level_gross_total_does_not_emit_scheme_row(self) -> None:
        text = "\n".join(
            [
                "Sub Head : 4217 03 191 06",
                "PM-eBus Sewa Scheme for electric bus depot",
                "19.8800                  --                        --              એકંદર સરવાળો 06 Gross Total --",
                "80.5478         260.87              179.21                 એકંદર સરવાળો : માગણી Gross Total : Demand No.075 322.99",
                "Sub Head : 4217 03 191 12",
                "PM-eBus Sewa Scheme for electric bus depot",
                "0.0000               15.00                      15.00            એકંદર સરવાળો 12 Gross Total 12.00",
            ]
        )

        rows = extract_rows_from_text(text, "2025-26", "demand.pdf")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["amount_total_cr"], 12.0)
        self.assertEqual(rows[0]["account_code"], "4217 03 191 12")
        self.assertNotIn("Demand No.075", rows[0]["raw_line"])


if __name__ == "__main__":
    unittest.main()
