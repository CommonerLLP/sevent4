from __future__ import annotations

from dataclasses import dataclass, replace
import posixpath
from typing import Any, Iterable, Mapping
from urllib.parse import urldefrag, urlparse

from sevent4.ports.publication import (
    DevolutionScorecardPublisher,
    DevolutionScorecardRepository,
    PublicPageRepository,
)


ELECTED_SERVICE_TYPES = {"corporation"}
CONTEXT_ONLY_SERVICES = {"electricity", "police"}
DECIDER_BY_TYPE = {
    "corporation": "city",
    "state_board": "state",
    "state_dept": "state",
    "spv": "state",
    "private": "state",
    "railways": "centre",
}
SERVICE_LABELS = {
    "water": "Water supply",
    "sewerage": "Sewerage / sanitation",
    "electricity": "Electricity",
    "city_bus": "City bus",
    "brt": "BRT",
    "metro": "Metro",
    "roads": "Roads",
    "development_authority": "Urban planning / land",
    "solid_waste": "Solid waste",
    "street_lighting": "Street lighting",
    "storm_water": "Storm-water drains",
    "parks": "Parks / open spaces",
    "public_health": "Public health",
    "police": "Police",
    "fire": "Fire services",
}
SERVICE_TYPE_LABELS = {
    "corporation": "your elected corporation",
    "state_board": "a state board",
    "spv": "a state SPV",
    "state_dept": "the state govt",
    "private": "a private firm",
    "railways": "Indian Railways",
    "na": "-",
}


@dataclass(frozen=True)
class DevolutionScorecardResult:
    scorecard: dict[str, dict[str, Any]]
    governance_updates: dict[str, dict[str, dict[str, int]]]
    preserved: tuple[str, ...]
    dropped: tuple[str, ...]
    governance_write_count: int = 0


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


def build_devolution_scorecard(
    service_providers: Mapping[str, Mapping[str, Any]],
    registry_city_ids: Iterable[str],
    existing_scorecard: Mapping[str, Mapping[str, Any]] | None = None,
) -> DevolutionScorecardResult:
    registry = tuple(registry_city_ids)
    registry_set = set(registry)
    existing = existing_scorecard or {}
    computed_rows = {
        city_id: _score_city_devolution(city_id, services)
        for city_id, services in service_providers.items()
        if not city_id.startswith("_") and city_id in registry_set
    }

    scorecard: dict[str, dict[str, Any]] = {}
    governance_updates: dict[str, dict[str, dict[str, int]]] = {}
    preserved: list[str] = []
    for city_id in registry:
        if city_id in computed_rows:
            row = computed_rows[city_id]
            scorecard[city_id] = row
            governance_updates[city_id] = {
                "devolution": {"elected": row["elected"], "total": row["n"], "pct": row["pct"]},
                "decided_by": dict(row["decided"]),
            }
        elif city_id in existing:
            scorecard[city_id] = dict(existing[city_id])
            preserved.append(city_id)

    dropped = tuple(
        sorted(
            city_id
            for city_id in service_providers
            if not city_id.startswith("_") and city_id not in registry_set
        )
    )
    return DevolutionScorecardResult(
        scorecard=scorecard,
        governance_updates=governance_updates,
        preserved=tuple(preserved),
        dropped=dropped,
    )


def publish_devolution_scorecard_from_repository(
    repository: DevolutionScorecardRepository,
    publisher: DevolutionScorecardPublisher,
) -> DevolutionScorecardResult:
    result = build_devolution_scorecard(
        repository.load_service_providers(),
        repository.load_registry_city_ids(),
        repository.load_existing_scorecard(),
    )
    publisher.write_scorecard(result.scorecard)
    write_count = 0
    for city_id, update in result.governance_updates.items():
        if publisher.write_governance_metrics(city_id, update):
            write_count += 1
    return replace(result, governance_write_count=write_count)


def format_devolution_scorecard_report(result: DevolutionScorecardResult, scorecard_path: str) -> str:
    lines = [
        "CUT 1 - DEVOLUTION: resident-facing services run by the ELECTED corporation",
        f"{'city':<14}{'elected/total':>14}{'%':>6}",
    ]
    for city_id, row in sorted(result.scorecard.items(), key=lambda item: item[1]["pct"]):
        lines.append(f"{row['name']:<14}{(str(row['elected'])+'/'+str(row['n'])):>14}{row['pct']:>5}%")
    lines.extend(
        [
            "",
            "CUT 2 - DECIDED_BY: of ALL arrangements (incl. electricity/police), share the elected CITY decided",
            f"{'city':<14}{'city/total':>12}{'%city':>7}   (state / centre)",
        ]
    )
    for city_id, row in sorted(result.scorecard.items(), key=lambda item: item[1]["decided"]["pct_city"]):
        decided = row["decided"]
        lines.append(
            f"{row['name']:<14}{(str(decided['city'])+'/'+str(decided['total'])):>12}"
            f"{decided['pct_city']:>6}%   ({decided['state']} / {decided['centre']})"
        )
    if result.preserved:
        lines.append(f"preserved special-case rows (absent from service map): {list(result.preserved)}")
    if result.dropped:
        lines.append(f"dropped service-map entries with no console (not in registry): {list(result.dropped)}")
    lines.append(f"\nwrote {scorecard_path} (both cuts) + injected into {result.governance_write_count} governance.json files")
    return "\n".join(lines)


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


def _score_city_devolution(city_id: str, services: Mapping[str, Any]) -> dict[str, Any]:
    elected = 0
    scored: list[str] = []
    taken: list[tuple[str, str, str]] = []
    decided = {"city": 0, "state": 0, "centre": 0}
    decided_total = 0
    for service_id, service in services.items():
        if service_id.startswith("_") or not isinstance(service, Mapping):
            continue
        service_type = service.get("type")
        if service_type == "na":
            continue
        decided[DECIDER_BY_TYPE.get(str(service_type), "state")] += 1
        decided_total += 1
        if service_id in CONTEXT_ONLY_SERVICES:
            continue
        scored.append(service_id)
        if service_type in ELECTED_SERVICE_TYPES:
            elected += 1
        else:
            taken.append((SERVICE_LABELS.get(service_id, service_id), str(service.get("provider", "")), str(service_type)))
    scored_count = len(scored)
    pct = round(100 * elected / scored_count) if scored_count else 0
    pct_city = round(100 * decided["city"] / decided_total) if decided_total else 0
    return {
        "name": city_id.title(),
        "elected": elected,
        "n": scored_count,
        "pct": pct,
        "decided": {**decided, "total": decided_total, "pct_city": pct_city},
        "taken": [
            {"service": label, "provider": provider, "by": SERVICE_TYPE_LABELS.get(service_type, service_type)}
            for label, provider, service_type in taken
        ],
    }


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
