from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path
from typing import Iterable


GTFS_FIELD_ORDER = {
    "agency.txt": ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_phone", "agency_lang"],
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
    "routes.txt": ["route_id", "agency_id", "route_short_name", "route_long_name", "route_desc", "route_type"],
    "stops.txt": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "trips.txt": ["route_id", "service_id", "trip_id"],
    "stop_times.txt": ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
}

REQUIRED_GTFS_FILES = tuple(GTFS_FIELD_ORDER)


def load_static_gtfs_tables_from_json_dir(input_dir: str | Path) -> dict[str, list[dict[str, object]]]:
    base = Path(input_dir)
    tables: dict[str, list[dict[str, object]]] = {}
    for filename in REQUIRED_GTFS_FILES:
        json_path = base / filename.replace(".txt", ".json")
        tables[filename] = load_iudx_json_rows(json_path)
    return tables


def load_iudx_json_rows(path: str | Path) -> list[dict[str, object]]:
    json_path = Path(path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    rows = _rows_from_payload(payload)
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{json_path} must contain row objects")
    return [_flatten_iudx_row(row) for row in rows]


def _rows_from_payload(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]
    raise ValueError("IUDX table export must be a JSON array or an object with a results array")


def _flatten_iudx_row(row: dict[str, object]) -> dict[str, object]:
    flattened: dict[str, object] = {}
    for key, value in row.items():
        if isinstance(value, dict) and set(value) <= {"type", "value"} and "value" in value:
            flattened[key] = value["value"]
        else:
            flattened[key] = value
    return flattened


def write_static_gtfs_zip_from_tables(
    rows_by_file: dict[str, list[dict[str, object]]],
    out_zip: str | Path,
) -> dict[str, int]:
    missing_files = [filename for filename in REQUIRED_GTFS_FILES if filename not in rows_by_file]
    if missing_files:
        raise ValueError(f"missing required GTFS files: {', '.join(missing_files)}")

    empty_files = [filename for filename in REQUIRED_GTFS_FILES if not rows_by_file.get(filename)]
    if empty_files:
        raise ValueError(f"empty required GTFS files: {', '.join(empty_files)}")

    if not _has_two_stop_trip(rows_by_file["stop_times.txt"]):
        raise ValueError("stop_times.txt must contain at least one trip with two stops")

    out_path = Path(out_zip)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename in REQUIRED_GTFS_FILES:
            rows = rows_by_file[filename]
            zf.writestr(filename, _csv_text(_ordered_fields(filename, rows), rows))

    return {filename: len(rows_by_file[filename]) for filename in REQUIRED_GTFS_FILES}


def summarize_static_gtfs_quality(rows_by_file: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    trip_stop_counts = _trip_stop_counts(rows_by_file.get("stop_times.txt", []))
    trips_with_two_or_more_stops = sum(1 for count in trip_stop_counts.values() if count >= 2)
    max_stops_per_trip = max(trip_stop_counts.values(), default=0)
    return {
        "route_geometry_ready": trips_with_two_or_more_stops > 0,
        "stop_count": len(rows_by_file.get("stops.txt", [])),
        "route_count": len(rows_by_file.get("routes.txt", [])),
        "trip_count": len(rows_by_file.get("trips.txt", [])),
        "stop_time_count": len(rows_by_file.get("stop_times.txt", [])),
        "trips_with_two_or_more_stops": trips_with_two_or_more_stops,
        "max_stops_per_trip": max_stops_per_trip,
    }


def _has_two_stop_trip(stop_times: Iterable[dict[str, object]]) -> bool:
    return any(count >= 2 for count in _trip_stop_counts(stop_times).values())


def _trip_stop_counts(stop_times: Iterable[dict[str, object]]) -> dict[str, int]:
    trip_stops: dict[str, set[str]] = {}
    for row in stop_times:
        trip_id = str(row.get("trip_id", "")).strip()
        stop_id = str(row.get("stop_id", "")).strip()
        if not trip_id or not stop_id:
            continue
        stops = trip_stops.setdefault(trip_id, set())
        stops.add(stop_id)
    return {trip_id: len(stops) for trip_id, stops in trip_stops.items()}


def _ordered_fields(filename: str, rows: Iterable[dict[str, object]]) -> list[str]:
    seen_fields = {field for row in rows for field in row}
    ordered = [field for field in GTFS_FIELD_ORDER[filename] if field in seen_fields]
    extras = sorted(seen_fields - set(ordered))
    return ordered + extras


def _csv_text(fields: list[str], rows: list[dict[str, object]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: "" if row.get(field) is None else row.get(field, "") for field in fields})
    return buffer.getvalue()
