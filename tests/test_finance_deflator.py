import unittest

from sevent4.adapters.finance_filesystem import load_deflator_series
from sevent4.domain.deflator import deflate, index_for, latest_confirmed_year


class DeflatorDomainTest(unittest.TestCase):
    """Pure domain logic — every function takes the series as a plain dict,
    no filesystem IO. Matches this repo's hex convention (see
    sevent4/domain/amc_budget.py's own docstring)."""

    SERIES = {"2011-12": 93.3, "2012-13": 102.5, "2024-25": 192.6}

    def test_deflate_identity_and_round_trip(self) -> None:
        self.assertEqual(deflate(self.SERIES, 100.0, "2011-12", "2011-12"), 100.0)
        forward = deflate(self.SERIES, 100.0, "2011-12", "2012-13")
        back = deflate(self.SERIES, forward, "2012-13", "2011-12")
        self.assertAlmostEqual(back, 100.0, places=6)

    def test_deflate_matches_public_finance_anchor_values(self) -> None:
        # RBI HBS 2023-24 Table 37, CPI-Combined annual averages (base CY2012=100).
        self.assertEqual(index_for(self.SERIES, "2011-12"), 93.3)
        self.assertEqual(
            deflate(self.SERIES, 100.0, "2011-12", "2012-13"),
            100 * 102.5 / 93.3,
        )

    def test_latest_confirmed_year(self) -> None:
        self.assertEqual(latest_confirmed_year(self.SERIES), "2024-25")

    def test_uncovered_year_raises_with_coverage_message(self) -> None:
        with self.assertRaisesRegex(ValueError, "2011-12 to 2024-25"):
            index_for(self.SERIES, "2026-27")

    def test_malformed_fiscal_year_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "YYYY-YY"):
            index_for(self.SERIES, "2015")


class DeflatorAdapterTest(unittest.TestCase):
    """The one place that touches disk: confirms the vendored series file
    loads and covers what public-finance's REQ-0011 delivery promised."""

    def test_load_deflator_series_covers_fy2005_06_to_fy2024_25(self) -> None:
        series = load_deflator_series()
        years = sorted(series)
        self.assertEqual(years[0], "2005-06")
        self.assertEqual(years[-1], "2024-25")
        self.assertEqual(latest_confirmed_year(series), "2024-25")

    def test_loaded_series_matches_public_finance_delivery_note(self) -> None:
        series = load_deflator_series()
        # public-finance's REQ-0011 delivery note: "875cr -> 10,500cr, 12.0x
        # nominal ~= 3.5x in real 2024-25 rupees".
        real_2005_06_in_2024_25 = deflate(series, 875.28, "2005-06", "2024-25")
        self.assertAlmostEqual(real_2005_06_in_2024_25, 3011.4, delta=0.5)


if __name__ == "__main__":
    unittest.main()
