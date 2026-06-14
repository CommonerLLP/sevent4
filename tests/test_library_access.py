import unittest

from scripts.recipes.accessibility.library_access import (
    haversine_m,
    nearest_library_access,
    threshold_share,
    weighted_quantile,
)


class LibraryAccessTest(unittest.TestCase):
    def test_weighted_quantile_uses_population_weights(self) -> None:
        rows = [
            {"minutes": 5.0, "population": 10.0},
            {"minutes": 20.0, "population": 80.0},
            {"minutes": 60.0, "population": 10.0},
        ]

        self.assertEqual(weighted_quantile(rows, "minutes", "population", 0.50), 20.0)
        self.assertEqual(weighted_quantile(rows, "minutes", "population", 0.90), 60.0)

    def test_threshold_share_reports_population_share(self) -> None:
        rows = [
            {"minutes": 10.0, "population": 25.0},
            {"minutes": 35.0, "population": 75.0},
        ]

        self.assertEqual(threshold_share(rows, "minutes", "population", 30.0), 25.0)

    def test_haversine_m_is_reasonable_for_short_city_distance(self) -> None:
        distance = haversine_m(28.6599438, 77.2291808, 28.6572918, 77.2303200)

        self.assertGreater(distance, 250.0)
        self.assertLess(distance, 400.0)

    def test_nearest_library_access_computes_walk_minutes(self) -> None:
        origins = [
            {"origin_id": "near", "latitude": "28.6599438", "longitude": "77.2291808", "population": "100"},
            {"origin_id": "far", "latitude": "28.6100", "longitude": "77.2000", "population": "50"},
        ]
        libraries = [
            {"library_id": "central", "latitude": "28.6599438", "longitude": "77.2291808", "name": "Central"},
            {"library_id": "south", "latitude": "28.5754", "longitude": "77.1939", "name": "South"},
        ]

        rows = nearest_library_access(origins, libraries, walk_speed_kmph=4.8)

        self.assertEqual(rows[0]["nearest_library_id"], "central")
        self.assertEqual(rows[0]["walk_minutes_to_nearest_library"], 0.0)
        self.assertEqual(rows[1]["nearest_library_id"], "south")
        self.assertGreater(rows[1]["walk_minutes_to_nearest_library"], 20.0)


if __name__ == "__main__":
    unittest.main()
