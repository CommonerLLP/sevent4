#!/usr/bin/env python3
"""Extract city-bounded rail layers from the archived Indian Railways GTFS feed.

The MobilityData Indian Railways feed is a useful rail schedule lead, but it is
not an official city suburban feed. This recipe therefore writes separate
`suburban_rail_gtfs_*` layers and provenance instead of replacing the OSM/official
suburban rail layers.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import zipfile


DEFAULT_GTFS = Path("data/cities/_shared/source/transit/gtfs/indian_railways_unofficial.zip")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("city")
    parser.add_argument("--bbox", required=True, help="minlon,minlat,maxlon,maxlat")
    parser.add_argument("--keyword", action="append", default=[], help="route name keyword to keep")
    parser.add_argument("--gtfs", type=Path, default=DEFAULT_GTFS)
    parser.add_argument("--city-root", type=Path, default=Path("data/cities"))
    args = parser.parse_args()

    bbox = tuple(float(part) for part in args.bbox.split(","))
    if len(bbox) != 4:
        raise SystemExit("--bbox must be minlon,minlat,maxlon,maxlat")
    layers = build_layers(args.gtfs, bbox, tuple(args.keyword))

    city_dir = args.city_root / args.city
    out_dir = city_dir / "layers"
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "suburban_rail_gtfs_stations.geojson", layers["stops"])
    _write_json(out_dir / "suburban_rail_gtfs_routes.geojson", layers["routes"])
    _patch_manifest(out_dir / "layer_manifest.json")

    sources_dir = city_dir / "source" / "transit"
    sources_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        sources_dir / "indian_railways_gtfs.sources.json",
        {
            "schema": "sevent4.indian_railways_gtfs.sources.v1",
            "city": args.city,
            "source": {
                "name": "Indian Railways GTFS via MobilityData",
                "url": "https://storage.googleapis.com/storage/v1/b/mdb-latest/o/in-unknown-indian-railways-gtfs-2867.zip?alt=media",
                "status": "active",
                "official": False,
                "notes": (
                    "MobilityData marks this as active but the source record names it "
                    "'Unofficial data'; use as a schedule lead, not as an official "
                    "suburban railway disclosure."
                ),
            },
            "filters": {"bbox": list(bbox), "keywords": list(args.keyword)},
            "outputs": {
                "stops": "suburban_rail_gtfs_stations.geojson",
                "routes": "suburban_rail_gtfs_routes.geojson",
                "stop_features": len(layers["stops"]["features"]),
                "route_features": len(layers["routes"]["features"]),
            },
        },
        indent=2,
    )
    print(
        f"{args.city}: wrote {len(layers['stops']['features'])} GTFS rail stops and "
        f"{len(layers['routes']['features'])} GTFS rail routes"
    )


def build_layers(gtfs_zip: Path, bbox: tuple[float, float, float, float], keywords: tuple[str, ...]) -> dict:
    tables = _read_gtfs_zip(gtfs_zip)
    stops = _stops(tables["stops.txt"])
    routes = {row["route_id"]: row for row in tables["routes.txt"] if row.get("route_id")}
    trips = {row["trip_id"]: row for row in tables["trips.txt"] if row.get("trip_id") and row.get("route_id")}
    stop_times = _stop_times(tables["stop_times.txt"])
    shapes = _shapes(tables["shapes.txt"])
    in_city_stops = {
        stop_id
        for stop_id, stop in stops.items()
        if _in_bbox(stop["coordinates"], bbox)
    }

    route_features = []
    used_stops: set[str] = set()
    seen_routes: set[str] = set()
    for trip_id, stop_ids in stop_times.items():
        trip = trips.get(trip_id)
        if not trip:
            continue
        route = routes.get(trip["route_id"], {})
        if keywords and not _matches_keywords(route, keywords):
            continue
        hits = [stop_id for stop_id in stop_ids if stop_id in in_city_stops]
        if len(hits) < 2 or trip["route_id"] in seen_routes:
            continue
        shape = shapes.get(trip.get("shape_id", ""))
        line = _clip_line_to_bbox(shape, bbox) if shape else [stops[stop_id]["coordinates"] for stop_id in hits]
        if len(line) < 2:
            continue
        seen_routes.add(trip["route_id"])
        used_stops.update(hits)
        route_features.append(
            {
                "type": "Feature",
                "properties": {
                    "route_id": trip["route_id"],
                    "route_short_name": route.get("route_short_name", ""),
                    "route_long_name": route.get("route_long_name", ""),
                    "operator": "Indian Railways",
                    "mode": "suburban_rail",
                    "source": "MobilityData Indian Railways GTFS (unofficial data)",
                },
                "geometry": {"type": "LineString", "coordinates": line},
            }
        )

    stop_features = [
        {
            "type": "Feature",
            "properties": {
                "stop_id": stop_id,
                "stop_name": stops[stop_id]["name"],
                "operator": "Indian Railways",
                "mode": "suburban_rail",
                "source": "MobilityData Indian Railways GTFS (unofficial data)",
            },
            "geometry": {"type": "Point", "coordinates": stops[stop_id]["coordinates"]},
        }
        for stop_id in sorted(used_stops, key=lambda item: stops[item]["name"])
    ]
    return {
        "stops": {"type": "FeatureCollection", "features": stop_features},
        "routes": {"type": "FeatureCollection", "features": route_features},
    }


def _read_gtfs_zip(path: Path) -> dict[str, list[dict[str, str]]]:
    with zipfile.ZipFile(path) as zf:
        names = {Path(name).name: name for name in zf.namelist()}
        return {
            table: _read_zip_csv(zf, names[table])
            for table in ("stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "shapes.txt")
        }


def _read_zip_csv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with zf.open(name) as handle:
        return list(csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig", newline="")))


def _stops(rows: list[dict[str, str]]) -> dict[str, dict]:
    out = {}
    for row in rows:
        try:
            out[row["stop_id"]] = {
                "name": row.get("stop_name", ""),
                "coordinates": [float(row["stop_lon"]), float(row["stop_lat"])],
            }
        except (KeyError, ValueError):
            continue
    return out


def _stop_times(rows: list[dict[str, str]]) -> dict[str, list[str]]:
    out: dict[str, list[tuple[int, str]]] = {}
    for row in rows:
        try:
            out.setdefault(row["trip_id"], []).append((int(row["stop_sequence"]), row["stop_id"]))
        except (KeyError, ValueError):
            continue
    return {trip_id: [stop_id for _, stop_id in sorted(points)] for trip_id, points in out.items()}


def _shapes(rows: list[dict[str, str]]) -> dict[str, list[list[float]]]:
    out: dict[str, list[tuple[int, list[float]]]] = {}
    for row in rows:
        try:
            out.setdefault(row["shape_id"], []).append(
                (int(row["shape_pt_sequence"]), [float(row["shape_pt_lon"]), float(row["shape_pt_lat"])])
            )
        except (KeyError, ValueError):
            continue
    return {shape_id: [point for _, point in sorted(points)] for shape_id, points in out.items()}


def _matches_keywords(route: dict[str, str], keywords: tuple[str, ...]) -> bool:
    haystack = " ".join(
        [route.get("route_short_name", ""), route.get("route_long_name", ""), route.get("route_desc", "")]
    ).upper()
    return any(keyword.upper() in haystack for keyword in keywords)


def _in_bbox(point: list[float], bbox: tuple[float, float, float, float]) -> bool:
    minlon, minlat, maxlon, maxlat = bbox
    lon, lat = point
    return minlon <= lon <= maxlon and minlat <= lat <= maxlat


def _clip_line_to_bbox(line: list[list[float]], bbox: tuple[float, float, float, float]) -> list[list[float]]:
    return [point for point in line if _in_bbox(point, bbox)]


def _patch_manifest(path: Path) -> None:
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = [
        {
            "id": "suburban_rail_gtfs_routes",
            "label": "Rail schedules (GTFS lead)",
            "file": "suburban_rail_gtfs_routes.geojson",
            "kind": "line",
            "group": "Transit",
            "default": False,
            "popup": ["route_short_name", "route_long_name", "operator", "source"],
            "paint": {"line-color": "#d9a94f", "line-width": 1.4, "line-opacity": 0.82},
        },
        {
            "id": "suburban_rail_gtfs_stations",
            "label": "Rail stations (GTFS lead)",
            "file": "suburban_rail_gtfs_stations.geojson",
            "kind": "circle",
            "group": "Transit",
            "default": False,
            "popup": ["stop_name", "operator", "source"],
            "paint": {
                "circle-color": "#d9a94f",
                "circle-radius": 3.0,
                "circle-stroke-color": "#101318",
                "circle-stroke-width": 0.6,
                "circle-opacity": 0.85,
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


def _write_json(path: Path, document: dict, indent: int | None = None) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":")),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
