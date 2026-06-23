import unittest

from sevent4.qa.browser_smoke import SMOKE_PATHS, is_ignored_request, screenshot_path


class BrowserSmokeTest(unittest.TestCase):
    def test_browser_smoke_covers_root_home_and_seed_console(self) -> None:
        self.assertEqual(
            SMOKE_PATHS,
            (
                "/index.html",
                "/public/index.html",
                "/public/cities/ahmedabad/index.html",
            ),
        )

    def test_browser_smoke_ignores_only_browser_chrome_noise(self) -> None:
        self.assertTrue(is_ignored_request("/favicon.ico"))
        self.assertFalse(is_ignored_request("/public/assets/theme.css"))
        self.assertFalse(is_ignored_request("/whose-city/index.html?city=ahmedabad"))

    def test_screenshot_path_is_stable_for_routes(self) -> None:
        self.assertEqual(screenshot_path("/index.html"), "index.html.png")
        self.assertEqual(screenshot_path("/public/cities/ahmedabad/index.html"), "public-cities-ahmedabad-index.html.png")


if __name__ == "__main__":
    unittest.main()
