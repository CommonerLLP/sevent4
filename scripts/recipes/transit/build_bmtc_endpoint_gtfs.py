#!/usr/bin/env python3
"""Build endpoint-shaped BMTC static GTFS from BMTC route names + stop coordinates."""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_URL = "https://mybmtc.karnataka.gov.in/"


def build_bmtc_endpoint_gtfs(
    *,
    source_zip: Path,
    out_zip: Path,
    provenance_path: Path,
    generated_at: str,
    source_url: str = DEFAULT_SOURCE_URL,
) -> dict[str, int]:
    with zipfile.ZipFile(source_zip) as zf:
        stops = _read_zip_csv(zf, "stops.txt")
        source_routes = _read_zip_csv(zf, "routes.txt")

    lookup = _StopLookup(stops)
    used_stops: dict[str, dict[str, str]] = {}
    route_rows = []
    trip_rows = []
    stop_time_rows = []
    frequency_rows = []
    shape_rows = []
    skipped = []

    for route in source_routes:
        endpoints = _route_endpoints(route.get("route_long_name", ""))
        if endpoints is None:
            skipped.append({"route_id": route.get("route_id", ""), "reason": "route_long_name_has_no_endpoint_separator"})
            continue
        origin_name, destination_name = endpoints
        origin = lookup.match(origin_name)
        destination = lookup.match(destination_name)
        if origin is None or destination is None:
            skipped.append(
                {
                    "route_id": route.get("route_id", ""),
                    "reason": "endpoint_stop_not_matched",
                    "origin": origin_name,
                    "destination": destination_name,
                }
            )
            continue
        if origin.get("stop_id") == destination.get("stop_id"):
            skipped.append(
                {
                    "route_id": route.get("route_id", ""),
                    "reason": "same_endpoint_stop",
                    "origin": origin_name,
                    "destination": destination_name,
                }
            )
            continue

        route_id = route["route_id"]
        route_rows.append(
            {
                "route_id": route_id,
                "agency_id": route.get("agency_id") or "BMTC",
                "route_short_name": route_id,
                "route_long_name": route.get("route_long_name", f"{origin_name} - {destination_name}"),
                "route_type": route.get("route_type") or "3",
            }
        )
        for stop in (origin, destination):
            used_stops[stop["stop_id"]] = stop
        for direction_id, direction_stops in enumerate(((origin, destination), (destination, origin))):
            trip_id = f"{_id(route_id)}_{direction_id}"
            shape_id = trip_id
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
            for sequence, stop in enumerate(direction_stops, 1):
                elapsed = (sequence - 1) * 30
                stop_time_rows.append(
                    {
                        "trip_id": trip_id,
                        "arrival_time": _time(elapsed),
                        "departure_time": _time(elapsed),
                        "stop_id": stop["stop_id"],
                        "stop_sequence": str(sequence),
                    }
                )
                shape_rows.append(
                    {
                        "shape_id": shape_id,
                        "shape_pt_lat": _coord(stop, "stop_lat"),
                        "shape_pt_lon": _coord(stop, "stop_lon"),
                        "shape_pt_sequence": str(sequence),
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

    stop_rows = [
        {
            "stop_id": stop["stop_id"],
            "stop_name": stop.get("stop_name", ""),
            "stop_lat": _coord(stop, "stop_lat"),
            "stop_lon": _coord(stop, "stop_lon"),
        }
        for _, stop in sorted(used_stops.items())
    ]
    documents = {
        "agency.txt": _csv_text(
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            [
                {
                    "agency_id": "BMTC",
                    "agency_name": "Bangalore Metropolitan Transport Corporation endpoint construction",
                    "agency_url": DEFAULT_SOURCE_URL,
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
                    "feed_publisher_name": "BMTC endpoint GTFS construction",
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

    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(
        json.dumps(
            {
                "schema": "sevent4.bmtc_endpoint_gtfs.sources.v1",
                "status": "unofficial_constructed",
                "agency": "Bangalore Metropolitan Transport Corporation",
                "generated_at": generated_at,
                "source_url": source_url,
                "source_zip": str(source_zip),
                "gtfs_zip": str(out_zip),
                "counts": {
                    "source_routes": len(source_routes),
                    "routes": len(route_rows),
                    "stops": len(stop_rows),
                    "trips": len(trip_rows),
                    "stop_times": len(stop_time_rows),
                    "skipped_routes": len(skipped),
                },
                "skipped_routes": skipped,
                "note": "Unofficial endpoint-shaped static GTFS constructed from BMTC route_long_name endpoints and BMTC stop coordinates; route geometry is endpoint-to-endpoint, not full stop-by-stop path geometry.",
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "source_routes": len(source_routes),
        "routes": len(route_rows),
        "stops": len(stop_rows),
        "trips": len(trip_rows),
        "stop_times": len(stop_time_rows),
        "skipped_routes": len(skipped),
    }


def _read_zip_csv(zf: zipfile.ZipFile, filename: str) -> list[dict[str, str]]:
    names = {Path(name).name: name for name in zf.namelist()}
    with zf.open(names[filename]) as handle:
        text = io.TextIOWrapper(handle, encoding="utf-8-sig", newline="")
        return list(csv.DictReader(text))


def _route_endpoints(value: str) -> tuple[str, str] | None:
    parts = [part.strip() for part in re.split(r"\s+-\s+", value, maxsplit=1)]
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


class _StopLookup:
    def __init__(self, stops: list[dict[str, str]]) -> None:
        self.stops = [
            (stop, _normalize(stop.get("stop_name", "")), _tokens(stop.get("stop_name", "")))
            for stop in stops
            if stop.get("stop_id") and stop.get("stop_name")
        ]
        self.exact = {}
        for stop, normalized, _ in self.stops:
            self.exact.setdefault(normalized, stop)

    def match(self, raw_name: str) -> dict[str, str] | None:
        normalized = _normalize(raw_name)
        exact = self.exact.get(normalized)
        if exact:
            return exact
        query_tokens = _tokens(raw_name)
        if not query_tokens:
            return None
        best = None
        best_score = 0.0
        for stop, _, stop_tokens in self.stops:
            shared = len(query_tokens & stop_tokens)
            if not shared:
                continue
            score = shared / max(len(query_tokens), len(stop_tokens))
            if score > best_score and (score >= 0.67 or (shared >= 2 and score >= 0.5)):
                best = stop
                best_score = score
        return best


def _normalize(value: str) -> str:
    value = value.casefold().replace("&", " and ")
    replacements = {
        "stn": "station",
        "st.": "street",
        "rd": "road",
        "jn": "junction",
        "jcn": "junction",
    }
    for source, target in replacements.items():
        value = re.sub(rf"\b{re.escape(source)}\b", target, value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _tokens(value: str) -> set[str]:
    ignored = {"bus", "station", "stand", "stop", "road", "circle", "cross", "gate", "market", "main"}
    return {token for token in _normalize(value).split() if len(token) >= 4 and token not in ignored}


def _coord(stop: dict[str, str], field: str) -> str:
    return f"{float(stop[field]):.7f}"


def _id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}:00"


def _csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    handle = io.StringIO()
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return handle.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build endpoint-shaped BMTC GTFS from BMTC route names and stops.")
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out-zip", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    args = parser.parse_args()
    result = build_bmtc_endpoint_gtfs(
        source_zip=args.source_zip,
        out_zip=args.out_zip,
        provenance_path=args.provenance,
        generated_at=args.generated_at,
        source_url=args.source_url,
    )
    print(
        f"wrote BMTC endpoint GTFS: {result['stops']} stops, {result['routes']} routes, "
        f"{result['skipped_routes']} skipped routes"
    )


if __name__ == "__main__":
    main()
