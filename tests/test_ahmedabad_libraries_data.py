import csv
import json
import unittest
from pathlib import Path

from scripts.recipes.library_networks import proactive_disclosure_year, year_from_text


BASE = Path("data/cities/ahmedabad/source/libraries")
DISCLOSURE_YEARS = [
    "2015-16",
    "2016-17",
    "2017-18",
    "2018-19",
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
    "2025-26",
]


def rows(name: str) -> list[dict[str, str]]:
    with (BASE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class AhmedabadLibrariesDataTest(unittest.TestCase):
    def test_year_extractors_cover_mj_disclosure_url_patterns(self) -> None:
        self.assertEqual(year_from_text("_RTI_201718_MJ%20Library_Discloser.pdf"), "2017-18")
        self.assertEqual(year_from_text("2020-2021.pdf"), "2020-21")
        self.assertEqual(year_from_text("2022_2023.pdf"), "2022-23")
        self.assertEqual(
            proactive_disclosure_year("PRO ACTIVE DISCLOSURE 2024-25 - "),
            "2024-25",
        )

    def test_pdf_index_covers_all_official_proactive_disclosures(self) -> None:
        pdf_rows = rows("mj_library_pdf_index.csv")
        proactive_years = sorted(
            {row["year"] for row in pdf_rows if row["category"] == "proactive_disclosure"}
        )

        self.assertEqual(proactive_years, DISCLOSURE_YEARS)
        self.assertEqual(len([row for row in pdf_rows if row["category"] == "proactive_disclosure"]), 22)
        self.assertIn("rules_orders", {row["category"] for row in pdf_rows})
        self.assertIn("fees", {row["category"] for row in pdf_rows})
        self.assertIn("forms", {row["category"] for row in pdf_rows})

    def test_disclosure_text_exports_exist_for_every_year(self) -> None:
        text_rows = rows("mj_library_disclosure_text_index.csv")

        self.assertEqual([row["year"] for row in text_rows], DISCLOSURE_YEARS)
        for row in text_rows:
            text_path = Path(row["text_path"])
            self.assertTrue(text_path.exists(), row["text_path"])
            self.assertGreater(int(row["pages"]), 90)
            self.assertGreater(int(row["text_chars"]), 250_000)

    def test_curated_tables_and_network_json_are_consistent(self) -> None:
        self.assertEqual([row["year"] for row in rows("mj_library_annual_stats.csv")], DISCLOSURE_YEARS)
        self.assertEqual([row["year"] for row in rows("mj_library_membership.csv")], DISCLOSURE_YEARS)
        self.assertEqual(len(rows("mj_library_finance.csv")), 5)
        self.assertEqual(len(rows("ahmedabad_library_locations.csv")), 83)

        network = json.loads((BASE / "mj_library_network.json").read_text(encoding="utf-8"))
        self.assertEqual(network["coverage"]["proactive_disclosures"], 11)
        self.assertEqual(network["coverage"]["official_site_content_entries"], 383)
        self.assertEqual(network["coverage"]["ahmedabad_library_location_sources"]["amc_library_geojson"], 62)
        self.assertEqual(network["coverage"]["ahmedabad_library_location_sources"]["civic_json_library"], 21)
        self.assertEqual(network["derived_2025_26"]["library_income_share_pct"], 3.7)
        self.assertEqual(
            network["derived_2025_26"]["estimated_core_membership_fee_revenue_pct_of_total_budget"],
            0.761,
        )


if __name__ == "__main__":
    unittest.main()
