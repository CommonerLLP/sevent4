#!/usr/bin/env python3
"""Build bus layers from public IUDX static sample files."""
from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from pathlib import Path
from typing import Any


def build_iudx_bus_sample_layers(
    *,
    city: str,
    operator: str,
    dataset_id: str,
    stops_json: Path,
    routes_json: Path,
    resources_json: Path,
    out_dir: Path,
    source_dir: Path,
) -> dict[str, int]:
    stop_rows = _rows(json.loads(Path(stops_json).read_text(encoding="utf-8")))
    route_rows = _rows(json.loads(Path(routes_json).read_text(encoding="utf-8")))
    resources = _resource_summaries(json.loads(Path(resources_json).read_text(encoding="utf-8")))
    stop_fc = _stop_features(stop_rows, operator, dataset_id)
    route_fc = _route_features(route_rows, operator, dataset_id)

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "bus_stops.geojson", stop_fc)
    _write_json(out_dir / "bus_routes.geojson", route_fc)
    _patch_manifest(out_dir / "layer_manifest.json")

    source_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        source_dir / "iudx_bus_sample.sources.json",
        _sources(
            city=city,
            operator=operator,
            dataset_id=dataset_id,
            stops_json=Path(stops_json),
            routes_json=Path(routes_json),
            resources_json=Path(resources_json),
            resources=resources,
            stop_count=len(stop_fc["features"]),
            route_count=len(route_fc["features"]),
        ),
        indent=1,
    )
    return {"stop_features": len(stop_fc["features"]), "route_features": len(route_fc["features"])}


