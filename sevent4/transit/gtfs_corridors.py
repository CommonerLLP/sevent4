from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable


def main() -> None:
    parser = argparse.ArgumentParser(description="Build route corridor GeoJSON from a GTFS feed.")
    parser.add_argument("--gtfs-dir", required=True, help="Directory containing GTFS txt files")
    parser.add_argument("--out", required=True, help="Output GeoJSON path")
    args = parser.parse_args()
    build_corridors(Path(args.gtfs_dir), Path(args.out))


def build_corridors(gtfs_dir: Path, out: Path) -> None:
    stops = _stops(gtfs_dir / "stops.txt")
    routes = _routes(gtfs_dir / "routes.txt")
    trips = _trips(gtfs_dir / "trips.txt")
    shapes = _shapes(gtfs_dir / "shapes.txt") if (gtfs_dir / "shapes.txt").exists() else {}
    stop_times = _stop_times(gtfs_dir / "stop_times.txt") if not shapes else {}

    features = []
    route_trip: dict[str, dict[str, str]] = {}
    for trip in trips:
        route_trip.setdefault(trip["route_id"], trip)

    for route_id, trip in route_trip.items():
        route = routes.get(route_id, {})
        shape_id = trip.get("shape_id")
        if shape_id and shape_id in shapes:
            line = shapes[shape_id]
        else:
            line = [stops[sid] for sid in stop_times.get(trip["trip_id"], []) if sid in stops]
        if len(line) < 2:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "route_id": route_id,
                "route_short_name": route.get("route_short_name", ""),
                "route_long_name": route.get("route_long_name", ""),
                "agency_id": route.get("agency_id", ""),
            },
            "geometry": {"type": "LineString", "coordinates": line},
        })

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")))
    print(f"wrote {out} ({len(features)} route corridors)")


def _read_csv(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


def _stops(path: Path) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for row in _read_csv(path):
        try:
            out[row["stop_id"]] = [float(row["stop_lon"]), float(row["stop_lat"])]
        except (KeyError, ValueError):
            continue
    return out


def _routes(path: Path) -> dict[str, dict[str, str]]:
    return {row["route_id"]: row for row in _read_csv(path) if row.get("route_id")}


def _trips(path: Path) -> list[dict[str, str]]:
    return [row for row in _read_csv(path) if row.get("route_id") and row.get("trip_id")]


def _shapes(path: Path) -> dict[str, list[list[float]]]:
    rows: dict[str, list[tuple[int, list[float]]]] = defaultdict(list)
    for row in _read_csv(path):
        try:
            rows[row["shape_id"]].append((int(row["shape_pt_sequence"]), [float(row["shape_pt_lon"]), float(row["shape_pt_lat"])]))
        except (KeyError, ValueError):
            continue
    return {shape_id: [point for _, point in sorted(points)] for shape_id, points in rows.items()}


def _stop_times(path: Path) -> dict[str, list[str]]:
    rows: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in _read_csv(path):
        try:
            rows[row["trip_id"]].append((int(row["stop_sequence"]), row["stop_id"]))
        except (KeyError, ValueError):
            continue
    return {trip_id: [stop_id for _, stop_id in sorted(points)] for trip_id, points in rows.items()}


if __name__ == "__main__":
    main()
