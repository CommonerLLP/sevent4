#!/usr/bin/env python3
"""Build metro fallback layers from saved Overpass JSON responses."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_osm_metro_layers(
    *,
    city: str,
    lines_json: Path,
    stations_json: Path,
    out_dir: Path,
    source_dir: Path,
    bbox: str = "",
) -> dict[str, int]:
    line_fc = _line_features(_elements(lines_json))
    station_fc = _station_features(_elements(stations_json))

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "metro_lines.geojson", line_fc)
    _write_json(out_dir / "metro.geojson", station_fc)
    _patch_manifest(out_dir / "layer_manifest.json")

    source_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        source_dir / "osm_metro.sources.json",
        {
            "schema": "sevent4.osm_metro.sources.v1",
            "city": city,
            "status": "fallback_osm",
            "source": "OpenStreetMap",
            "license": "ODbL",
            "raw_line_json": str(lines_json),
            "raw_station_json": str(stations_json),
            **_optional_station_xml(stations_json),
            "bbox": bbox,
            "layers": {
                "metro_lines.geojson": len(line_fc["features"]),
                "metro.geojson": len(station_fc["features"]),
            },
            "note": "Fallback geometry only; no public static GTFS feed was found for this metro system.",
        },
        indent=1,
    )
    return {"line_features": len(line_fc["features"]), "station_features": len(station_fc["features"])}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build OSM-derived metro fallback layers from Overpass JSON.")
    parser.add_argument("city")
    parser.add_argument("--lines-json", required=True, type=Path)
    parser.add_argument("--stations-json", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--bbox", default="")
    args = parser.parse_args()
    result = build_osm_metro_layers(
        city=args.city,
        lines_json=args.lines_json,
        stations_json=args.stations_json,
        out_dir=args.out_dir,
        source_dir=args.source_dir,
        bbox=args.bbox,
    )
    print(f"[{args.city}] {result['line_features']} metro lines · {result['station_features']} metro stations")


def _elements(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8")).get("elements", [])


def _line_features(elements: list[dict[str, Any]]) -> dict[str, Any]:
    features = []
    seen = set()
    for element in elements:
        if element.get("type") != "way" or element.get("id") in seen or not element.get("geometry"):
            continue
        seen.add(element.get("id"))
        tags = element.get("tags") or {}
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[point["lon"], point["lat"]] for point in element["geometry"]],
                },
                "properties": {
                    "name": tags.get("name") or tags.get("ref") or "",
                    "operator": tags.get("operator") or tags.get("network") or "",
                    "mode": "metro",
                    "source": "OpenStreetMap (fallback)",
                    "source_way_id": str(element.get("id", "")),
                },
            }
        )
    return _fc(features)


def _station_features(elements: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: dict[str, dict[str, Any]] = {}
    seen = set()
    for element in elements:
        if element.get("type") != "node" or element.get("id") in seen:
            continue
        if "lat" not in element or "lon" not in element:
            continue
        seen.add(element.get("id"))
        tags = element.get("tags") or {}
        if _is_inactive_station(tags):
            continue
        name = tags.get("name") or "Metro station"
        key = _station_key(name)
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [element["lon"], element["lat"]]},
            "properties": {
                "name": name,
                "operator": tags.get("operator") or tags.get("network") or "",
                "mode": "metro",
                "source": "OpenStreetMap (fallback)",
                "source_node_id": str(element.get("id", "")),
            },
            "_rank": _station_rank(tags),
        }
        current = by_key.get(key)
        if current is None or feature["_rank"] > current["_rank"]:
            by_key[key] = feature
    features = []
    for feature in sorted(by_key.values(), key=lambda item: item["properties"]["name"].casefold()):
        feature.pop("_rank", None)
        features.append(feature)
    return _fc(features)


def _is_inactive_station(tags: dict[str, Any]) -> bool:
    inactive_keys = ("construction", "disused", "disused:railway", "abandoned", "proposed")
    return any(key in tags for key in inactive_keys) or tags.get("railway") == "construction"


def _station_key(name: str) -> str:
    return " ".join(name.casefold().split())


def _station_rank(tags: dict[str, Any]) -> int:
    if tags.get("public_transport") == "station" or tags.get("railway") == "station":
        return 3
    if tags.get("subway") == "yes":
        return 2
    return 1


def _patch_manifest(path: Path) -> None:
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = [
        {
            "id": "metro_lines",
            "label": "Metro lines (OSM fallback)",
            "file": "metro_lines.geojson",
            "kind": "line",
            "group": "Transit",
            "default": False,
            "popup": ["name", "operator", "source"],
            "paint": {"line-color": "#dc4c4c", "line-width": 2.4, "line-opacity": 0.88},
        },
        {
            "id": "metro",
            "label": "Metro stations (OSM fallback)",
            "file": "metro.geojson",
            "kind": "circle",
            "group": "Transit",
            "default": False,
            "popup": ["name", "operator", "source"],
            "paint": {
                "circle-color": "#dc4c4c",
                "circle-radius": 3.4,
                "circle-stroke-color": "#101318",
                "circle-stroke-width": 0.7,
                "circle-opacity": 0.9,
            },
        },
    ]
    layers = list(manifest.get("layers", []))
    by_id = {layer.get("id"): idx for idx, layer in enumerate(layers)}
    for entry in entries:
        idx = by_id.get(entry["id"])
        if idx is None:
            by_id[entry["id"]] = len(layers)
            layers.append(entry)
        else:
            layers[idx] = entry
    manifest["layers"] = layers
    _write_json(path, manifest, indent=2)


def _fc(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def _write_json(path: Path, document: dict[str, Any], indent: int | None = None) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def _optional_station_xml(stations_json: Path) -> dict[str, str]:
    station_xml = stations_json.with_name(stations_json.name.replace(".overpass.json", ".osm.xml"))
    if not station_xml.exists():
        return {}
    return {"raw_station_xml": str(station_xml)}


if __name__ == "__main__":
    main()
