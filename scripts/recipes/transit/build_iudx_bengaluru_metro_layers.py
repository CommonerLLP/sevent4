#!/usr/bin/env python3
"""Build Bengaluru BMRCL layers from IUDX catalogue sample files."""
from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from pathlib import Path
from typing import Any


BMRCL_SAMPLE_COVERAGE_SCOPE = {
    "as_of": "2026-07-04",
    "coverage_complete": False,
    "expected_operational_route_short_names": ["Purple Line", "Green Line", "Yellow Line"],
    "sample_route_short_names": ["Purple Line", "Green Line"],
    "missing_operational_route_short_names": ["Yellow Line"],
    "unverified_or_upcoming_route_short_names": ["Pink Line", "Blue Line"],
    "note": (
        "The public IUDX sample line file covers Purple and Green only. "
        "Yellow is operational in 2026 but absent from this sample; Pink and Blue "
        "are not counted as operational here until public service is verified."
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Bengaluru IUDX BMRCL metro layers.")
    parser.add_argument("--stations-json", required=True, type=Path)
    parser.add_argument("--lines-json", required=True, type=Path)
    parser.add_argument("--bmrcl-network-detail", required=True, type=Path)
    parser.add_argument("--bmrcl-operations-detail", required=True, type=Path)
    parser.add_argument("--bmtc-detail", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--gtfs-zip", type=Path)
    parser.add_argument("--gtfs-provenance", type=Path)
    parser.add_argument("--generated-at", default="2026-07-04T00:00:00Z")
    args = parser.parse_args()

    stations = json.loads(args.stations_json.read_text(encoding="utf-8"))
    lines = json.loads(args.lines_json.read_text(encoding="utf-8"))
    station_fc = _station_features(stations)
    route_fc = _route_features(lines)
    constructed_gtfs = None
    if args.gtfs_zip or args.gtfs_provenance:
        if not args.gtfs_zip or not args.gtfs_provenance:
            parser.error("--gtfs-zip and --gtfs-provenance must be provided together")
        constructed_gtfs = build_bmrcl_sample_gtfs(
            stations_json=args.stations_json,
            lines_json=args.lines_json,
            out_zip=args.gtfs_zip,
            provenance_path=args.gtfs_provenance,
            generated_at=args.generated_at,
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.out_dir / "metro_gtfs_stops.geojson", station_fc)
    _write_json(args.out_dir / "metro_gtfs_routes.geojson", route_fc)
    _patch_manifest(args.out_dir / "layer_manifest.json")

    args.source_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        args.source_dir / "iudx_bengaluru_transit.sources.json",
        _sources(args, station_fc, route_fc, constructed_gtfs=constructed_gtfs),
        indent=1,
    )
    print(f"wrote {len(station_fc['features'])} BMRCL stops and {len(route_fc['features'])} BMRCL routes")


def build_bmrcl_sample_gtfs(
    *,
    stations_json: Path,
    lines_json: Path,
    out_zip: Path,
    provenance_path: Path,
    generated_at: str,
) -> dict[str, int]:
    stations = json.loads(Path(stations_json).read_text(encoding="utf-8"))
    lines = json.loads(Path(lines_json).read_text(encoding="utf-8"))
    agency_id = "BMRCL"
    service_id = "sample_daily"

    stops = []
    stops_by_id = {}
    for row in stations:
        location = row.get("location", {})
        coordinates = location.get("coordinates", [])
        if len(coordinates) != 2:
            continue
        stop_id = str(row.get("stop_code", "")).strip()
        if not stop_id:
            continue
        stop = {
            "stop_id": stop_id,
            "stop_name": str(row.get("stop_name", stop_id)).strip() or stop_id,
            "stop_lat": f"{float(coordinates[1]):.7f}",
            "stop_lon": f"{float(coordinates[0]):.7f}",
        }
        stops_by_id[stop_id] = stop
        stops.append(stop)

    routes = []
    trips = []
    stop_times = []
    shapes = []
    frequencies = []
    for row in lines:
        route_id = str(row.get("route_id", "")).strip()
        if not route_id:
            continue
        route_name = str(row.get("route_long_name", route_id)).strip() or route_id
        routes.append(
            {
                "route_id": route_id,
                "agency_id": agency_id,
                "route_short_name": str(row.get("route_short_name", route_id)).strip() or route_id,
                "route_long_name": route_name,
                "route_type": "1",
            }
        )
        coordinates = row.get("location", {}).get("coordinates", [])
        line = [
            [float(pair[0]), float(pair[1])]
            for pair in coordinates
            if isinstance(pair, list | tuple) and len(pair) == 2
        ]
        sequence = row.get("routeStopSequence") or []
        ordered = [str(stop_id).strip() for stop_id in sequence if str(stop_id).strip() in stops_by_id]
        for direction_id, ordered_stops in ((0, ordered), (1, list(reversed(ordered)))):
            trip_id = f"{route_id}_{direction_id}"
            shape_id = f"{route_id}_{direction_id}"
            trips.append(
                {
                    "route_id": route_id,
                    "service_id": service_id,
                    "trip_id": trip_id,
                    "trip_headsign": stops_by_id[ordered_stops[-1]]["stop_name"] if ordered_stops else route_name,
                    "direction_id": str(direction_id),
                    "shape_id": shape_id,
                }
            )
            shape_line = list(reversed(line)) if direction_id else line
            for idx, coordinate in enumerate(shape_line, start=1):
                shapes.append(
                    {
                        "shape_id": shape_id,
                        "shape_pt_lat": f"{coordinate[1]:.7f}",
                        "shape_pt_lon": f"{coordinate[0]:.7f}",
                        "shape_pt_sequence": str(idx),
                    }
                )
            for idx, stop_id in enumerate(ordered_stops, start=1):
                time = _service_time(idx)
                stop_times.append(
                    {
                        "trip_id": trip_id,
                        "arrival_time": time,
                        "departure_time": time,
                        "stop_id": stop_id,
                        "stop_sequence": str(idx),
                    }
                )
            frequencies.append(
                {
                    "trip_id": trip_id,
                    "start_time": "06:00:00",
                    "end_time": "23:00:00",
                    "headway_secs": "600",
                }
            )

    documents = {
        "agency.txt": _csv_text(
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            [
                {
                    "agency_id": agency_id,
                    "agency_name": "Bangalore Metro Rail Corporation Limited",
                    "agency_url": "https://english.bmrc.co.in/",
                    "agency_timezone": "Asia/Kolkata",
                }
            ],
        ),
        "stops.txt": _csv_text(["stop_id", "stop_name", "stop_lat", "stop_lon"], stops),
        "routes.txt": _csv_text(["route_id", "agency_id", "route_short_name", "route_long_name", "route_type"], routes),
        "trips.txt": _csv_text(["route_id", "service_id", "trip_id", "trip_headsign", "direction_id", "shape_id"], trips),
        "stop_times.txt": _csv_text(["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"], stop_times),
        "calendar.txt": _csv_text(
            ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"],
            [
                {
                    "service_id": service_id,
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
        "frequencies.txt": _csv_text(["trip_id", "start_time", "end_time", "headway_secs"], frequencies),
        "shapes.txt": _csv_text(["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"], shapes),
        "feed_info.txt": _csv_text(
            ["feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_start_date", "feed_end_date", "feed_version"],
            [
                {
                    "feed_publisher_name": "BMRCL IUDX public sample construction",
                    "feed_publisher_url": "https://catalogue.iudx.org.in/bengaluru",
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
    _write_json(
        provenance_path,
        {
            "schema": "sevent4.iudx_bmrcl_sample_gtfs.sources.v1",
            "status": "sample_public_constructed_gtfs",
            "city": "bengaluru",
            "operator": "Bangalore Metro Rail Corporation Limited",
            "source_dataset_id": "6c5df87a-38d6-4136-aadb-b3b55842d985",
            "generated_at": generated_at,
            "gtfs_zip": str(out_zip),
            "source_files": [str(stations_json), str(lines_json)],
            "counts": {
                "stops": len(stops),
                "routes": len(routes),
                "trips": len(trips),
                "stop_times": len(stop_times),
                "shapes": len(shapes),
                "frequencies": len(frequencies),
            },
            "coverage_scope": BMRCL_SAMPLE_COVERAGE_SCOPE,
            "note": "Static GTFS constructed from public IUDX BMRCL station and line sample files; authenticated schedule/fare resources remain SECURE-gated.",
        },
        indent=1,
    )
    return {
        "stops": len(stops),
        "routes": len(routes),
        "trips": len(trips),
        "stop_times": len(stop_times),
        "shapes": len(shapes),
        "frequencies": len(frequencies),
    }


def _station_features(rows: list[dict[str, Any]]) -> dict[str, Any]:
    features = []
    for row in rows:
        location = row["location"]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "name": row.get("stop_name", "").strip(),
                    "stop_code": row.get("stop_code", ""),
                    "mode": "metro",
                    "operator": "Bangalore Metro Rail Corporation Limited",
                    "source": "IUDX Bengaluru Metro Station Locations sample file",
                    "source_dataset_id": "6c5df87a-38d6-4136-aadb-b3b55842d985",
                    "source_resource_id": row.get("id", "938d4b2d-565b-4cee-afca-fe6dbf628ccf"),
                },
                "geometry": {"type": "Point", "coordinates": location["coordinates"]},
            }
        )
    return _fc(features)


def _route_features(rows: list[dict[str, Any]]) -> dict[str, Any]:
    features = []
    for row in rows:
        sequence = row.get("routeStopSequence") or []
        location = row["location"]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "name": row.get("route_long_name", ""),
                    "route_id": row.get("route_id", ""),
                    "route_short_name": row.get("route_short_name", ""),
                    "mode": "metro",
                    "operator": "Bangalore Metro Rail Corporation Limited",
                    "station_count": len(sequence),
                    "station_codes": "; ".join(sequence),
                    "source": "IUDX Bengaluru Metro Rail Lines sample file",
                    "source_dataset_id": "6c5df87a-38d6-4136-aadb-b3b55842d985",
                    "source_resource_id": row.get("id", "e2c3b8a9-e03c-4045-9c80-66d463ca5cda"),
                },
                "geometry": {"type": "LineString", "coordinates": location["coordinates"]},
            }
        )
    return _fc(features)


def _patch_manifest(path: Path) -> None:
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = [
        {
            "id": "metro_gtfs_routes",
            "label": "Metro routes (IUDX/BMRCL sample)",
            "file": "metro_gtfs_routes.geojson",
            "kind": "line",
            "group": "Transit",
            "default": False,
            "popup": ["name", "route_short_name", "station_count", "operator", "source"],
            "paint": {"line-color": "#7857d6", "line-width": 2.6, "line-opacity": 0.88},
        },
        {
            "id": "metro_gtfs_stops",
            "label": "Metro stations (IUDX/BMRCL sample)",
            "file": "metro_gtfs_stops.geojson",
            "kind": "circle",
            "group": "Transit",
            "default": False,
            "popup": ["name", "stop_code", "operator", "source"],
            "paint": {
                "circle-color": "#36a3d9",
                "circle-radius": 3.4,
                "circle-stroke-color": "#101318",
                "circle-stroke-width": 0.7,
                "circle-opacity": 0.9,
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


def _sources(
    args: argparse.Namespace,
    station_fc: dict[str, Any],
    route_fc: dict[str, Any],
    *,
    constructed_gtfs: dict[str, int] | None = None,
) -> dict[str, Any]:
    bmrcl_network = _detail_summary(args.bmrcl_network_detail)
    bmrcl_operations = _detail_summary(args.bmrcl_operations_detail)
    bmtc = _detail_summary(args.bmtc_detail)
    document = {
        "schema": "sevent4.iudx_transit.sources.v1",
        "city": "bengaluru",
        "catalogue": {
            "instance": "bengaluru",
            "instance_id": "33fc80f8-7d3a-4b6c-ae4d-45751e001694",
            "dataset_endpoint": "https://cos.iudx.org.in/iudx/cat/v1/internal/ui/dataset",
            "catalogue_url": "https://catalogue.iudx.org.in/bengaluru",
            "probed_on": "2026-07-03",
        },
        "downloaded_public_files": [
            {
                "url": "https://fs-sample-file-bucket.s3.ap-south-1.amazonaws.com/public-access/bengaluru/bengaluru-metro-additional-info-metro-stations-location.json",
                "local": str(args.stations_json),
                "features": len(station_fc["features"]),
            },
            {
                "url": "https://fs-sample-file-bucket.s3.ap-south-1.amazonaws.com/public-access/bengaluru/bengaluru-metro-additional-info-metro-lines.json",
                "local": str(args.lines_json),
                "features": len(route_fc["features"]),
            },
        ],
        "datasets": [bmrcl_network, bmrcl_operations, bmtc],
        "layers": {
            "metro_gtfs_stops.geojson": len(station_fc["features"]),
            "metro_gtfs_routes.geojson": len(route_fc["features"]),
        },
        "coverage_scope": BMRCL_SAMPLE_COVERAGE_SCOPE,
        "access_note": (
            "IUDX catalogue metadata is public. Authenticated probe on "
            "2026-07-04 confirmed the provided portal client credentials work "
            "against authorization.iudx.org.in for a COS resource-server "
            "consumer token. BMTC GTFS table resources plus BMRCL network/"
            "schedule/fare resources remain SECURE; BMTC and BMRCL "
            "resource-level consumer token requests returned APD evaluation "
            "failed: No policy exist for given item's Resource Group, and "
            "resource-server-token reads returned 401 invalidAuthorizationToken "
            "from rs.cos.iudx.org.in."
        ),
    }
    if constructed_gtfs and args.gtfs_zip and args.gtfs_provenance:
        document["constructed_gtfs"] = {
            "status": "sample_public_constructed_gtfs",
            "local": str(args.gtfs_zip),
            "provenance": str(args.gtfs_provenance),
            "source_files": [str(args.stations_json), str(args.lines_json)],
            "counts": constructed_gtfs,
            "coverage_scope": BMRCL_SAMPLE_COVERAGE_SCOPE,
            "note": (
                "Static GTFS constructed from public IUDX BMRCL station and line sample files. "
                "Authenticated schedule/fare resources remain SECURE-gated."
            ),
        }
    return document


def _detail_summary(path: Path) -> dict[str, Any]:
    detail = json.loads(path.read_text(encoding="utf-8"))
    result = detail["results"][0]
    dataset = result["dataset"]
    resources = []
    for resource in result.get("resource", []):
        resources.append(
            {
                "id": resource.get("resourceId"),
                "label": resource.get("label"),
                "accessPolicy": resource.get("accessPolicy"),
                "resourceType": resource.get("resourceType"),
                "resourceServer": resource.get("resourceServer"),
                "apis": resource.get("iudxResourceAPIs", []),
            }
        )
    return {
        "id": dataset.get("id"),
        "label": dataset.get("label"),
        "provider": dataset.get("provider", {}),
        "description": dataset.get("description", ""),
        "totalResources": dataset.get("totalResources"),
        "resources": resources,
    }


def _fc(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def _csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fieldnames})
    return out.getvalue()


def _service_time(sequence: int) -> str:
    minutes = (sequence - 1) * 3
    return f"{6 + minutes // 60:02d}:{minutes % 60:02d}:00"


def _write_json(path: Path, document: dict[str, Any], indent: int | None = None) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
