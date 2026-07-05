#!/usr/bin/env python3
"""Build a BMRCL static GTFS zip from approved IUDX network and schedule exports."""
from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from sevent4.transit.iudx_gtfs_export import load_iudx_json_rows, summarize_static_gtfs_quality


OPERATIONAL_ROUTE_SHORT_NAMES = ["Purple Line", "Green Line", "Yellow Line"]
REQUIRED_INPUT_FILES = ["stations.json", "lines.json", "schedule.json"]
GTFS_FIELD_ORDER = {
    "agency.txt": ["agency_id", "agency_name", "agency_url", "agency_timezone"],
    "calendar.txt": [
        "service_id",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "start_date",
        "end_date",
    ],
    "routes.txt": ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"],
    "stops.txt": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "trips.txt": ["route_id", "service_id", "trip_id", "trip_headsign", "shape_id"],
    "stop_times.txt": ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
    "shapes.txt": ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
    "feed_info.txt": ["feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_version"],
}


def build_bmrcl_iudx_gtfs_from_exports(
    *,
    input_dir: str | Path,
    out_zip: str | Path,
    provenance_path: str | Path,
    manifest_row_path: str | Path | None = None,
    feed_manifest_path: str | Path | None = None,
    generated_at: str,
) -> dict[str, Any]:
    base = Path(input_dir)
    stations = load_iudx_json_rows(base / "stations.json")
    lines = load_iudx_json_rows(base / "lines.json")
    schedule = load_iudx_json_rows(base / "schedule.json")
    tables = build_bmrcl_gtfs_tables(stations=stations, lines=lines, schedule=schedule, generated_at=generated_at)
    row_counts = write_bmrcl_gtfs_zip(tables, out_zip)
    quality_checks = summarize_bmrcl_quality(tables)
    provenance = {
        "schema": "sevent4.bengaluru_bmrcl_iudx_gtfs_export.sources.v1",
        "feed_id": "bengaluru_bmrcl_iudx_full_network_schedule",
        "status": "iudx_policy_approved_export",
        "generated_at": generated_at,
        "input_dir": str(input_dir),
        "gtfs_zip": str(out_zip),
        "required_input_files": REQUIRED_INPUT_FILES,
        "row_counts": row_counts,
        "quality_checks": quality_checks,
        "notes": (
            "Static GTFS built from approved BMRCL IUDX station, line, and schedule exports. "
            "The coverage row must stay gated unless Purple, Green, and Yellow are present."
        ),
    }
    _write_json(provenance_path, provenance)
    if manifest_row_path is not None:
        _write_json(manifest_row_path, build_bmrcl_iudx_manifest_feed_row(provenance))
    if feed_manifest_path is not None:
        _write_json(
            feed_manifest_path,
            {
                "schema": "sevent4.multimodal_transit.manifest.v1",
                "feeds": [build_bmrcl_iudx_manifest_feed_row(provenance)],
            },
        )
    return provenance


def build_bmrcl_gtfs_tables(
    *,
    stations: list[dict[str, object]],
    lines: list[dict[str, object]],
    schedule: list[dict[str, object]],
    generated_at: str,
) -> dict[str, list[dict[str, object]]]:
    agency_id = "BMRCL"
    service_id = "approved_daily"
    stops = _build_stops(stations)
    stops_by_id = {str(row["stop_id"]): row for row in stops}
    routes, shapes, sequence_by_route, route_name_by_id = _build_routes_and_shapes(lines, agency_id)
    trips, stop_times = _build_trips_and_stop_times(
        schedule,
        service_id=service_id,
        stops_by_id=stops_by_id,
        sequence_by_route=sequence_by_route,
        route_name_by_id=route_name_by_id,
    )
    return {
        "agency.txt": [
            {
                "agency_id": agency_id,
                "agency_name": "Bangalore Metro Rail Corporation Limited",
                "agency_url": "https://english.bmrc.co.in/",
                "agency_timezone": "Asia/Kolkata",
            }
        ],
        "calendar.txt": [
            {
                "service_id": service_id,
                "monday": "1",
                "tuesday": "1",
                "wednesday": "1",
                "thursday": "1",
                "friday": "1",
                "saturday": "1",
                "sunday": "1",
                "start_date": "20260705",
                "end_date": "20271231",
            }
        ],
        "routes.txt": routes,
        "stops.txt": stops,
        "trips.txt": trips,
        "stop_times.txt": stop_times,
        "shapes.txt": shapes,
        "feed_info.txt": [
            {
                "feed_publisher_name": "BMRCL IUDX policy-approved export",
                "feed_publisher_url": "https://catalogue.iudx.org.in/bengaluru",
                "feed_lang": "en",
                "feed_version": generated_at,
            }
        ],
    }


