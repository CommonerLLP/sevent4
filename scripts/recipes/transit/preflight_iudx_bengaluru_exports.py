#!/usr/bin/env python3
"""Preflight approved Bengaluru IUDX export folders before building GTFS."""
from __future__ import annotations

import argparse
import json
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.recipes.transit.build_bmrcl_iudx_gtfs_from_exports import (
    REQUIRED_INPUT_FILES as BMRCL_REQUIRED_INPUT_FILES,
    build_bmrcl_gtfs_tables,
    summarize_bmrcl_quality,
)
from sevent4.transit.iudx_gtfs_export import (
    REQUIRED_GTFS_FILES,
    load_iudx_json_rows,
    load_static_gtfs_tables_from_json_dir,
    summarize_static_gtfs_quality,
)

BMTC_REQUIRED_FIELDS_BY_INPUT_FILE = {
    "agency.json": ["agency_id", "agency_name", "agency_url", "agency_timezone"],
    "calendar.json": [
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
    "routes.json": ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"],
    "stops.json": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "trips.json": ["route_id", "service_id", "trip_id"],
    "stop_times.json": ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
}

BMRCL_REQUIRED_FIELDS_BY_INPUT_FILE = {
    "stations.json": ["stop_code", "stop_name", "location"],
    "lines.json": ["route_id", "route_short_name", "route_long_name", "routeStopSequence", "location"],
    "schedule.json": ["stationCode", "arrival_time", "departure_time", "train_id", "route_id"],
}

BMTC_FIELD_VALIDATORS: dict[str, dict[str, Callable[[Any], bool]]] = {
    "agency.json": {
        "agency_url": lambda value: isinstance(value, str) and value.startswith(("http://", "https://")),
    },
    "calendar.json": {
        "monday": lambda value: str(value) in {"0", "1"},
        "tuesday": lambda value: str(value) in {"0", "1"},
        "wednesday": lambda value: str(value) in {"0", "1"},
        "thursday": lambda value: str(value) in {"0", "1"},
        "friday": lambda value: str(value) in {"0", "1"},
        "saturday": lambda value: str(value) in {"0", "1"},
        "sunday": lambda value: str(value) in {"0", "1"},
        "start_date": lambda value: _is_yyyymmdd(value),
        "end_date": lambda value: _is_yyyymmdd(value),
    },
    "routes.json": {
        "route_type": lambda value: _is_int_in_range(value, 0, 7),
    },
    "stops.json": {
        "stop_lat": lambda value: _is_float_in_range(value, -90, 90),
        "stop_lon": lambda value: _is_float_in_range(value, -180, 180),
    },
    "stop_times.json": {
        "arrival_time": lambda value: _is_gtfs_time(value),
        "departure_time": lambda value: _is_gtfs_time(value),
        "stop_sequence": lambda value: _is_positive_int(value),
    },
}

BMRCL_FIELD_VALIDATORS: dict[str, dict[str, Callable[[Any], bool]]] = {
    "stations.json": {
        "location": lambda value: _is_geojson_location(value),
    },
    "lines.json": {
        "location": lambda value: _is_geojson_location(value),
        "routeStopSequence": lambda value: isinstance(value, list) and len(value) >= 2,
    },
    "schedule.json": {
        "arrival_time": lambda value: _is_gtfs_time(value),
        "departure_time": lambda value: _is_gtfs_time(value),
    },
}


def preflight_bmtc_export_dir(input_dir: str | Path) -> dict[str, Any]:
    required_input_files = [filename.replace(".txt", ".json") for filename in REQUIRED_GTFS_FILES]
    present_input_files, missing_input_files = _input_file_status(input_dir, required_input_files)
    row_counts: dict[str, int] = {}
    quality_checks: dict[str, object] = {}
    input_errors: list[dict[str, str]] = []
    empty_input_files: list[str] = []
    missing_required_fields: list[dict[str, object]] = []
    invalid_field_values: list[dict[str, object]] = []
    remaining_gates = []
    if missing_input_files:
        remaining_gates.append("missing_input_files")
        if "stop_times.json" in missing_input_files:
            remaining_gates.append("stop_times_or_equivalent_stop_sequence")
    else:
        try:
            tables = load_static_gtfs_tables_from_json_dir(input_dir)
        except (json.JSONDecodeError, ValueError) as exc:
            input_errors.append(_input_error(exc, input_dir=input_dir))
            remaining_gates.append("invalid_input_json")
        else:
            row_counts = {filename: len(rows) for filename, rows in tables.items()}
            rows_by_input_file = {
                filename.replace(".txt", ".json"): rows
                for filename, rows in tables.items()
            }
            missing_required_fields = _missing_required_fields(
                rows_by_input_file,
                BMTC_REQUIRED_FIELDS_BY_INPUT_FILE,
            )
            invalid_field_values = _invalid_field_values(
                rows_by_input_file,
                BMTC_FIELD_VALIDATORS,
            )
            quality_checks = summarize_static_gtfs_quality(tables)
            empty_input_files = [filename.replace(".txt", ".json") for filename, rows in tables.items() if not rows]
            if empty_input_files:
                remaining_gates.append("empty_input_files")
            if missing_required_fields:
                remaining_gates.append("missing_required_fields")
            if invalid_field_values:
                remaining_gates.append("invalid_field_values")
            if not quality_checks.get("route_geometry_ready"):
                remaining_gates.append("stop_times_or_equivalent_stop_sequence")
    return {
        "feed_id": "bengaluru_bmtc_iudx_full_gtfs",
        "input_dir": str(input_dir),
        "required_input_files": required_input_files,
        "present_input_files": present_input_files,
        "missing_input_files": missing_input_files,
        "empty_input_files": empty_input_files,
        "missing_required_fields": missing_required_fields,
        "invalid_field_values": invalid_field_values,
        "input_errors": input_errors,
        "row_counts": row_counts,
        "quality_checks": quality_checks,
        "ready_to_build": not remaining_gates,
        "remaining_gates": remaining_gates,
    }


def preflight_bmrcl_export_dir(
    input_dir: str | Path,
    *,
    generated_at: str,
) -> dict[str, Any]:
    present_input_files, missing_input_files = _input_file_status(input_dir, BMRCL_REQUIRED_INPUT_FILES)
    row_counts: dict[str, int] = {}
    quality_checks: dict[str, object] = {}
    input_errors: list[dict[str, str]] = []
    empty_input_files: list[str] = []
    missing_required_fields: list[dict[str, object]] = []
    invalid_field_values: list[dict[str, object]] = []
    remaining_gates = []
    if missing_input_files:
        remaining_gates.append("missing_input_files")
    else:
        base = Path(input_dir)
        try:
            source_rows = {
                "stations.json": load_iudx_json_rows(base / "stations.json"),
                "lines.json": load_iudx_json_rows(base / "lines.json"),
                "schedule.json": load_iudx_json_rows(base / "schedule.json"),
            }
            empty_input_files = sorted(filename for filename, rows in source_rows.items() if not rows)
            missing_required_fields = _missing_required_fields(
                source_rows,
                BMRCL_REQUIRED_FIELDS_BY_INPUT_FILE,
            )
            invalid_field_values = _invalid_field_values(
                source_rows,
                BMRCL_FIELD_VALIDATORS,
            )
            tables = {}
            if not empty_input_files and not missing_required_fields and not invalid_field_values:
                tables = build_bmrcl_gtfs_tables(
                    stations=source_rows["stations.json"],
                    lines=source_rows["lines.json"],
                    schedule=source_rows["schedule.json"],
                    generated_at=generated_at,
                )
        except (json.JSONDecodeError, ValueError) as exc:
            input_errors.append(_input_error(exc, input_dir=input_dir))
            remaining_gates.append("invalid_input_json")
        else:
            if tables:
                row_counts = {filename: len(rows) for filename, rows in tables.items()}
                quality_checks = summarize_bmrcl_quality(tables)
                source_file_by_empty_table = {
                    "stops.txt": "stations.json",
                    "routes.txt": "lines.json",
                    "trips.txt": "schedule.json",
                    "stop_times.txt": "schedule.json",
                }
                empty_input_files = sorted(
                    {
                        source_file
                        for table, source_file in source_file_by_empty_table.items()
                        if not tables.get(table)
                    }
                )
            if empty_input_files:
                remaining_gates.append("empty_input_files")
            if missing_required_fields:
                remaining_gates.append("missing_required_fields")
            if invalid_field_values:
                remaining_gates.append("invalid_field_values")
            if quality_checks.get("missing_scheduled_operational_route_short_names"):
                remaining_gates.append("purple_green_yellow_scheduled_two_stop_trips")
            elif not quality_checks.get("route_geometry_ready"):
                if quality_checks:
                    remaining_gates.append("route_geometry_ready")
    return {
        "feed_id": "bengaluru_bmrcl_iudx_full_network_schedule",
        "input_dir": str(input_dir),
        "required_input_files": list(BMRCL_REQUIRED_INPUT_FILES),
        "present_input_files": present_input_files,
        "missing_input_files": missing_input_files,
        "empty_input_files": empty_input_files,
        "missing_required_fields": missing_required_fields,
        "invalid_field_values": invalid_field_values,
        "input_errors": input_errors,
        "row_counts": row_counts,
        "quality_checks": quality_checks,
        "ready_to_build": not remaining_gates,
        "remaining_gates": remaining_gates,
    }


def _input_file_status(input_dir: str | Path, required_input_files: list[str]) -> tuple[list[str], list[str]]:
    base = Path(input_dir)
    present_input_files = [filename for filename in required_input_files if (base / filename).exists()]
    missing_input_files = [filename for filename in required_input_files if filename not in present_input_files]
    return present_input_files, missing_input_files


def _missing_required_fields(
    rows_by_file: dict[str, list[dict[str, Any]]],
    required_fields_by_file: dict[str, list[str]],
) -> list[dict[str, object]]:
    missing_by_file = []
    for filename, required_fields in required_fields_by_file.items():
        rows = rows_by_file.get(filename, [])
        missing_fields = []
        for field in required_fields:
            if any(_field_is_missing(row, field) for row in rows):
                missing_fields.append(field)
        if missing_fields:
            missing_by_file.append({
                "file": filename,
                "missing_fields": missing_fields,
            })
    return missing_by_file


def _invalid_field_values(
    rows_by_file: dict[str, list[dict[str, Any]]],
    validators_by_file: dict[str, dict[str, Callable[[Any], bool]]],
) -> list[dict[str, object]]:
    invalid_by_file = []
    for filename, validators in validators_by_file.items():
        rows = rows_by_file.get(filename, [])
        invalid_fields = []
        for field, validator in validators.items():
            if any(not _field_is_missing(row, field) and not validator(row.get(field)) for row in rows):
                invalid_fields.append(field)
        if invalid_fields:
            invalid_by_file.append({
                "file": filename,
                "invalid_fields": invalid_fields,
            })
    return invalid_by_file


def _field_is_missing(row: dict[str, Any], field: str) -> bool:
    value = row.get(field)
    return value is None or value == ""


def _is_yyyymmdd(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{8}", value):
        return False
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError:
        return False
    return True


def _is_gtfs_time(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    match = re.fullmatch(r"(\d{1,2}):(\d{2}):(\d{2})", value)
    if not match:
        return False
    _hour, minute, second = (int(part) for part in match.groups())
    return minute < 60 and second < 60


def _is_int_in_range(value: Any, minimum: int, maximum: int) -> bool:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return False
    return minimum <= parsed <= maximum


def _is_positive_int(value: Any) -> bool:
    try:
        return int(str(value)) > 0
    except (TypeError, ValueError):
        return False


def _is_float_in_range(value: Any, minimum: float, maximum: float) -> bool:
    try:
        parsed = float(str(value))
    except (TypeError, ValueError):
        return False
    return minimum <= parsed <= maximum


def _is_geojson_location(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return _coordinates_are_valid(value.get("coordinates"))


def _coordinates_are_valid(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    if len(value) == 2 and not any(isinstance(item, list) for item in value):
        return _is_float_in_range(value[0], -180, 180) and _is_float_in_range(value[1], -90, 90)
    return bool(value) and all(_coordinates_are_valid(item) for item in value)


def _input_error(exc: Exception, *, input_dir: str | Path) -> dict[str, str]:
    filename = ""
    message = str(exc)
    base = Path(input_dir)
    for path in sorted(base.glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            filename = path.name
            break
    return {
        "file": filename,
        "error": message,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Preflight approved Bengaluru IUDX export folders.")
    parser.add_argument("--bmtc-input-dir", type=Path)
    parser.add_argument("--bmrcl-input-dir", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any requested feed is not ready to build.")
    args = parser.parse_args()

    generated_at = args.generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    results = {
        "schema": "sevent4.bengaluru_iudx_export_preflight.v1",
        "generated_at": generated_at,
        "feeds": [],
    }
    if args.bmtc_input_dir is not None:
        results["feeds"].append(preflight_bmtc_export_dir(args.bmtc_input_dir))
    if args.bmrcl_input_dir is not None:
        results["feeds"].append(preflight_bmrcl_export_dir(args.bmrcl_input_dir, generated_at=generated_at))
    text = json.dumps(results, ensure_ascii=False, indent=1) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.strict and any(not feed.get("ready_to_build") for feed in results["feeds"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
