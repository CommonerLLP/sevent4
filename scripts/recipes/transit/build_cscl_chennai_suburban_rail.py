#!/usr/bin/env python3
"""Build Chennai suburban rail/MRTS layers from CSCL station inventory.

CSCL publishes the official station/line inventory as a CSV without
coordinates. This joins that inventory to OSM rail-station geometry and emits
station + corridor layers with explicit source separation.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Chennai suburban rail layers from CSCL CSV + OSM stations.")
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--overpass-json", required=True, type=Path)
    parser.add_argument("--package-json", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--source-dir", required=True, type=Path)
    args = parser.parse_args()

    rows = _read_cscl(args.csv)
    geometry = _station_geometry(args.overpass_json)
    station_fc, route_fc = _build_layers(rows, geometry)
    mrts_station_fc, mrts_route_fc = _split_mrts_layers(station_fc, route_fc)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.out_dir / "suburban_rail_stations.geojson", station_fc)
    _write_json(args.out_dir / "suburban_rail.geojson", route_fc)
    _write_json(args.out_dir / "mrts_stations.geojson", mrts_station_fc)
    _write_json(args.out_dir / "mrts.geojson", mrts_route_fc)
    _patch_manifest(args.out_dir / "layer_manifest.json")

    args.source_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        args.source_dir / "suburban_rail.sources.json",
        _sources(args.package_json, rows, station_fc, route_fc, mrts_station_fc, mrts_route_fc),
        indent=1,
    )
    print(
        "wrote "
        f"{len(station_fc['features'])} stations and {len(route_fc['features'])} corridors"
    )


def _read_cscl(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="cp1252") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _station_geometry(path: Path) -> dict[str, tuple[float, float, dict[str, Any]]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    by_ref: dict[str, tuple[float, float, dict[str, Any]]] = {}
    by_name: list[tuple[str, float, float, dict[str, Any]]] = []
    for element in doc.get("elements", []):
        tags = element.get("tags", {})
        lat = element.get("lat") or element.get("center", {}).get("lat")
        lon = element.get("lon") or element.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        props = {
            "osm_type": element.get("type"),
            "osm_id": element.get("id"),
            "osm_name": tags.get("name", ""),
            "osm_ref": tags.get("ref") or tags.get("uic_ref") or tags.get("railway:ref") or "",
        }
        for key in ("ref", "uic_ref", "railway:ref"):
            if not tags.get(key):
                continue
            for ref in re.split(r"[:;,/ ]+", tags[key]):
                ref = ref.strip().upper()
                if ref:
                    by_ref.setdefault(ref, (float(lon), float(lat), props))
        name = _normalise(tags.get("name", ""))
        if name:
            by_name.append((name, float(lon), float(lat), props))
    return {"by_ref": by_ref, "by_name": by_name}  # type: ignore[return-value]


def _build_layers(
    rows: list[dict[str, str]],
    geometry: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    stations: dict[str, dict[str, Any]] = {}
    ordered_by_line: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        lon, lat, osm_props, match_method = _match_geometry(row, geometry)
        code = row["Station Code"].strip().upper()
        connection = row["Connection"].strip()
        ordered_by_line.setdefault(connection, []).append(row | {"_lon": lon, "_lat": lat})
        if code not in stations:
            stations[code] = {
                "type": "Feature",
                "properties": {
                    "station_code": code,
                    "name": _clean_station_name(row["Station"]),
                    "connections": [],
                    "interchange": row.get("Interchange", ""),
                    "layout": row.get("Layout", ""),
                    "parking_contract_available": row.get("Parking Contract Available", ""),
                    "cscl_zone": row.get("Zone", ""),
                    "cscl_division": row.get("Division", ""),
                    "source": "CSCL Sub Urban Rail CSV; OSM station geometry",
                    "geometry_source": "OpenStreetMap via Overpass API",
                    "geometry_match": match_method,
                    **osm_props,
                },
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
            }
        connections = stations[code]["properties"]["connections"]
        if connection not in connections:
            connections.append(connection)
    for feature in stations.values():
        feature["properties"]["connections"] = "; ".join(feature["properties"]["connections"])

    route_features = []
    for connection, line_rows in sorted(ordered_by_line.items()):
        ordered = sorted(line_rows, key=lambda item: _distance(item.get("Distance in Kms", "")))
        coordinates = [[row["_lon"], row["_lat"]] for row in ordered]
        route_features.append(
            {
                "type": "Feature",
                "properties": {
                    "name": connection,
                    "mode": "suburban_rail" if connection != "MRTS Line" else "mrts",
                    "operator": "Southern Railway",
                    "decided_by": "Union government",
                    "station_count": len(ordered),
                    "station_codes": "; ".join(row["Station Code"].strip().upper() for row in ordered),
                    "source": "CSCL Sub Urban Rail CSV; OSM station geometry",
                },
                "geometry": {"type": "LineString", "coordinates": coordinates},
            }
        )
    return _fc(list(stations.values())), _fc(route_features)


def _split_mrts_layers(station_fc: dict[str, Any], route_fc: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    mrts_routes = [
        feature
        for feature in route_fc.get("features", [])
        if feature.get("properties", {}).get("mode") == "mrts"
    ]
    mrts_station_codes = {
        code.strip()
        for feature in mrts_routes
        for code in str(feature.get("properties", {}).get("station_codes", "")).split(";")
        if code.strip()
    }
    mrts_stations = []
    for feature in station_fc.get("features", []):
        properties = feature.get("properties", {})
        station_code = str(properties.get("station_code", "")).strip()
        connections = str(properties.get("connections", ""))
        if station_code in mrts_station_codes or "MRTS Line" in connections:
            mrts_stations.append(feature)
    return _fc(mrts_stations), _fc(mrts_routes)


def _match_geometry(row: dict[str, str], geometry: dict[str, Any]) -> tuple[float, float, dict[str, Any], str]:
    code = row["Station Code"].strip().upper()
    by_ref = geometry["by_ref"]
    if code in by_ref:
        lon, lat, props = by_ref[code]
        return lon, lat, props, "station_code"
    names = [_normalise(part) for part in row["Station"].split(";")]
    for target in names:
        if not target:
            continue
        for candidate, lon, lat, props in geometry["by_name"]:
            if target == candidate or target in candidate or candidate in target:
                return lon, lat, props, "station_name"
    raise ValueError(f"No OSM geometry match for {code}: {row['Station']}")


def _normalise(value: str) -> str:
    value = value.replace("\ufffd", " ").replace("\xa0", " ")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(
        r"\brs\b|railway station|station|halt|rail terminus|marina beach|airport|cultural center|t nagar",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _clean_station_name(value: str) -> str:
    return " / ".join(part.strip().replace("\ufffd", "") for part in value.split(";") if part.strip())


def _distance(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def _fc(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def _patch_manifest(path: Path) -> None:
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = [
        {
            "id": "suburban_rail",
            "label": "Suburban rail + MRTS",
            "file": "suburban_rail.geojson",
            "kind": "line",
            "group": "Transit",
            "default": False,
            "popup": ["name", "operator", "station_count", "source"],
            "paint": {"line-color": "#8a8f98", "line-width": 1.8, "line-opacity": 0.85},
        },
        {
            "id": "suburban_rail_stations",
            "label": "Suburban rail + MRTS stations",
            "file": "suburban_rail_stations.geojson",
            "kind": "circle",
            "group": "Transit",
            "default": False,
            "popup": ["name", "station_code", "connections", "interchange", "layout", "source"],
            "paint": {
                "circle-color": "#edc233",
                "circle-radius": 3.2,
                "circle-stroke-color": "#101318",
                "circle-stroke-width": 0.6,
                "circle-opacity": 0.85,
            },
        },
        {
            "id": "mrts",
            "label": "MRTS corridor",
            "file": "mrts.geojson",
            "kind": "line",
            "group": "Transit",
            "default": False,
            "popup": ["name", "operator", "station_count", "source"],
            "paint": {"line-color": "#22a6a6", "line-width": 2.0, "line-opacity": 0.88},
        },
        {
            "id": "mrts_stations",
            "label": "MRTS stations",
            "file": "mrts_stations.geojson",
            "kind": "circle",
            "group": "Transit",
            "default": False,
            "popup": ["name", "station_code", "connections", "interchange", "layout", "source"],
            "paint": {
                "circle-color": "#22a6a6",
                "circle-radius": 3.2,
                "circle-stroke-color": "#101318",
                "circle-stroke-width": 0.6,
                "circle-opacity": 0.85,
            },
        },
    ]
    by_id = {layer.get("id"): idx for idx, layer in enumerate(manifest.get("layers", []))}
    for entry in entries:
        idx = by_id.get(entry["id"])
        if idx is None:
            manifest.setdefault("layers", []).append(entry)
        else:
            manifest["layers"][idx] = entry
    _write_json(path, manifest, indent=2)


def _sources(
    package_json: Path,
    rows: list[dict[str, str]],
    station_fc: dict[str, Any],
    route_fc: dict[str, Any],
    mrts_station_fc: dict[str, Any],
    mrts_route_fc: dict[str, Any],
) -> dict[str, Any]:
    package = json.loads(package_json.read_text(encoding="utf-8"))
    result = package["result"][0] if isinstance(package.get("result"), list) else package.get("result", {})
    return {
        "schema": "sevent4.suburban_rail.sources.v1",
        "city": "chennai",
        "dataset": {
            "title": result.get("title", "Sub Urban Rail"),
            "url": result.get("url", "https://opendata.cscl.co.in/dataset/sub-urban-rail"),
            "notes": result.get("notes", ""),
            "metadata_created": result.get("metadata_created", ""),
            "metadata_modified": result.get("metadata_modified", ""),
            "resource_url": result.get("resources", [{}])[0].get("url", ""),
        },
        "layers": {
            "suburban_rail_stations.geojson": len(station_fc["features"]),
            "suburban_rail.geojson": len(route_fc["features"]),
            "mrts_stations.geojson": len(mrts_station_fc["features"]),
            "mrts.geojson": len(mrts_route_fc["features"]),
        },
        "source_rows": len(rows),
        "geometry_source": "OpenStreetMap via Overpass API, joined by station code/name.",
    }


def _write_json(path: Path, document: dict[str, Any], indent: int | None = None) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
