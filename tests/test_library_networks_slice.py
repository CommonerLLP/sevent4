import unittest

from sevent4.domain.library_networks import (
    natural_key,
    normalize_name,
    one_year,
    plain_text,
    proactive_disclosure_year,
    sorted_js_object,
    source_counts,
    year_from_text,
)


class LibraryNetworksDomainTest(unittest.TestCase):
    def test_plain_text_strips_html(self) -> None:
        self.assertEqual(plain_text("<p>Hello&amp;  <b>world</b></p>"), "Hello& world")

    def test_normalize_and_natural_key(self) -> None:
        self.assertEqual(normalize_name("M.J. Library #2"), "m j library 2")
        self.assertEqual(natural_key("a10b2"), ["a", 10, "b", 2, ""])

    def test_year_from_text_patterns(self) -> None:
        self.assertEqual(year_from_text("FY 2021-2022"), "2021-22")
        self.assertEqual(year_from_text("2021-22 report"), "2021-22")
        self.assertEqual(year_from_text("ref 202122 x"), "2021-22")
        self.assertIsNone(year_from_text("no year here"))

    def test_proactive_disclosure_year(self) -> None:
        self.assertEqual(proactive_disclosure_year("PRO ACTIVE DISCLOSURE 2025-26 ..."), "2025-26")
        self.assertIsNone(proactive_disclosure_year("nothing"))

    def test_one_year_and_source_counts(self) -> None:
        rows = [{"year": "2021-22", "source_category": "a"}, {"year": "2022-23", "source_category": "a"}]
        self.assertEqual(one_year(rows, "2022-23")["source_category"], "a")
        with self.assertRaises(KeyError):
            one_year(rows, "1999-00")
        self.assertEqual(source_counts(rows), {"a": 2})

    def test_sorted_js_object_natural_order(self) -> None:
        out = sorted_js_object({"item10": {"x": "1"}, "item2": {"x": "2"}})
        self.assertEqual(list(out.keys()), ["item2", "item10"])


class LibraryNetworksShimTest(unittest.TestCase):
    def test_shim_reexports_for_existing_importers(self) -> None:
        # enrich_mj does: from scripts.recipes.library_networks import parse_js_object, plain_text
        from scripts.recipes import library_networks as shim

        for name in ("parse_js_object", "plain_text", "export_pdf_texts", "read_csv", "write_json", "year_from_text"):
            self.assertTrue(hasattr(shim, name), f"shim must re-export {name}")


if __name__ == "__main__":
    unittest.main()
