#!/usr/bin/env python3
"""Build fallback static GTFS from OSM bus route relations."""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any


def build_osm_bus_route_gtfs(
    *,
    source_json: Path,
    out_zip: Path,
    provenance_path: Path,
    feed_id: str,
    agency_id: str,
    agency_name: str,
    network: str,
    generated_at: str,
    source_url: str,
    provenance_status: str,
    operator: str = "",
) -> dict[str, int]:
    data = json.loads(source_json.read_text(encoding="utf-8"))
    elements = data.get("elements", [])
    nodes = {element["id"]: element for element in elements if element.get("type") == "node"}
    ways = {element["id"]: element for element in elements if element.get("type") == "way"}
    relations = [element for element in elements if _matches_relation(element, network, operator)]

    route_rows = []
    stop_rows = []
    trip_rows = []
    stop_time_rows = []
    frequency_rows = []
    shape_rows = []
    skipped = []
    forward_shape_points = 0

    for relation in sorted(relations, key=lambda item: str(item.get("id"))):
        tags = relation.get("tags") or {}
        origin = _clean(tags.get("from"))
        destination = _clean(tags.get("to"))
        shape = _relation_shape(relation, ways, nodes)
        if not origin or not destination or len(shape) < 2:
            skipped.append(
                {
                    "relation_id": relation.get("id"),
                    "ref": tags.get("ref"),
                    "reason": "missing endpoints or usable way geometry",
                }
            )
            continue

        ref = _clean(tags.get("ref")) or str(relation.get("id"))
        route_id = _id(feed_id, str(relation.get("id")), ref)
        route_rows.append(
            {
                "route_id": route_id,
                "agency_id": agency_id,
                "route_short_name": ref,
                "route_long_name": _clean(tags.get("name")) or f"{origin} - {destination}",
                "route_type": "3",
            }
        )
        forward_shape_points += len(shape)

        endpoint_stops = [
            {
                "stop_id": _id(route_id, "from"),
                "stop_name": origin,
                "stop_lat": f"{shape[0][1]:.7f}",
                "stop_lon": f"{shape[0][0]:.7f}",
            },
            {
                "stop_id": _id(route_id, "to"),
                "stop_name": destination,
                "stop_lat": f"{shape[-1][1]:.7f}",
                "stop_lon": f"{shape[-1][0]:.7f}",
            },
        ]
        stop_rows.extend(endpoint_stops)

        for direction_id, direction_shape in enumerate((shape, list(reversed(shape)))):
            trip_id = f"{route_id}_{direction_id}"
            shape_id = f"{route_id}_{direction_id}"
            direction_stops = endpoint_stops if direction_id == 0 else list(reversed(endpoint_stops))
            trip_rows.append(
                {
                    "route_id": route_id,
                    "service_id": "daily",
                    "trip_id": trip_id,
                    "trip_headsign": direction_stops[-1]["stop_name"],
                    "direction_id": str(direction_id),
                    "shape_id": shape_id,
                }
            )
            for stop_idx, stop in enumerate(direction_stops, 1):
                elapsed = (stop_idx - 1) * 45
                stop_time_rows.append(
                    {
                        "trip_id": trip_id,
                        "arrival_time": _time(elapsed),
                        "departure_time": _time(elapsed),
                        "stop_id": stop["stop_id"],
                        "stop_sequence": str(stop_idx),
                    }
                )
            for shape_idx, (lon, lat) in enumerate(direction_shape, 1):
                shape_rows.append(
                    {
                        "shape_id": shape_id,
                        "shape_pt_lat": f"{lat:.7f}",
                        "shape_pt_lon": f"{lon:.7f}",
                        "shape_pt_sequence": str(shape_idx),
                    }
                )
            frequency_rows.append(
                {
                    "trip_id": trip_id,
                    "start_time": "05:00:00",
                    "end_time": "23:00:00",
                    "headway_secs": "900",
                    "exact_times": "0",
                }
            )

    documents = {
        "agency.txt": _csv_text(
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            [
                {
                    "agency_id": agency_id,
                    "agency_name": agency_name,
                    "agency_url": source_url,
                    "agency_timezone": "Asia/Kolkata",
                }
            ],
        ),
        "stops.txt": _csv_text(["stop_id", "stop_name", "stop_lat", "stop_lon"], stop_rows),
        "routes.txt": _csv_text(["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"], route_rows),
        "calendar.txt": _csv_text(
            ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"],
            [
                {
                    "service_id": "daily",
                    "monday": "1",
                    "tuesday": "1",
                    "wednesday": "1",
                    "thursday": "1",
                    "friday": "1",
                    "saturday": "1",
                    "sunday": "1",
                    "start_date": "20260704",
                    "end_date": "20271231",
                }
            ],
        ),
        "trips.txt": _csv_text(["route_id", "service_id", "trip_id", "trip_headsign", "direction_id", "shape_id"], trip_rows),
        "stop_times.txt": _csv_text(["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"], stop_time_rows),
        "frequencies.txt": _csv_text(["trip_id", "start_time", "end_time", "headway_secs", "exact_times"], frequency_rows),
        "shapes.txt": _csv_text(["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"], shape_rows),
        "feed_info.txt": _csv_text(
            ["feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_start_date", "feed_end_date", "feed_version"],
            [
                {
                    "feed_publisher_name": f"{agency_name} OSM fallback construction",
                    "feed_publisher_url": source_url,
                    "feed_lang": "en",
                    "feed_start_date": "20260704",
                    "feed_end_date": "20271231",
                    "feed_version": generated_at,
                }
            ],
        ),
    }
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, text in documents.items():
            zf.writestr(name, text)

    counts = {
        "source_routes": len(relations),
        "routes": len(route_rows),
        "stops": len(stop_rows),
        "trips": len(trip_rows),
        "stop_times": len(stop_time_rows),
        "shape_points": forward_shape_points,
        "shape_rows": len(shape_rows),
        "skipped_routes": len(skipped),
    }
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(
        json.dumps(
            {
                "schema": "sevent4.osm_bus_route_gtfs.sources.v1",
                "status": provenance_status,
                "feed_id": feed_id,
                "network": network,
                "operator_filter": operator,
                "agency": agency_name,
                "generated_at": generated_at,
                "source_url": source_url,
                "source_json": str(source_json),
                "gtfs_zip": str(out_zip),
                "counts": counts,
                "skipped_routes": skipped,
                "note": "Fallback static GTFS constructed from OSM bus route relations. Endpoint stops come from relation from/to tags and relation way endpoints; this is not an agency-published GTFS feed.",
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return counts


def _matches_relation(element: dict[str, Any], network: str, operator: str) -> bool:
    if element.get("type") != "relation":
        return False
    tags = element.get("tags") or {}
    if tags.get("type") != "route" or tags.get("route") != "bus":
        return False
    if network and tags.get("network") != network:
        return False
    if operator and tags.get("operator") != operator:
        return False
    return bool(network or operator)


def _relation_shape(relation: dict[str, Any], ways: dict[int, dict[str, Any]], nodes: dict[int, dict[str, Any]]) -> list[tuple[float, float]]:
    shape: list[tuple[float, float]] = []
    for member in relation.get("members") or []:
        if member.get("type") != "way":
            continue
        way = ways.get(member.get("ref"))
        if not way:
            continue
        coords = _way_coords(way, nodes)
        if not coords:
            continue
        if shape:
            coords = _orient_to_previous(shape[-1], coords)
        for coord in coords:
            if not shape or shape[-1] != coord:
                shape.append(coord)
    return shape


def _way_coords(way: dict[str, Any], nodes: dict[int, dict[str, Any]]) -> list[tuple[float, float]]:
    if way.get("geometry"):
        return [(float(point["lon"]), float(point["lat"])) for point in way.get("geometry") or [] if "lon" in point and "lat" in point]
    coords = []
    for node_id in way.get("nodes") or []:
        node = nodes.get(node_id)
        if node and "lon" in node and "lat" in node:
            coords.append((float(node["lon"]), float(node["lat"])))
    return coords


def _orient_to_previous(previous: tuple[float, float], coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if _distance(previous, coords[-1]) < _distance(previous, coords[0]):
        return list(reversed(coords))
    return coords


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _csv_text(fields: list[str], rows: list[dict[str, Any]]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return out.getvalue()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _id(*parts: str) -> str:
    value = "_".join(_clean(part) for part in parts if _clean(part))
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()


def _time(minutes: int) -> str:
    hour = 5 + minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}:00"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-json", type=Path, required=True)
    parser.add_argument("--out-zip", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--feed-id", required=True)
    parser.add_argument("--agency-id", required=True)
    parser.add_argument("--agency-name", required=True)
    parser.add_argument("--network", required=True)
    parser.add_argument("--operator", default="")
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--provenance-status", default="osm_fallback_constructed")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = build_osm_bus_route_gtfs(
        source_json=args.source_json,
        out_zip=args.out_zip,
        provenance_path=args.provenance,
        feed_id=args.feed_id,
        agency_id=args.agency_id,
        agency_name=args.agency_name,
        network=args.network,
        generated_at=args.generated_at,
        source_url=args.source_url,
        provenance_status=args.provenance_status,
        operator=args.operator,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
