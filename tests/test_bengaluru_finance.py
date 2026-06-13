import csv
import tempfile
import unittest
from pathlib import Path

from scripts.recipes.bengaluru.build_finance_layer import (
    build_yearly_table,
    order_year,
)
from scripts.recipes.bengaluru.wire_finance_layer import build_yearly_geojson


class BengaluruFinanceTest(unittest.TestCase):
    def test_order_year_accepts_two_and_four_digit_year_dates(self) -> None:
        self.assertEqual(order_year({"Order Date": "20-Dec-21"}), 2021)
        self.assertEqual(order_year({"Order Date": "04-Apr-2022"}), 2022)

    def test_build_yearly_table_aggregates_by_ward_and_order_year(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp)
            path = raw / "Work_Orders_for_Test_Ward_Num-1_Ward.csv"
            fields = [
                "0", "Sl No", "Job Number", "Start Date", "End Date", "Name of Work",
                "Ward", "Office", "Budget Head", "Contractor", "Mobile", "Email",
                "Bill Type", "Order Number", "Order Date", "SBR Number", "SBR Date",
                "BR Number", "BR Date", "CBR Number", "CBR Date", "Payment", "Gross",
                "Gross In words", "Deduction", "Deduction in words", "Nett", "Nett in words",
            ]
            with path.open("w", encoding="utf-8", newline="") as fh:
                fh.write("BBMP preamble\nanother preamble\n")
                writer = csv.DictWriter(fh, fieldnames=fields)
                writer.writeheader()
                writer.writerow({
                    "0": "1",
                    "Sl No": "1",
                    "Job Number": "001-21-000001",
                    "Start Date": "20-Dec-21",
                    "End Date": "31-Jan-22",
                    "Name of Work": "Drain work",
                    "Ward": "001 Test Ward",
                    "Office": "Office",
                    "Budget Head": "P1771 Roads",
                    "Contractor": "Contractor A",
                    "Order Number": "191",
                    "Order Date": "20-Dec-21",
                    "Nett": "900000",
                })
                writer.writerow({
                    "0": "2",
                    "Sl No": "2",
                    "Job Number": "001-22-000001",
                    "Start Date": "04-Apr-2022",
                    "End Date": "31-May-2022",
                    "Name of Work": "Park work",
                    "Ward": "001 Test Ward",
                    "Office": "Office",
                    "Budget Head": "P0190 Parks",
                    "Contractor": "Contractor B",
                    "Order Number": "192",
                    "Order Date": "04-Apr-2022",
                    "Nett": "2000000",
                })
                writer.writerow({
                    "0": "3",
                    "Sl No": "3",
                    "Job Number": "001-12-000001",
                    "Start Date": "01-Jan-2012",
                    "End Date": "31-Jan-2012",
                    "Name of Work": "Older work",
                    "Ward": "001 Test Ward",
                    "Office": "Office",
                    "Budget Head": "P1771 Roads",
                    "Contractor": "Contractor C",
                    "Order Number": "193",
                    "Order Date": "01-Jan-2012",
                    "Nett": "3000000",
                })

            rows = build_yearly_table(raw)

        keyed = {(row["ward_num"], row["year"]): row for row in rows}
        self.assertEqual(keyed[("1", 2021)]["total_nett_cr"], 0.09)
        self.assertEqual(keyed[("1", 2021)]["work_count"], 1)
        self.assertEqual(keyed[("1", 2022)]["total_nett_cr"], 0.2)
        self.assertEqual(keyed[("1", 2022)]["top_contractors"][0]["name"], "Contractor B")
        self.assertNotIn(("1", 2012), keyed)

    def test_build_yearly_geojson_emits_one_feature_per_ward_year(self) -> None:
        boundary = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"Ward": "Test Ward"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    },
                }
            ],
        }
        yearly = [
            {
                "ward_name": "001 Test Ward",
                "year": 2021,
                "total_nett_cr": 0.09,
                "work_count": 1,
                "top_contractors": [{"name": "Contractor A", "cr": 0.09}],
                "top_budget_heads": [{"head": "P1771 Roads", "cr": 0.09}],
                "flagged_works": [{"name": "Drain work", "contractor": "Contractor A", "head": "P1771", "lakh": 9}],
            }
        ]

        out = build_yearly_geojson(boundary, yearly, years=[2021, 2022])

        self.assertEqual(len(out["features"]), 2)
        by_year = {ft["properties"]["year"]: ft["properties"] for ft in out["features"]}
        self.assertEqual(by_year[2021]["works_spend_cr"], 0.09)
        self.assertEqual(by_year[2021]["work_count"], 1)
        self.assertIsNone(by_year[2022]["works_spend_cr"])


if __name__ == "__main__":
    unittest.main()
