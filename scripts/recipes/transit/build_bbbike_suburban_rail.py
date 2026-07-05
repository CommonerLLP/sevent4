#!/usr/bin/env python3
"""Build a first-pass suburban rail layer from a BBBike Osmium GeoJSON extract.

This is a fallback for cities where public Overpass is too slow/rate-limited
for the generic rail pull. The output remains OSM-derived and non-authoritative.
"""
from __future__ import annotations

import argparse
import json
import lzma
from pathlib import Path

RAIL_LINE_PROPS = ("name", "ref", "usage", "operator", "network")
RAIL_STATION_PROPS = ("name", "ref", "operator", "network")


def build_layers(city: str, extract: Path, source_url: str) -> tuple[dict, dict, dict]:
    lines = []
    stations = []
    for feature in _iter_features(extract):
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        if geom.get("type") == "LineString" and props.get("railway") == "rail":
            lines.append(_line_feature(feature, city))
        elif geom.get("type") == "Point" and _is_suburban_station(props):
            stations.append(_station_feature(feature, city))

    sources = {
        "layer": "suburban_rail",
        "publisher": "OpenStreetMap contributors via BBBike extract",
        "licence": "ODbL",
        "source_url": source_url,
        "local": str(extract),
        "decided_by": "Union — Indian Railways (Railways = Union List, Entry 22)",
        "trust": "NON-AUTHORITATIVE (OSM) — illustrative network geometry, first pass",
        "to_improve": "verify route membership against official railway/GTFS source; filter freight/yard ways",
        "citation": "OpenStreetMap contributors / BBBike -> sevent4",
        "city": city,
        "line_features": len(lines),
        "station_features": len(stations),
    }
    return (
        {"type": "FeatureCollection", "features": lines},
        {"type": "FeatureCollection", "features": stations},
        sources,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build OSM-derived suburban rail layers from a BBBike extract.")
    parser.add_argument("city")
    parser.add_argument("--extract", required=True, type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--city-root", type=Path, default=Path("data/cities"))
    parser.add_argument("--public-root", type=Path)
    args = parser.parse_args()

    line_fc, station_fc, sources = build_layers(args.city, args.extract, args.source_url)
    _write_city(args.city, args.city_root, line_fc, station_fc, sources)
    if args.public_root:
        _write_city(args.city, args.public_root, line_fc, station_fc, sources, public=True)
    print(f"[{args.city}] {len(line_fc['features'])} rail segments · {len(station_fc['features'])} stations")


def _iter_features(path: Path):
    opener = lzma.open if path.suffix == ".xz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line.startswith('{"type":"Feature"'):
                continue
            if line.endswith(","):
                line = line[:-1]
            yield json.loads(line)


def _line_feature(feature: dict, city: str) -> dict:
    props = feature.get("properties") or {}
    out_props = {key: props.get(key, "") for key in RAIL_LINE_PROPS}
    out_props.update(
        {
            "name": props.get("name") or props.get("ref") or "",
            "operator": props.get("operator") or "Indian Railways",
            "decided_by": "Union (Indian Railways)",
            "source": f"OpenStreetMap / BBBike ({city}; first pass)",
        }
    )
    return {"type": "Feature", "geometry": feature["geometry"], "properties": out_props}


def _station_feature(feature: dict, city: str) -> dict:
    props = feature.get("properties") or {}
    out_props = {key: props.get(key, "") for key in RAIL_STATION_PROPS}
    out_props.update(
        {
            "name": props.get("name", "Station"),
            "operator": props.get("operator") or "Indian Railways",
            "source": f"OpenStreetMap / BBBike ({city}; first pass)",
        }
    )
    return {"type": "Feature", "geometry": feature["geometry"], "properties": out_props}


def _is_suburban_station(props: dict) -> bool:
    text = " ".join(str(props.get(key, "")) for key in ("network", "operator", "railway", "public_transport", "train"))
    low = text.lower()
    if any(skip in low for skip in ("metro", "monorail", "bus")):
        return False
    if props.get("railway") in {"station", "halt"} and props.get("train") == "yes":
        return True
    if any(token in low for token in ("mumbai suburban", "western railway", "central railway", "western railways", "central railways", "indian railways", " cr", " wr")):
        return props.get("public_transport") == "station" or props.get("railway") in {"station", "halt"}
    return False


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
    ids = {layer.get("id"): idx for idx, layer in enumerate(layers)}
    for entry in entries:
        idx = ids.get(entry["id"])
        if idx is None:
            ids[entry["id"]] = len(layers)
            layers.append(entry)
        else:
            layers[idx] = entry
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
    path.write_text(json.dumps(document, ensure_ascii=False, indent=indent), encoding="utf-8")


if __name__ == "__main__":
    main()
