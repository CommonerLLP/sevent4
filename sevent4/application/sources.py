from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sevent4.ports.sources import (
    SourcesHtmlWriter,
    SourcesInputRepository,
    SourcesJsonWriter,
    SourcesRenderer,
)

PUBLIC_SOURCES_SCHEMA = "sevent4.public_sources.v1"

# Fields promoted to the public artifact. `evidence` (the internal on-disk
# record behind an entry) is deliberately NOT published: it names files in the
# gitignored data/ tree, so on the public surface it would be a dead path. Its
# existence is enforced at load time by the filesystem adapter instead.
_PUBLIC_FIELDS = ("id", "kind", "label", "url", "notes")


@dataclass(frozen=True)
class SourcesPageBuildResult:
    html: str
    payload: dict[str, Any]


def _validate(entries: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for i, entry in enumerate(entries):
        for field in ("id", "kind", "label"):
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"sources[{i}]: missing or blank required field {field!r}")
        if entry["id"] in seen:
            raise ValueError(f"sources[{i}]: duplicate id {entry['id']!r}")
        seen.add(entry["id"])
        url = entry.get("url")
        if url is not None and not (
            isinstance(url, str) and url.startswith(("http://", "https://"))
        ):
            # same discipline as the officials popups (#104): a non-URL never
            # becomes an <a href>; record it as null + a note instead
            raise ValueError(f"sources[{i}] ({entry['id']}): url must be http(s) or null, got {url!r}")


def public_sources_payload(
    city_id: str, city_name: str, compiled: str, entries: list[dict[str, Any]]
) -> dict[str, Any]:
    _validate(entries)
    return {
        "schema": PUBLIC_SOURCES_SCHEMA,
        "city": city_id,
        "city_name": city_name,
        "compiled": compiled or None,
        "count": len(entries),
        "sources": [
            {field: entry.get(field) for field in _PUBLIC_FIELDS} for entry in entries
        ],
    }


def publish_sources_page(
    repository: SourcesInputRepository,
    html_writer: SourcesHtmlWriter,
    json_writer: SourcesJsonWriter,
    render: SourcesRenderer,
) -> SourcesPageBuildResult:
    inputs = repository.load()
    payload = public_sources_payload(
        inputs.city.id, inputs.city.name, inputs.compiled, inputs.entries
    )
    html = render(inputs.city, inputs.compiled, inputs.entries)
    html_writer.write_html(html)
    json_writer.write_json(payload)
    return SourcesPageBuildResult(html=html, payload=payload)
