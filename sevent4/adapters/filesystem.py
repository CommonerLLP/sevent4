from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
import html.parser

from sevent4.domain.evidence import (
    EvidenceBundle,
    claim_ids_in_html,
    evidence_bundle_from_dict,
    validate_claim_ids,
)


class _LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


class PublicSiteFileRepository:
    def __init__(self, public_dir: str | Path) -> None:
        self.public_dir = Path(public_dir)

    def page_ids(self) -> set[str]:
        return {_page_id(page.relative_to(self.public_dir)) for page in self.public_dir.glob("**/index.html")}

    def links_for_page(self, page_id: str) -> list[str]:
        parser = _LinkParser()
        parser.feed((self.public_dir / _path_from_page_id(page_id)).read_text(encoding="utf-8"))
        return parser.links


class JsonEvidenceBundleRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> EvidenceBundle:
        return evidence_bundle_from_dict(json.loads(self.path.read_text(encoding="utf-8")))


class FilePollutionBoardCapacityRepository:
    def __init__(self, cities_dir: str | Path) -> None:
        self.cities_dir = Path(cities_dir)

    def list_capacity_records(self) -> Mapping[str, Mapping[str, Any]]:
        records: dict[str, Mapping[str, Any]] = {}
        for capacity_path in sorted(self.cities_dir.glob("*/source/pollution/capacity.json")):
            city = capacity_path.relative_to(self.cities_dir).parts[0]
            records[city] = json.loads(capacity_path.read_text(encoding="utf-8"))
        return records


class JsonFilePublicSurfaceWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_json(self, document: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def load_evidence_bundle(path: str | Path) -> EvidenceBundle:
    return JsonEvidenceBundleRepository(path).load()


def claim_ids_in_page(path: str | Path) -> tuple[str, ...]:
    return claim_ids_in_html(Path(path).read_text(encoding="utf-8"))


def validate_page_claim_ids(path: str | Path, bundle: EvidenceBundle) -> None:
    validate_claim_ids(claim_ids_in_page(path), bundle, str(Path(path)))


def _page_id(rel: Path) -> str:
    if rel == Path("index.html"):
        return ""
    if rel.name == "index.html":
        return rel.parent.as_posix() + "/"
    return rel.as_posix()


def _path_from_page_id(page_id: str) -> Path:
    return Path("index.html") if page_id == "" else Path(page_id) / "index.html"
