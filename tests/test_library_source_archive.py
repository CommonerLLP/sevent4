import unittest

from scripts.recipes.libraries.source_archive import (
    drive_download_url,
    parse_dpl_staffing_text,
    text_needs_ocr,
)


class LibrarySourceArchiveTest(unittest.TestCase):
    def test_drive_download_url_converts_share_link(self) -> None:
        self.assertEqual(
            drive_download_url("https://drive.google.com/file/d/abc123/view?usp=sharing"),
            "https://drive.google.com/uc?export=download&id=abc123",
        )

    def test_drive_download_url_keeps_non_drive_url(self) -> None:
        url = "https://dpl.gov.in/images/annualreport910.pdf"
        self.assertEqual(drive_download_url(url), url)

    def test_text_needs_ocr_for_image_only_extract(self) -> None:
        self.assertTrue(text_needs_ocr("ANNUAL REPORT\n2020-2021", min_chars=200))
        self.assertFalse(text_needs_ocr("x" * 250, min_chars=200))

    def test_parse_dpl_staffing_split_table(self) -> None:
        text = """
        (2) Library Administration: (as on 31-03-2024)
        Total Posts Sanctioned : 274 Filled up Post : 138 Vacant Post : 136
        Professional Ministerial Professional Ministerial Professional Ministerial
        199 75 97 41 102 34
        """
        row = parse_dpl_staffing_text("2023-24", text)
        self.assertEqual(row["total_posts_sanctioned"], "274")
        self.assertEqual(row["total_posts_filled"], "138")
        self.assertEqual(row["total_posts_vacant"], "136")
        self.assertEqual(row["professional_posts_vacant"], "102")
        self.assertEqual(row["ministerial_posts_vacant"], "34")
        self.assertEqual(row["vacancy_rate_pct"], "49.6")
        self.assertEqual(row["extraction_status"], "observed_split")

    def test_parse_dpl_staffing_prose_total_only(self) -> None:
        text = """
        2.1 Staff: The library has sanctioned staff strength of 290 comprising of 210 professionals and
        80 Non-Professionals, out of which 86 posts are lying vacant.
        """
        row = parse_dpl_staffing_text("2017-18", text)
        self.assertEqual(row["total_posts_sanctioned"], "290")
        self.assertEqual(row["total_posts_filled"], "204")
        self.assertEqual(row["total_posts_vacant"], "86")
        self.assertEqual(row["professional_posts_sanctioned"], "210")
        self.assertEqual(row["ministerial_posts_sanctioned"], "80")
        self.assertEqual(row["extraction_status"], "observed_total_only")


if __name__ == "__main__":
    unittest.main()
