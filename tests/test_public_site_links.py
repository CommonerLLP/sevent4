import unittest
from pathlib import Path

from sevent4.adapters.filesystem import PublicSiteFileRepository
from sevent4.application.public_site import (
    build_public_route_graph_from_repository,
    public_target_page,
    reachable_public_pages,
    resolve_public_target_page,
    terminal_public_pages,
)


PUBLIC = Path("public")


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def _relative_luminance(hex_color: str) -> float:
    channels = []
    for channel in _hex_to_rgb(hex_color):
        if channel <= 0.03928:
            channels.append(channel / 12.92)
        else:
            channels.append(((channel + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast_ratio(foreground: str, background: str) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def _theme_tokens(marker: str) -> dict[str, str]:
    css = (PUBLIC / "assets" / "theme.css").read_text(encoding="utf-8")
    start = css.index(marker)
    end = css.index("}", start)
    block = css[start:end]
    tokens: dict[str, str] = {}
    for declaration in block.split(";"):
        if ":#" not in declaration:
            continue
        name, value = declaration.split(":#", 1)
        tokens[name.strip()] = "#" + value.strip()
    return tokens


def _id_from_rel(rel: Path) -> str:
    if rel == Path("index.html"):
        return ""
    if rel.name == "index.html":
        return rel.parent.as_posix() + "/"
    return rel.as_posix()


def _page_id(path: Path) -> str:
    return _id_from_rel(path.relative_to(PUBLIC))


class PublicSiteLinksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = PublicSiteFileRepository(PUBLIC)
        self.pages = sorted(PUBLIC.glob("**/index.html"))
        self.page_ids = self.repository.page_ids()

    def _links_from(self, page: Path) -> list[str]:
        return self.repository.links_for_page(_page_id(page))

    def _target_page(self, from_page: Path, href: str) -> str | None:
        return public_target_page(_page_id(from_page), href, self.page_ids)

    def _resolved_target_page(self, from_page: Path, href: str) -> str | None:
        return resolve_public_target_page(_page_id(from_page), href)

    def test_public_pages_do_not_ship_placeholder_links(self) -> None:
        placeholders: list[str] = []
        for page in self.pages:
            for href in self._links_from(page):
                if href.strip() == "#":
                    placeholders.append(f"{_page_id(page) or 'index.html'} -> #")

        self.assertEqual([], placeholders)

    def test_public_pages_do_not_have_dead_internal_page_links(self) -> None:
        missing: list[str] = []
        for page in self.pages:
            for href in self._links_from(page):
                target = self._resolved_target_page(page, href)
                if target is not None and target not in self.page_ids:
                    missing.append(f"{_page_id(page) or 'index.html'} -> {href}")

        self.assertEqual([], missing)

    def test_public_pages_are_reachable_from_home_by_static_links(self) -> None:
        graph = build_public_route_graph_from_repository(self.repository)

        self.assertEqual(sorted(self.page_ids), sorted(reachable_public_pages(graph)))

    def test_public_pages_are_not_terminal_islands(self) -> None:
        terminals = terminal_public_pages(build_public_route_graph_from_repository(self.repository))

        self.assertEqual([], terminals)

    def test_shared_public_css_exposes_keyboard_focus_states(self) -> None:
        missing = [
            path.as_posix()
            for path in (
                PUBLIC / "assets" / "masthead.css",
                PUBLIC / "assets" / "atlas-ui.css",
                PUBLIC / "assets" / "why.css",
            )
            if ":focus-visible" not in path.read_text(encoding="utf-8")
        ]

        self.assertEqual([], missing)

    def test_primary_buttons_use_action_ink_token(self) -> None:
        theme = (PUBLIC / "assets" / "theme.css").read_text(encoding="utf-8")
        atlas = (PUBLIC / "assets" / "atlas-ui.css").read_text(encoding="utf-8")

        self.assertIn("--action-blue:", theme)
        self.assertIn("--on-action:", theme)
        self.assertIn("background:var(--action-blue);color:var(--on-action)", atlas)
        self.assertNotIn("background:var(--blue);color:#0a0c10", atlas)

    def test_theme_tokens_keep_light_and_dark_contrast_accessible(self) -> None:
        dark = _theme_tokens("color-scheme:dark;")
        light = _theme_tokens(":root[data-theme=light]")

        self.assertEqual("#fffdf8", light["--panel"])
        self.assertEqual("#f7f4ec", light["--panel2"])

        for tokens in (dark, light):
            self.assertGreaterEqual(_contrast_ratio(tokens["--ink"], tokens["--bg"]), 7)
            self.assertGreaterEqual(_contrast_ratio(tokens["--ink"], tokens["--panel"]), 7)
            self.assertGreaterEqual(_contrast_ratio(tokens["--mut"], tokens["--bg"]), 4.5)
            self.assertGreaterEqual(_contrast_ratio(tokens["--blue"], tokens["--bg"]), 4.5)
            self.assertGreaterEqual(
                _contrast_ratio(tokens["--on-action"], tokens["--action-blue"]),
                4.5,
            )

    def test_public_display_type_avoids_black_weight_and_negative_tracking(self) -> None:
        pages = [
            PUBLIC / "index.html",
            PUBLIC / "findings" / "index.html",
            PUBLIC / "about" / "index.html",
            PUBLIC / "devolution" / "index.html",
        ]

        for page in pages:
            html = page.read_text(encoding="utf-8")
            self.assertNotIn("font:900", html, page.as_posix())
            self.assertNotIn("letter-spacing:-", html, page.as_posix())

        self.assertIn("h1{font:400", (PUBLIC / "index.html").read_text(encoding="utf-8"))
        self.assertIn("h1{font:400", (PUBLIC / "findings" / "index.html").read_text(encoding="utf-8"))
        self.assertIn(".hero h1{font:400", (PUBLIC / "about" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("h1{font:400", (PUBLIC / "devolution" / "index.html").read_text(encoding="utf-8"))

    def test_theme_defaults_to_browser_device_preference(self) -> None:
        theme = (PUBLIC / "assets" / "theme.css").read_text(encoding="utf-8")
        script = (PUBLIC / "assets" / "theme.js").read_text(encoding="utf-8")
        home = (PUBLIC / "index.html").read_text(encoding="utf-8")

        self.assertIn("@media (prefers-color-scheme: light)", theme)
        self.assertIn(":root:not([data-theme=dark])", theme)
        self.assertIn(":root[data-theme=light]", theme)
        self.assertIn("localStorage.getItem('atlas-theme')", home)
        self.assertIn("localStorage.setItem(THEME_KEY, theme)", script)
        self.assertIn("setTheme(systemTheme(), false)", script)
        self.assertIn("hasSavedTheme()", script)
        self.assertIn("matchMedia('(prefers-color-scheme: light)')", script)

    def test_theme_toggle_uses_delegated_click_and_keyboard_handlers(self) -> None:
        script = (PUBLIC / "assets" / "theme.js").read_text(encoding="utf-8")
        masthead = (PUBLIC / "assets" / "masthead.js").read_text(encoding="utf-8")
        masthead_css = (PUBLIC / "assets" / "masthead.css").read_text(encoding="utf-8")

        self.assertIn("closest('#theme')", script)
        self.assertIn("document.addEventListener('click', toggleFrom)", script)
        self.assertIn("document.addEventListener('keydown'", script)
        self.assertIn("atlas:mastheadrendered", masthead)
        self.assertIn("atlas:mastheadrendered", script)
        self.assertIn("syncControls()", script)
        self.assertIn("'Switch to ' + next + ' theme'", script)
        self.assertIn("aria-pressed", script)
        self.assertIn("ICONS[next]", script)
        self.assertIn("stroke:currentColor", masthead_css)
        self.assertIn("min-height:44px", masthead_css)
        self.assertIn("width:44px;height:44px", masthead_css)
        self.assertNotIn("document.getElementById('theme')", script)

    def test_why_action_links_are_touch_sized(self) -> None:
        why_css = (PUBLIC / "assets" / "why.css").read_text(encoding="utf-8")

        self.assertIn(".endnav .btn{align-items:center;display:inline-flex;min-height:44px}", why_css)

    def test_home_starts_with_residence_question_and_game_routes(self) -> None:
        html = (PUBLIC / "index.html").read_text(encoding="utf-8")

        self.assertIn("Where do you live?", html)
        self.assertIn('href="whose-city/index.html?city=ahmedabad"', html)
        self.assertIn('href="whose-city/index.html?city=bengaluru"', html)
        self.assertIn('href="cities/index.html"', html)
        self.assertIn(".hero{padding-block:52px 34px}", html)
        self.assertNotIn(".hero{padding:52px 0 34px}", html)

    def test_game_uses_short_tap_warmup_before_maps(self) -> None:
        html = (PUBLIC / "whose-city" / "index.html").read_text(encoding="utf-8")
        basics = html[html.index('id="s-basics"') : html.index('id="s-basicsr"')]

        self.assertIn("Play the power map.", html)
        self.assertIn("Pick a door. Make a guess.", html)
        self.assertIn("Last local election", html)
        self.assertIn("Your street sits inside a ward", html)
        self.assertIn("Rain night", html)
        self.assertIn("No idea", html)
        self.assertIn("Reveal the trap", html)
        self.assertIn("data-basics-choice", html)
        self.assertIn("min-height:44px", html)
        self.assertNotIn("<input", basics)
        self.assertNotIn("<select", basics)
        self.assertLess(
            html.index("Play the power map."),
            html.index("Teach me what my city controls"),
        )

    def test_game_frames_political_knowledge_gap_without_shame(self) -> None:
        html = (PUBLIC / "whose-city" / "index.html").read_text(encoding="utf-8")

        self.assertIn("That knowledge gap is not a personal failure.", html)
        self.assertIn("This is a learning exercise, not a test of intelligence.", html)
        self.assertIn("Neutrality does not keep you outside politics", html)
        self.assertIn("who benefits from that confusion, and who pays for it", html)
        self.assertIn("Politicization is a practice you can learn", html)
        self.assertIn("who is protected, and who is made to live with the damage", html)


if __name__ == "__main__":
    unittest.main()
