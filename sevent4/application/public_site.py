from __future__ import annotations

import posixpath
from urllib.parse import urldefrag, urlparse

from sevent4.ports.publication import PublicPageRepository


def build_public_route_graph(page_links: dict[str, list[str]]) -> dict[str, set[str]]:
    page_ids = set(page_links)
    graph: dict[str, set[str]] = {}
    for page_id, links in page_links.items():
        graph[page_id] = {
            target
            for href in links
            if (target := public_target_page(page_id, href, page_ids)) is not None and target != page_id
        }
    return graph


def build_public_route_graph_from_repository(repository: PublicPageRepository) -> dict[str, set[str]]:
    return build_public_route_graph({page_id: repository.links_for_page(page_id) for page_id in repository.page_ids()})


def reachable_public_pages(graph: dict[str, set[str]], start: str = "") -> set[str]:
    seen = {start}
    queue = [start]
    while queue:
        current = queue.pop(0)
        for target in sorted(graph.get(current, set()) - seen):
            seen.add(target)
            queue.append(target)
    return seen


def terminal_public_pages(graph: dict[str, set[str]]) -> list[str]:
    return sorted(page_id or "index.html" for page_id, targets in graph.items() if not targets)


def public_target_page(from_page_id: str, href: str, known_pages: set[str]) -> str | None:
    target_id = resolve_public_target_page(from_page_id, href)
    return target_id if target_id in known_pages else None


def resolve_public_target_page(from_page_id: str, href: str) -> str | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or href.startswith(("mailto:", "tel:", "javascript:")):
        return None
    clean, _fragment = urldefrag(parsed.path or href)
    if not clean:
        return None
    if clean.startswith("/"):
        target_path = clean.lstrip("/")
    else:
        base_dir = posixpath.dirname(_path_from_page_id(from_page_id))
        target_path = posixpath.normpath(posixpath.join(base_dir, clean))
    if target_path == ".":
        return ""
    if clean.endswith("/") or target_path.endswith("/"):
        target_path = posixpath.join(target_path, "index.html")
    return _page_id_from_path(target_path)


def _path_from_page_id(page_id: str) -> str:
    return "index.html" if page_id == "" else posixpath.join(page_id, "index.html")


def _page_id_from_path(path: str) -> str:
    clean = posixpath.normpath(path)
    if clean == "index.html":
        return ""
    if clean.endswith("/index.html"):
        return clean.removesuffix("index.html")
    return clean
