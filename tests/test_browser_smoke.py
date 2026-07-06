from pathlib import Path
import unittest

from sevent4.qa.browser_smoke import SMOKE_PATHS, SMOKE_VIEWPORTS, build_screenshot_command, is_ignored_request, screenshot_path


class BrowserSmokeTest(unittest.TestCase):
    def test_browser_smoke_covers_root_home_and_seed_console(self) -> None:
        self.assertEqual(
            SMOKE_PATHS,
            (
                "/index.html",
                "/public/index.html",
                "/public/cities/ahmedabad/index.html",
                "/public/cities/bengaluru/finance/index.html",
            ),
        )

    def test_browser_smoke_covers_mobile_tablet_and_desktop_viewports(self) -> None:
        self.assertEqual(
            tuple(viewport.label for viewport in SMOKE_VIEWPORTS),
            ("mobile", "tablet", "desktop"),
        )
        self.assertEqual(
            [(viewport.width, viewport.height) for viewport in SMOKE_VIEWPORTS],
            [(390, 844), (768, 1024), (1366, 900)],
        )

    def test_browser_smoke_ignores_only_browser_chrome_noise(self) -> None:
        self.assertTrue(is_ignored_request("/favicon.ico"))
        self.assertFalse(is_ignored_request("/public/assets/theme.css"))
        self.assertFalse(is_ignored_request("/whose-city/index.html?city=ahmedabad"))

    def test_screenshot_path_is_stable_for_routes(self) -> None:
        self.assertEqual(screenshot_path("/index.html", "mobile"), "mobile-index.html.png")
        self.assertEqual(
            screenshot_path("/public/cities/ahmedabad/index.html", "desktop"),
            "desktop-public-cities-ahmedabad-index.html.png",
        )
        self.assertEqual(
            screenshot_path("/public/cities/bengaluru/finance/index.html", "desktop"),
            "desktop-public-cities-bengaluru-finance-index.html.png",
        )

    def test_screenshot_command_sets_viewport_size(self) -> None:
        command = build_screenshot_command(
            Path("playwright"),
            "http://127.0.0.1:9174/index.html",
            Path("out/mobile-index.html.png"),
            SMOKE_VIEWPORTS[0],
        )

        self.assertIn("--viewport-size=390,844", command)
        self.assertIn("--full-page", command)


if __name__ == "__main__":
    unittest.main()
