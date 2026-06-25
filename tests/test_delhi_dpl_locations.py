import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.recipes.delhi.extract_dpl_library import extract_dpl_locations, geocode_cache_rows


class DelhiDplLocationsTest(unittest.TestCase):
    def test_extract_dpl_locations_reads_zone_address_and_embedded_coordinates(self) -> None:
        with TemporaryDirectory() as tmp:
            html_dir = Path(tmp)
            (html_dir / "operations__central_zone.html").write_text(
                """
                <strong style="color: #000000; font-size: 20px;">Central Library</strong>
                <iframe src="https://www.google.com/maps/embed?pb=!2d77.229180829205!3d28.659943775695407"></iframe>
                <table>
                  <tr><td><span><strong>Address</strong></span></td>
                  <td><p>Delhi Public Library, Dr. Shyama Prasad Mukherjee Marg, Delhi-110006</p></td></tr>
                </table>
                """,
                encoding="utf-8",
            )

            rows = extract_dpl_locations(html_dir)

        self.assertEqual(rows[0]["name"], "Central Library")
        self.assertEqual(rows[0]["address"], "Delhi Public Library, Dr. Shyama Prasad Mukherjee Marg, Delhi-110006")
        self.assertEqual(rows[0]["latitude"], "28.659943775695407")
        self.assertEqual(rows[0]["longitude"], "77.229180829205")
        self.assertEqual(rows[0]["coordinate_source"], "google_maps_embed")

    def test_extract_dpl_locations_keeps_address_only_rows_for_geocoding(self) -> None:
        with TemporaryDirectory() as tmp:
            html_dir = Path(tmp)
            (html_dir / "operations__south_zone.html").write_text(
                """
                <table>
                  <tr><td colspan="2">Sarojini Nagar (Zonal Library)</td></tr>
                  <tr><td><strong>Address</strong></td>
                  <td><p>Delhi Public Library, H-block, Near Main Market, Sarojini Nagar, New Delhi-110023</p></td></tr>
                </table>
                """,
                encoding="utf-8",
            )

            rows = extract_dpl_locations(html_dir)
            cache = geocode_cache_rows(rows)

        self.assertEqual(rows[0]["name"], "Sarojini Nagar")
        self.assertEqual(rows[0]["geocode_status"], "needs_geocode")
        self.assertEqual(cache[0]["source_record_id"], rows[0]["source_record_id"])
        self.assertIn("Sarojini Nagar", cache[0]["geocode_query"])


if __name__ == "__main__":
    unittest.main()