def build_iudx_bus_sample_gtfs(
    *,
    city: str,
    operator: str,
    dataset_id: str,
    agency_url: str,
    stops_json: Path,
    routes_json: Path,
    out_zip: Path,
    provenance_path: Path,
    generated_at: str,
) -> dict[str, int]:
    stop_rows = _rows(json.loads(Path(stops_json).read_text(encoding="utf-8")))
    route_rows = _rows(json.loads(Path(routes_json).read_text(encoding="utf-8")))
    agency_id = f"{city.upper()}IUDX"
    service_id = "sample_daily"

    stops = []
    stops_by_id = {}
    for row in stop_rows:
        point = _point_coordinates(row)
        if point is None:
            continue
        stop_id = _first_text(row, ("stop_id", "stopCode", "stop_code", "stationCode", "id"))
        if not stop_id:
            continue
        stop = {
            "stop_id": stop_id,
            "stop_name": _first_text(row, ("stop_name", "stopName", "name", "stationName", "description")) or stop_id,
            "stop_lat": f"{point[1]:.7f}",
            "stop_lon": f"{point[0]:.7f}",
        }
        stops_by_id[stop_id] = stop
        stops.append(stop)

    routes = []
    trips = []
    stop_times = []
    shapes = []
    frequencies = []
    for row in route_rows:
        route_id = _first_text(row, ("route_id", "routeId", "routeCode", "id"))
        if not route_id:
            continue
        route_name = _first_text(row, ("route_long_name", "routeLongName", "routeName", "name", "description"))
        routes.append(
            {
                "route_id": route_id,
                "agency_id": agency_id,
                "route_short_name": _first_text(row, ("route_short_name", "routeShortName", "routeCode")) or route_id,
                "route_long_name": route_name or route_id,
                "route_type": "3",
            }
        )
        line = _line_coordinates(row)
        sequence = row.get("routeStopSequence") or row.get("route_stop_sequence") or []
        sequence = [str(stop_id) for stop_id in sequence if str(stop_id) in stops_by_id] if isinstance(sequence, list) else []
        for direction_id, ordered_stops in ((0, sequence), (1, list(reversed(sequence)))):
            trip_id = f"{route_id}_{direction_id}"
            shape_id = f"{route_id}_{direction_id}"
            trips.append(
                {
                    "route_id": route_id,
                    "service_id": service_id,
                    "trip_id": trip_id,
                    "trip_headsign": stops_by_id[ordered_stops[-1]]["stop_name"] if ordered_stops else route_name or route_id,
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
                    "end_time": "22:00:00",
                    "headway_secs": "900",
                }
            )

    documents = {
        "agency.txt": _csv_text(["agency_id", "agency_name", "agency_url", "agency_timezone"], [
            {
                "agency_id": agency_id,
                "agency_name": operator,
                "agency_url": agency_url,
                "agency_timezone": "Asia/Kolkata",
            }
        ]),
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
                    "feed_publisher_name": f"{operator} IUDX public sample construction",
                    "feed_publisher_url": agency_url,
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
            "schema": "sevent4.iudx_bus_sample_gtfs.sources.v1",
            "status": "sample_public_constructed_gtfs",
            "city": city,
            "operator": operator,
            "source_dataset_id": dataset_id,
            "generated_at": generated_at,
            "gtfs_zip": str(out_zip),
            "source_files": [str(stops_json), str(routes_json)],
            "counts": {
                "stops": len(stops),
                "routes": len(routes),
                "trips": len(trips),
                "stop_times": len(stop_times),
                "shapes": len(shapes),
                "frequencies": len(frequencies),
            },
            "note": "Static GTFS constructed from public IUDX catalogue sample files; authenticated full resources remain SECURE-gated.",
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build city bus layers from public IUDX static sample files.")
    parser.add_argument("--city", required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--stops-json", required=True, type=Path)
    parser.add_argument("--routes-json", required=True, type=Path)
    parser.add_argument("--resources-json", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--source-dir", required=True, type=Path)
    args = parser.parse_args()

    result = build_iudx_bus_sample_layers(
        city=args.city,
        operator=args.operator,
        dataset_id=args.dataset_id,
        stops_json=args.stops_json,
        routes_json=args.routes_json,
        resources_json=args.resources_json,
        out_dir=args.out_dir,
        source_dir=args.source_dir,
    )
    print(f"wrote {result['stop_features']} bus stops and {result['route_features']} bus routes for {args.city}")


def _rows(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, list):
        return [row for row in document if isinstance(row, dict)]
    if isinstance(document, dict):
        for key in ("results", "data", "features"):
            value = document.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        if isinstance(document.get("records"), list):
            return [row for row in document["records"] if isinstance(row, dict)]
    raise ValueError("IUDX sample JSON must be a list or a mapping with rows")


def _stop_features(rows: list[dict[str, Any]], operator: str, dataset_id: str) -> dict[str, Any]:
    features = []
    for row in rows:
        point = _point_coordinates(row)
        if point is None:
            continue
        stop_id = _first_text(row, ("stop_id", "stopCode", "stop_code", "stationCode", "id"))
        stop_name = _first_text(row, ("stop_name", "stopName", "name", "stationName", "description"))
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "stop_id": stop_id,
                    "stop_name": stop_name,
                    "mode": "bus",
                    "operator": operator,
                    "source": "IUDX public sample file",
                    "source_dataset_id": dataset_id,
                    "source_resource_id": _first_text(row, ("id", "resourceId", "resource_id")),
                },
                "geometry": {"type": "Point", "coordinates": point},
            }
        )
    return _fc(features)


def _route_features(rows: list[dict[str, Any]], operator: str, dataset_id: str) -> dict[str, Any]:
    features = []
    for row in rows:
        line = _line_coordinates(row)
        if not line:
            continue
        sequence = row.get("routeStopSequence") or row.get("route_stop_sequence") or []
        route_id = _first_text(row, ("route_id", "routeId", "routeCode", "id"))
        route_name = _first_text(row, ("route_long_name", "routeLongName", "routeName", "name", "description"))
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "route_id": route_id,
                    "route_short_name": _first_text(row, ("route_short_name", "routeShortName", "routeCode")),
                    "route_long_name": route_name,
                    "name": route_name or route_id,
                    "mode": "bus",
                    "operator": operator,
                    "stop_sequence_count": len(sequence) if isinstance(sequence, list) else 0,
                    "stop_sequence": "; ".join(str(part) for part in sequence) if isinstance(sequence, list) else "",
                    "source": "IUDX public sample file",
                    "source_dataset_id": dataset_id,
                    "source_resource_id": _first_text(row, ("id", "resourceId", "resource_id")),
                },
                "geometry": {"type": "LineString", "coordinates": line},
            }
        )
    return _fc(features)


