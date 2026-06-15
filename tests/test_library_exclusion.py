import unittest

from scripts.recipes.ahmedabad.build_library_exclusion import (
    build_index,
    min_max_norm,
    nearest_point_distance_m,
    summarize,
    weighted_median,
)


def _sample_rows():
    # medians across these five wards: distance 2.0 km, deprivation 0.5.
    return [
        {"Name": "A", "nearest_library_km": 0.0, "deprivation": 0.1, "population_2020": 100.0},
        {"Name": "B", "nearest_library_km": 1.0, "deprivation": 0.4, "population_2020": 200.0},
        {"Name": "C", "nearest_library_km": 2.0, "deprivation": 0.5, "population_2020": 300.0},
        {"Name": "D", "nearest_library_km": 3.0, "deprivation": 0.8, "population_2020": 400.0},
        {"Name": "E", "nearest_library_km": 4.0, "deprivation": 0.9, "population_2020": 500.0},
    ]


class MinMaxNormTest(unittest.TestCase):
    def test_scales_to_unit_interval(self) -> None:
        norm = min_max_norm([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(norm[0], 0.0)
        self.assertEqual(norm[-1], 1.0)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in norm))

    def test_constant_series_maps_to_zero(self) -> None:
        self.assertEqual(min_max_norm([5.0, 5.0, 5.0]), [0.0, 0.0, 0.0])


class NearestPointTest(unittest.TestCase):
    def test_zero_distance_when_point_coincides(self) -> None:
        self.assertEqual(nearest_point_distance_m(10.0, 10.0, [(10.0, 10.0), (20.0, 20.0)]), 0.0)

    def test_returns_minimum_euclidean_distance(self) -> None:
        # 3-4-5 triangle; the far point must be ignored.
        self.assertEqual(nearest_point_distance_m(0.0, 0.0, [(3.0, 4.0), (100.0, 100.0)]), 5.0)


class BuildIndexTest(unittest.TestCase):
    def test_is_deterministic(self) -> None:
        first, meta_first = build_index(_sample_rows())
        second, meta_second = build_index(_sample_rows())
        self.assertEqual(first, second)
        self.assertEqual(meta_first, meta_second)

    def test_exclusion_index_within_unit_interval(self) -> None:
        rows, _ = build_index(_sample_rows())
        self.assertTrue(all(0.0 <= r["exclusion_index"] <= 1.0 for r in rows))
        self.assertTrue(all(0.0 <= r["access_norm"] <= 1.0 for r in rows))

    def test_double_locked_is_median_inclusive(self) -> None:
        rows, meta = build_index(_sample_rows())
        by_name = {r["Name"]: r for r in rows}
        # C sits exactly on both medians and must count as double-locked (>=).
        self.assertEqual(by_name["C"]["double_locked"], "True")
        self.assertEqual(by_name["D"]["double_locked"], "True")
        self.assertEqual(by_name["E"]["double_locked"], "True")
        # A and B are below at least one median.
        self.assertEqual(by_name["A"]["double_locked"], "False")
        self.assertEqual(by_name["B"]["double_locked"], "False")
        self.assertEqual(meta["median_deprivation"], 0.5)
        self.assertEqual(meta["median_nearest_library_km"], 2.0)

    def test_rows_sorted_by_name(self) -> None:
        rows, _ = build_index(_sample_rows())
        self.assertEqual([r["Name"] for r in rows], ["A", "B", "C", "D", "E"])


class SummarizeTest(unittest.TestCase):
    def test_people_affected_sums_locked_population(self) -> None:
        rows, meta = build_index(_sample_rows())
        summary = summarize(rows, meta)
        self.assertEqual(summary["double_locked_ward_count"], 3)
        self.assertEqual(summary["people_in_double_locked"], 1200)  # C+D+E
        self.assertEqual(summary["total_population"], 1500)
        self.assertEqual(summary["pct_population_double_locked"], 80.0)


class WeightedMedianTest(unittest.TestCase):
    def test_population_weighting(self) -> None:
        self.assertEqual(weighted_median([1.0, 2.0, 3.0], [10.0, 80.0, 10.0]), 2.0)

    def test_zero_weight_is_safe(self) -> None:
        self.assertEqual(weighted_median([1.0, 2.0], [0.0, 0.0]), 0.0)


if __name__ == "__main__":
    unittest.main()
