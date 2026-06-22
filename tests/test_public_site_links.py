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

    def test_home_starts_with_residence_question_and_game_routes(self) -> None:
        html = (PUBLIC / "index.html").read_text(encoding="utf-8")

        self.assertIn("Where do you live?", html)
        self.assertIn('href="whose-city/index.html?city=ahmedabad"', html)
        self.assertIn('href="whose-city/index.html?city=bengaluru"', html)
        self.assertIn('href="cities/index.html"', html)

    def test_game_asks_local_election_memory_before_maps(self) -> None:
        html = (PUBLIC / "whose-city" / "index.html").read_text(encoding="utf-8")

        self.assertIn("When was the last local body election here?", html)
        self.assertIn("Did you vote in it?", html)
        self.assertIn("What did you vote on?", html)
        self.assertIn("What should a local vote decide?", html)
        self.assertLess(
            html.index("When was the last local body election here?"),
            html.index("Your ward"),
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