def _point_coordinates(row: dict[str, Any]) -> list[float] | None:
    geometry = _geometry(row)
    if geometry and geometry.get("type") == "Point":
        return _coordinate_pair(geometry.get("coordinates"))
    lon = _first_float(row, ("longitude", "lon", "lng", "stop_lon"))
    lat = _first_float(row, ("latitude", "lat", "stop_lat"))
    if lon is None or lat is None:
        return None
    return [lon, lat]


def _line_coordinates(row: dict[str, Any]) -> list[list[float]]:
    geometry = _geometry(row)
    if not geometry or geometry.get("type") != "LineString":
        return []
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list):
        return []
    out = []
    for coordinate in coordinates:
        pair = _coordinate_pair(coordinate)
        if pair is not None:
            out.append(pair)
    return out


def _geometry(row: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("location", "geometry"):
        value = row.get(key)
        if isinstance(value, dict):
            return value
    return None


def _coordinate_pair(value: Any) -> list[float] | None:
    if not isinstance(value, list | tuple) or len(value) < 2:
        return None
    try:
        lon = float(value[0])
        lat = float(value[1])
    except (TypeError, ValueError):
        return None
    return [lon, lat]


def _first_text(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return str(value).strip()
    return ""


def _first_float(row: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _patch_manifest(path: Path) -> None:
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = [
        {
            "id": "bus_stops",
            "label": "Bus stops (IUDX sample)",
            "file": "bus_stops.geojson",
            "kind": "circle",
            "group": "Transit",
            "default": False,
            "popup": ["stop_name", "operator", "source"],
            "paint": {
                "circle-color": "#9ca3ad",
                "circle-radius": 3.2,
                "circle-stroke-color": "#101318",
                "circle-stroke-width": 0.6,
                "circle-opacity": 0.85,
            },
        },
        {
            "id": "bus_routes",
            "label": "Bus routes (IUDX sample)",
            "file": "bus_routes.geojson",
            "kind": "line",
            "group": "Transit",
            "default": False,
            "popup": ["route_short_name", "route_long_name", "operator", "source"],
            "paint": {"line-color": "#9ca3ad", "line-width": 1.8, "line-opacity": 0.88},
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
    *,
    city: str,
    operator: str,
    dataset_id: str,
    stops_json: Path,
    routes_json: Path,
    resources_json: Path,
    resources: list[dict[str, Any]],
    stop_count: int,
    route_count: int,
) -> dict[str, Any]:
    return {
        "schema": "sevent4.iudx_bus_sample.sources.v1",
        "city": city,
        "feeds": [
            {
                "feed_id": f"{city}_iudx_bus_sample",
                "mode": "bus",
                "operator": operator,
                "status": "sample_public",
                "source_dataset_id": dataset_id,
                "source_files": [str(stops_json), str(routes_json), str(resources_json)],
                "layers": {"bus_stops.geojson": stop_count, "bus_routes.geojson": route_count},
                "note": "Built from public IUDX catalogue sample files; authenticated live resources remain SECURE.",
            }
        ],
        "resources": resources,
    }


def _resource_summaries(document: Any) -> list[dict[str, Any]]:
    resources = []
    if isinstance(document, dict):
        values = document.get("results")
        if isinstance(values, dict):
            values = values.get("resource") or values.get("resources")
        if values is None:
            values = document.get("resource") or document.get("resources")
    elif isinstance(document, list):
        values = document
    else:
        values = []
    for resource in values if isinstance(values, list) else []:
        if not isinstance(resource, dict):
            continue
        resources.append(
            {
                "id": resource.get("id") or resource.get("resourceId"),
                "label": resource.get("label"),
                "accessPolicy": resource.get("accessPolicy"),
                "resourceType": resource.get("resourceType"),
                "resourceServer": resource.get("resourceServer"),
            }
        )
    return resources


def _fc(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def _write_json(path: Path, document: dict[str, Any], indent: int | None = None) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def _csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    handle = io.StringIO()
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return handle.getvalue()


def _service_time(stop_sequence: int) -> str:
    minutes = (stop_sequence - 1) * 3
    return f"{minutes // 60:02d}:{minutes % 60:02d}:00"


if __name__ == "__main__":
    main()
