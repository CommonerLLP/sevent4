#!/usr/bin/env python3
"""Build suburban rail layers from saved Overpass JSON responses."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

from sevent4.domain.suburban_rail import (
    collect_stations,
    collect_ways,
    line_features,
    rail_sources,
    station_features,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build OSM-derived suburban rail layers from Overpass JSON.")
    parser.add_argument("city")
    parser.add_argument("--rail-json", required=True, type=Path)
    parser.add_argument("--stations-json", required=True, type=Path)
    parser.add_argument("--city-root", type=Path, default=Path("data/cities"))
    parser.add_argument("--public-root", type=Path)
    parser.add_argument("--bbox", default="")
    parser.add_argument("--membership-html", type=Path)
    args = parser.parse_args()

    line_fc, station_fc, sources = build_layers(
        args.city,
        args.rail_json,
        args.stations_json,
        args.bbox,
        args.membership_html,
    )
    _write_city(args.city, args.city_root, line_fc, station_fc, sources)
    if args.public_root:
        _write_city(args.city, args.public_root, line_fc, station_fc, sources, public=True)
    print(f"[{args.city}] {len(line_fc['features'])} rail segments · {len(station_fc['features'])} stations")


def build_layers(
    city: str,
    rail_json: Path,
    stations_json: Path,
    bbox: str = "",
    membership_html: Path | None = None,
) -> tuple[dict, dict, dict]:
    ways: dict = {}
    collect_ways(_read_elements(rail_json), ways)
    snodes: dict = {}
    collect_stations(_read_elements(stations_json), snodes)
    line_fc = {"type": "FeatureCollection", "features": line_features(ways)}
    membership_rows = _membership_rows(membership_html) if membership_html else []
    if membership_rows:
        snodes, missing = _filter_stations_by_membership(snodes, membership_rows)
    else:
        missing = []
    station_fc = {"type": "FeatureCollection", "features": station_features(snodes)}
    sources = rail_sources(city)
    sources.update(
        {
            "schema": "sevent4.suburban_rail.sources.v1",
            "geometry_source": "OpenStreetMap via Overpass API",
            "raw_rail_json": str(rail_json),
            "raw_station_json": str(stations_json),
            "bbox": bbox,
            "line_features": len(line_fc["features"]),
            "station_features": len(station_fc["features"]),
            "membership_source": str(membership_html) if membership_html else "",
            "membership_rows": len(membership_rows),
            "membership_missing_geometry": missing,
        }
    )
    return line_fc, station_fc, sources


def _read_elements(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")).get("elements", [])


def _membership_rows(path: Path) -> list[dict]:
    parser = _StationTableParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    rows = []
    for row in parser.rows:
        if not row or not row[0].isdigit() or len(row) < 5:
            continue
        rows.append({"name": row[1], "line": row[4]})
    return rows


def _filter_stations_by_membership(snodes: dict, rows: list[dict]) -> tuple[dict, list[str]]:
    wanted = {_normalise(row["name"]): row for row in rows if _normalise(row["name"])}
    matched: dict[str, dict] = {}
    for element in snodes.values():
        tags = element.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or ""
        key = _normalise(name)
        if key not in wanted:
            continue
        current = matched.get(key)
        if current is None or _station_rank(element) > _station_rank(current):
            enriched = dict(element)
            enriched["tags"] = dict(tags)
            enriched["tags"]["kolkata_suburban_line"] = wanted[key]["line"]
            enriched["tags"]["membership_source"] = "Wikipedia station list"
            matched[key] = enriched
    missing = [row["name"] for key, row in wanted.items() if key not in matched]
    return {element["id"]: element for element in matched.values()}, missing


def _station_rank(element: dict) -> int:
    tags = element.get("tags", {})
    rank = 0
    if tags.get("railway") == "station":
        rank += 2
    if tags.get("operator") in {"ER", "SER", "Eastern Railway", "South Eastern Railway"}:
        rank += 1
    return rank


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"\b(railway|station|halt|junction|jn|road|rd)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


class _StationTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._table_depth = 0
        self._in_row = False
        self._in_cell = False
        self.rows: list[list[str]] = []
        self._row: list[str] = []
        self._cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table_depth += 1
        if self._table_depth and tag == "tr":
            self._in_row = True
            self._row = []
        if self._in_row and tag in {"td", "th"}:
            self._in_cell = True
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if self._in_cell and tag in {"td", "th"}:
            self._row.append(" ".join("".join(self._cell).split()))
            self._in_cell = False
        if self._in_row and tag == "tr":
            if self._row:
                self.rows.append(self._row)
            self._in_row = False
        if tag == "table" and self._table_depth:
            self._table_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell.append(data)


def _write_city(
    city: str,
    root: Path,
    line_fc: dict,
    station_fc: dict,
    sources: dict,
    public: bool = False,
) -> None:
    city_dir = root / city
    layers = city_dir / "layers"
    layers.mkdir(parents=True, exist_ok=True)
    _write_json(layers / "suburban_rail.geojson", line_fc)
    _write_json(layers / "suburban_rail_stations.geojson", station_fc)
    _patch_manifest(layers / "layer_manifest.json")
    if not public:
        src = city_dir / "source" / "transit"
        src.mkdir(parents=True, exist_ok=True)
        _write_json(src / "suburban_rail.sources.json", sources, indent=1)


def _patch_manifest(path: Path) -> None:
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = [_line_manifest_entry(), _station_manifest_entry()]
    layers = list(manifest.get("layers", []))
    by_id = {layer.get("id"): index for index, layer in enumerate(layers)}
    for entry in entries:
        index = by_id.get(entry["id"])
        if index is None:
            by_id[entry["id"]] = len(layers)
            layers.append(entry)
        else:
            layers[index] = entry
    manifest["layers"] = layers
    _write_json(path, manifest, indent=2)


def _line_manifest_entry() -> dict:
    return {
        "id": "suburban_rail",
        "label": "Suburban rail — Indian Railways (Union)",
        "file": "suburban_rail.geojson",
        "kind": "line",
        "group": "Transit",
        "default": False,
        "popup": ["name", "operator", "decided_by", "source"],
        "paint": {"line-color": "#edc233", "line-width": 1.8, "line-opacity": 0.85},
    }


def _station_manifest_entry() -> dict:
    return {
        "id": "suburban_rail_stations",
        "label": "Suburban rail stations",
        "file": "suburban_rail_stations.geojson",
        "kind": "circle",
        "group": "Transit",
        "default": False,
        "popup": ["name", "operator", "source"],
        "paint": {
            "circle-color": "#edc233",
            "circle-radius": 3.2,
            "circle-stroke-color": "#101318",
            "circle-stroke-width": 0.6,
            "circle-opacity": 0.85,
        },
    }


def _write_json(path: Path, document: dict, indent: int | None = None) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