def write_bmrcl_gtfs_zip(
    tables: dict[str, list[dict[str, object]]],
    out_zip: str | Path,
) -> dict[str, int]:
    required = ["agency.txt", "calendar.txt", "routes.txt", "stops.txt", "trips.txt", "stop_times.txt"]
    missing = [filename for filename in required if filename not in tables]
    if missing:
        raise ValueError(f"missing required GTFS files: {', '.join(missing)}")
    empty = [filename for filename in required if not tables.get(filename)]
    if empty:
        raise ValueError(f"empty required GTFS files: {', '.join(empty)}")
    quality = summarize_static_gtfs_quality({filename: tables[filename] for filename in required})
    if not quality["route_geometry_ready"]:
        raise ValueError("BMRCL schedule export must contain at least one trip with two stops")

    out_path = Path(out_zip)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename in [*required, "shapes.txt", "feed_info.txt"]:
            rows = tables.get(filename, [])
            if rows:
                zf.writestr(filename, _csv_text(_ordered_fields(filename, rows), rows))
    return {filename: len(rows) for filename, rows in tables.items()}


def summarize_bmrcl_quality(tables: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    required = ["agency.txt", "calendar.txt", "routes.txt", "stops.txt", "trips.txt", "stop_times.txt"]
    quality = summarize_static_gtfs_quality({filename: tables.get(filename, []) for filename in required})
    routes = tables.get("routes.txt", [])
    route_short_names = [str(row.get("route_short_name", "")).strip() for row in routes]
    route_short_names = [name for name in route_short_names if name]
    route_short_name_by_id = {str(row.get("route_id", "")).strip(): str(row.get("route_short_name", "")).strip() for row in routes}
    route_id_by_trip_id = {
        str(row.get("trip_id", "")).strip(): str(row.get("route_id", "")).strip()
        for row in tables.get("trips.txt", [])
        if str(row.get("trip_id", "")).strip() and str(row.get("route_id", "")).strip()
    }
    stops_by_trip_id: dict[str, set[str]] = defaultdict(set)
    for row in tables.get("stop_times.txt", []):
        trip_id = str(row.get("trip_id", "")).strip()
        stop_id = str(row.get("stop_id", "")).strip()
        if trip_id and stop_id:
            stops_by_trip_id[trip_id].add(stop_id)
    scheduled_route_ids = {
        route_id_by_trip_id[trip_id]
        for trip_id, stop_ids in stops_by_trip_id.items()
        if len(stop_ids) >= 2 and trip_id in route_id_by_trip_id
    }
    scheduled_operational = [
        route_short_name_by_id[route_id]
        for route_id in route_short_name_by_id
        if route_id in scheduled_route_ids and route_short_name_by_id[route_id] in OPERATIONAL_ROUTE_SHORT_NAMES
    ]
    missing_operational = [name for name in OPERATIONAL_ROUTE_SHORT_NAMES if name not in route_short_names]
    missing_scheduled_operational = [name for name in OPERATIONAL_ROUTE_SHORT_NAMES if name not in scheduled_operational]
    quality["route_short_names"] = route_short_names
    quality["missing_operational_route_short_names"] = missing_operational
    quality["scheduled_operational_route_short_names"] = scheduled_operational
    quality["missing_scheduled_operational_route_short_names"] = missing_scheduled_operational
    quality["coverage_complete"] = not missing_operational and not missing_scheduled_operational
    quality["route_geometry_ready"] = bool(
        quality["route_geometry_ready"] and not missing_operational and not missing_scheduled_operational
    )
    return quality


def build_bmrcl_iudx_manifest_feed_row(provenance: dict[str, Any]) -> dict[str, Any]:
    quality_checks = provenance.get("quality_checks", {})
    missing = []
    if isinstance(quality_checks, dict):
        missing = [
            *quality_checks.get("missing_operational_route_short_names", []),
            *quality_checks.get("missing_scheduled_operational_route_short_names", []),
        ]
    if not isinstance(quality_checks, dict) or not quality_checks.get("route_geometry_ready") or missing:
        detail = f"; missing {', '.join(missing)}" if missing else ""
        raise ValueError(f"BMRCL IUDX provenance quality_checks.route_geometry_ready must be true{detail}")
    return {
        "feed_id": "bengaluru_bmrcl_iudx_full_network_schedule",
        "city": "bengaluru",
        "mode": "metro",
        "operator": "Bangalore Metro Rail Corporation Limited",
        "status": "ok",
        "source_url": "https://catalogue.iudx.org.in/bengaluru",
        "license": "IUDX policy-approved BMRCL network and schedule export.",
        "path": str(provenance["gtfs_zip"]),
        "stop_layer": "metro_gtfs_stops",
        "route_layer": "metro_gtfs_routes",
        "stop_features": int(quality_checks.get("stop_count", 0)),
        "route_features": int(quality_checks.get("route_count", 0)),
        "coverage_scope": {
            "coverage_complete": quality_checks.get("coverage_complete"),
            "expected_operational_route_short_names": OPERATIONAL_ROUTE_SHORT_NAMES,
            "route_short_names": quality_checks.get("route_short_names", []),
            "missing_operational_route_short_names": quality_checks.get("missing_operational_route_short_names", []),
            "scheduled_operational_route_short_names": quality_checks.get("scheduled_operational_route_short_names", []),
            "missing_scheduled_operational_route_short_names": quality_checks.get(
                "missing_scheduled_operational_route_short_names", []
            ),
        },
        "quality_checks": quality_checks,
        "notes": (
            "Replace the gated BMRCL IUDX row only after this exported GTFS has "
            "been converted into public stop and route layers."
        ),
    }


def _build_stops(stations: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    stops = []
    seen = set()
    for row in stations:
        stop_id = str(row.get("stop_code") or row.get("stationCode") or row.get("stop_id") or "").strip()
        coordinates = _coordinates(row.get("location"))
        if not stop_id or len(coordinates) != 2 or stop_id in seen:
            continue
        seen.add(stop_id)
        stops.append(
            {
                "stop_id": stop_id,
                "stop_name": str(row.get("stop_name", stop_id)).strip() or stop_id,
                "stop_lat": f"{float(coordinates[1]):.7f}",
                "stop_lon": f"{float(coordinates[0]):.7f}",
            }
        )
    return stops


def _build_routes_and_shapes(
    lines: Iterable[dict[str, object]],
    agency_id: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, list[str]], dict[str, str]]:
    routes = []
    shapes = []
    sequence_by_route: dict[str, list[str]] = {}
    route_name_by_id = {}
    for row in lines:
        route_id = str(row.get("route_id", "")).strip()
        if not route_id:
            continue
        route_short_name = str(row.get("route_short_name", route_id)).strip() or route_id
        route_long_name = str(row.get("route_long_name", route_id)).strip() or route_id
        routes.append(
            {
                "route_id": route_id,
                "agency_id": agency_id,
                "route_short_name": route_short_name,
                "route_long_name": route_long_name,
                "route_type": "1",
            }
        )
        route_name_by_id[route_id] = route_long_name
        sequence = row.get("routeStopSequence") or []
        if isinstance(sequence, list):
            sequence_by_route[route_id] = [str(stop_id).strip() for stop_id in sequence if str(stop_id).strip()]
        shape_id = f"{route_id}_shape"
        for idx, coordinate in enumerate(_line_coordinates(row.get("location")), start=1):
            shapes.append(
                {
                    "shape_id": shape_id,
                    "shape_pt_lat": f"{float(coordinate[1]):.7f}",
                    "shape_pt_lon": f"{float(coordinate[0]):.7f}",
                    "shape_pt_sequence": str(idx),
                }
            )
    return routes, shapes, sequence_by_route, route_name_by_id


def _build_trips_and_stop_times(
    schedule: Iterable[dict[str, object]],
    *,
    service_id: str,
    stops_by_id: dict[str, dict[str, object]],
    sequence_by_route: dict[str, list[str]],
    route_name_by_id: dict[str, str],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in schedule:
        route_id = str(row.get("route_id", "")).strip()
        train_id = str(row.get("train_id", "")).strip()
        station_code = str(row.get("stationCode") or row.get("stop_id") or row.get("stop_code") or "").strip()
        if route_id and train_id and station_code in stops_by_id:
            grouped[(route_id, train_id)].append(row)

    trips = []
    stop_times = []
    for (route_id, train_id), rows in sorted(grouped.items()):
        sequence_index = {stop_id: idx for idx, stop_id in enumerate(sequence_by_route.get(route_id, []))}
        ordered = sorted(
            rows,
            key=lambda row: (
                sequence_index.get(str(row.get("stationCode") or row.get("stop_id") or row.get("stop_code") or "").strip(), 99999),
                str(row.get("arrival_time", "")),
            ),
        )
        trip_id = f"{route_id}_{train_id}".replace(" ", "_")
        trips.append(
            {
                "route_id": route_id,
                "service_id": service_id,
                "trip_id": trip_id,
                "trip_headsign": route_name_by_id.get(route_id, route_id),
                "shape_id": f"{route_id}_shape",
            }
        )
        for idx, row in enumerate(ordered, start=1):
            station_code = str(row.get("stationCode") or row.get("stop_id") or row.get("stop_code") or "").strip()
            stop_times.append(
                {
                    "trip_id": trip_id,
                    "arrival_time": str(row.get("arrival_time", "")),
                    "departure_time": str(row.get("departure_time", row.get("arrival_time", ""))),
                    "stop_id": station_code,
                    "stop_sequence": str(idx),
                }
            )
    return trips, stop_times


def _coordinates(value: object) -> list[object]:
    if isinstance(value, dict) and isinstance(value.get("coordinates"), list):
        return value["coordinates"]
    return []


def _line_coordinates(value: object) -> list[list[object]]:
    coordinates = _coordinates(value)
    return [coordinate for coordinate in coordinates if isinstance(coordinate, list | tuple) and len(coordinate) == 2]


def _ordered_fields(filename: str, rows: Iterable[dict[str, object]]) -> list[str]:
    seen = {field for row in rows for field in row}
    ordered = [field for field in GTFS_FIELD_ORDER.get(filename, []) if field in seen]
    return ordered + sorted(seen - set(ordered))


def _csv_text(fields: list[str], rows: list[dict[str, object]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: "" if row.get(field) is None else row.get(field, "") for field in fields})
    return buffer.getvalue()


def _write_json(path: str | Path, document: dict[str, Any]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build BMRCL GTFS from approved IUDX JSON exports.")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--out-zip", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--manifest-row", type=Path)
    parser.add_argument("--feed-manifest", type=Path)
    parser.add_argument("--generated-at")
    args = parser.parse_args()

    generated_at = args.generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    result = build_bmrcl_iudx_gtfs_from_exports(
        input_dir=args.input_dir,
        out_zip=args.out_zip,
        provenance_path=args.provenance,
        manifest_row_path=args.manifest_row,
        feed_manifest_path=args.feed_manifest,
        generated_at=generated_at,
    )
    print(json.dumps({"gtfs_zip": result["gtfs_zip"], "row_counts": result["row_counts"]}, indent=1))


if __name__ == "__main__":
    main()
