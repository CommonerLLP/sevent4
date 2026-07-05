#!/usr/bin/env python3
"""Build unofficial WBTC city-bus static GTFS from WBTC route rows + OSM stops."""
from __future__ import annotations

import argparse
import csv
import html
from html.parser import HTMLParser
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_URL = "https://wbtconline.in/wbtc-city-bus-routes"


def build_wbtc_city_bus_gtfs(
    *,
    source_html: Path,
    osm_stops: Path,
    anchor_points: list[Path] | None = None,
    out_zip: Path,
    provenance_path: Path,
    generated_at: str,
    source_url: str = DEFAULT_SOURCE_URL,
) -> dict[str, int]:
    routes = _parse_wbtc_routes(source_html)
    anchor_points = anchor_points or []
    stop_lookup = _stop_lookup(osm_stops, anchor_points)
    route_rows = []
    trip_rows = []
    stop_time_rows = []
    frequency_rows = []
    shape_rows = []
    used_stops: dict[str, dict[str, Any]] = {}
    skipped = []

    for route in routes:
        sequence, unmatched = _matched_sequence(route, stop_lookup)
        if len(sequence) < 2:
            skipped.append({"route_no": route["route_no"], "unmatched": unmatched})
            continue
        route_id = _id("wbtc", route["route_no"])
        route_rows.append(
            {
                "route_id": route_id,
                "agency_id": "WBTC",
                "route_short_name": route["route_no"],
                "route_long_name": f"{route['origin']} - {route['destination']}",
                "route_type": "3",
            }
        )
        for stop in sequence:
            used_stops[stop["name"]] = stop
        for direction_id, direction_stops in enumerate((sequence, list(reversed(sequence)))):
            trip_id = f"{route_id}_{direction_id}"
            shape_id = f"{route_id}_{direction_id}"
            trip_rows.append(
                {
                    "route_id": route_id,
                    "service_id": "daily",
                    "trip_id": trip_id,
                    "trip_headsign": direction_stops[-1]["name"],
                    "direction_id": str(direction_id),
                    "shape_id": shape_id,
                }
            )
            for idx, stop in enumerate(direction_stops, 1):
                elapsed = (idx - 1) * 5
                stop_time_rows.append(
                    {
                        "trip_id": trip_id,
                        "arrival_time": _time(elapsed),
                        "departure_time": _time(elapsed),
                        "stop_id": _id("WBTC", stop["name"]),
                        "stop_sequence": str(idx),
                    }
                )
                lon, lat = stop["coordinates"]
                shape_rows.append(
                    {
                        "shape_id": shape_id,
                        "shape_pt_lat": f"{lat:.7f}",
                        "shape_pt_lon": f"{lon:.7f}",
                        "shape_pt_sequence": str(idx),
                    }
                )
            frequency_rows.append(
                {
                    "trip_id": trip_id,
                    "start_time": "05:30:00",
                    "end_time": "22:30:00",
                    "headway_secs": "900",
                    "exact_times": "0",
                }
            )

    stop_rows = [
        {
            "stop_id": _id("WBTC", name),
            "stop_name": name,
            "stop_lat": f"{stop['coordinates'][1]:.7f}",
            "stop_lon": f"{stop['coordinates'][0]:.7f}",
        }
        for name, stop in sorted(used_stops.items())
    ]
    documents = {
        "agency.txt": _csv_text(
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            [
                {
                    "agency_id": "WBTC",
                    "agency_name": "West Bengal Transport Corporation",
                    "agency_url": "https://wbtconline.in/",
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
                    "feed_publisher_name": "West Bengal Transport Corporation unofficial construction",
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
                "schema": "sevent4.wbtc_city_bus_gtfs.sources.v1",
                "status": "unofficial_constructed",
                "agency": "West Bengal Transport Corporation",
                "generated_at": generated_at,
                "source_url": source_url,
                "source_html": str(source_html),
                "osm_stops": str(osm_stops),
                "anchor_points": [str(path) for path in anchor_points],
                "gtfs_zip": str(out_zip),
                "counts": {
                    "source_routes": len(routes),
                    "routes": len(route_rows),
                    "stops": len(stop_rows),
                    "trips": len(trip_rows),
                    "stop_times": len(stop_time_rows),
                    "skipped_routes": len(skipped),
                    "anchor_point_sources": len(anchor_points),
                },
                "skipped_routes": skipped,
                "note": "Unofficial static GTFS constructed from WBTC public route rows, OSM bus-stop geometry, and optional source-backed transit anchor points; not an agency-published GTFS feed.",
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "source_routes": len(routes),
        "routes": len(route_rows),
        "stops": len(stop_rows),
        "trips": len(trip_rows),
        "stop_times": len(stop_time_rows),
        "skipped_routes": len(skipped),
    }


def _parse_wbtc_routes(path: Path) -> list[dict[str, str]]:
    parser = _TableParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    routes = []
    for row in parser.rows:
        if len(row) < 5 or not row[0].isdigit() or row[1].casefold() == "route no.":
            continue
        routes.append(
            {
                "serial": row[0],
                "route_no": row[1],
                "origin": row[2],
                "destination": row[3],
                "stoppage": row[4],
            }
        )
    return routes


def _matched_sequence(route: dict[str, str], lookup: "_StopLookup") -> tuple[list[dict[str, Any]], list[str]]:
    raw_names = [route["origin"], *_split_stoppages(route["stoppage"]), route["destination"]]
    sequence = []
    unmatched = []
    seen = set()
    for raw_name in raw_names:
        stop = lookup.match(raw_name)
        if stop is None:
            unmatched.append(raw_name)
            continue
        if stop["name"] in seen:
            continue
        seen.add(stop["name"])
        sequence.append(stop)
    return sequence, unmatched


def _split_stoppages(value: str) -> list[str]:
    value = html.unescape(value).replace("\xa0", " ")
    for old in ("–", "—", "/", ","):
        value = value.replace(old, "-")
    return [part.strip(" .") for part in re.split(r"\s*-\s*", value) if len(part.strip(" .")) >= 3]


def _stop_lookup(path: Path, anchor_points: list[Path] | None = None) -> "_StopLookup":
    stops = []
    for source in [path, *(anchor_points or [])]:
        data = json.loads(source.read_text(encoding="utf-8"))
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            geometry = feature.get("geometry") or {}
            name = props.get("name") or props.get("stop_name") or props.get("station")
            if not name or geometry.get("type") != "Point":
                continue
            stops.append({"name": name, "coordinates": geometry.get("coordinates")})
    return _StopLookup(stops)


class _StopLookup:
    def __init__(self, stops: list[dict[str, Any]]) -> None:
        self.stops = [(stop, _normalize(stop["name"]), _tokens(stop["name"])) for stop in stops if len(_normalize(stop["name"])) >= 4]
        self.exact = {}
        for stop, normalized, _ in self.stops:
            self.exact.setdefault(normalized, stop)

    def match(self, raw_name: str) -> dict[str, Any] | None:
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
        "ave": "avenue",
        "avn": "avenue",
        "xing": "crossing",
    }
    for source, target in replacements.items():
        value = re.sub(rf"\b{re.escape(source)}\b", target, value)
    value = re.sub(r"\b(p s|ps|police station)\b", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _tokens(value: str) -> set[str]:
    ignored = {"more", "road", "station", "metro", "stand", "gate", "city", "park"}
    return {token for token in _normalize(value).split() if len(token) >= 4 and token not in ignored}


def _id(prefix: str, value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return f"{prefix}_{normalized}"


def _time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}:00"


def _csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    handle = io.StringIO()
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return handle.getvalue()


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_cell = False
        self.current: list[str] = []
        self.row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        elif tag in {"td", "th"}:
            self.in_cell = True
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.in_cell:
            self.row.append(" ".join(html.unescape("".join(self.current)).replace("\xa0", " ").split()))
            self.in_cell = False
        elif tag == "tr" and self.row:
            self.rows.append(self.row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build unofficial WBTC city-bus GTFS from official route table rows.")
    parser.add_argument("--source-html", type=Path, required=True)
    parser.add_argument("--osm-stops", type=Path, required=True)
    parser.add_argument("--anchor-points", type=Path, nargs="*", default=[])
    parser.add_argument("--out-zip", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    args = parser.parse_args()
    result = build_wbtc_city_bus_gtfs(
        source_html=args.source_html,
        osm_stops=args.osm_stops,
        anchor_points=args.anchor_points,
        out_zip=args.out_zip,
        provenance_path=args.provenance,
        generated_at=args.generated_at,
        source_url=args.source_url,
    )
    print(
        f"wrote WBTC constructed GTFS: {result['stops']} stops, {result['routes']} routes, "
        f"{result['skipped_routes']} skipped routes"
    )


if __name__ == "__main__":
    main()
