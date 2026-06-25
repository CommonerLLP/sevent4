from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sevent4.ports.transit import GtfsCorridorInput, GtfsCorridorWriter, GtfsRow


@dataclass(frozen=True)
class GtfsCorridorResult:
    document: dict


def build_gtfs_corridors(
    inputs: GtfsCorridorInput,
    writer: GtfsCorridorWriter,
) -> GtfsCorridorResult:
    stops = _stops(inputs.stops)
    routes = _routes(inputs.routes)
    trips = _trips(inputs.trips)
    shapes = _shapes(inputs.shapes) if inputs.shapes else {}
    stop_times = _stop_times(inputs.stop_times) if not shapes else {}

    features = []
    route_trip: dict[str, GtfsRow] = {}
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
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "route_id": route_id,
                    "route_short_name": route.get("route_short_name", ""),
                    "route_long_name": route.get("route_long_name", ""),
                    "agency_id": route.get("agency_id", ""),
                },
                "geometry": {"type": "LineString", "coordinates": line},
            }
        )

    document = {"type": "FeatureCollection", "features": features}
    writer.write_geojson(document)
    return GtfsCorridorResult(document=document)


def split_corridors_by_agency(document: dict, agency_outputs: dict[str, str]) -> dict[str, dict]:
    """Split a route-corridor FeatureCollection into one FeatureCollection per
    agency. Each output keeps only that agency's features, reshaped to a `kind`
    property. Returns {output_filename: FeatureCollection}."""
    features = document.get("features", [])
    splits: dict[str, dict] = {}
    for agency, filename in agency_outputs.items():
        selected = [
            {"type": "Feature", "properties": {"kind": agency}, "geometry": feature.get("geometry")}
            for feature in features
            if (feature.get("properties") or {}).get("agency_id") == agency
        ]
        splits[filename] = {"type": "FeatureCollection", "features": selected}
    return splits


def _stops(rows: list[GtfsRow]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for row in rows:
        try:
            out[row["stop_id"]] = [float(row["stop_lon"]), float(row["stop_lat"])]
        except (KeyError, ValueError):
            continue
    return out


def _routes(rows: list[GtfsRow]) -> dict[str, GtfsRow]:
    return {row["route_id"]: row for row in rows if row.get("route_id")}


def _trips(rows: list[GtfsRow]) -> list[GtfsRow]:
    return [row for row in rows if row.get("route_id") and row.get("trip_id")]


def _shapes(rows: list[GtfsRow]) -> dict[str, list[list[float]]]:
    points_by_shape: dict[str, list[tuple[int, list[float]]]] = defaultdict(list)
    for row in rows:
        try:
            points_by_shape[row["shape_id"]].append(
                (int(row["shape_pt_sequence"]), [float(row["shape_pt_lon"]), float(row["shape_pt_lat"])])
            )
        except (KeyError, ValueError):
            continue
    return {shape_id: [point for _, point in sorted(points)] for shape_id, points in points_by_shape.items()}


def _stop_times(rows: list[GtfsRow]) -> dict[str, list[str]]:
    stops_by_trip: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in rows:
        try:
            stops_by_trip[row["trip_id"]].append((int(row["stop_sequence"]), row["stop_id"]))
        except (KeyError, ValueError):
            continue
    return {trip_id: [stop_id for _, stop_id in sorted(points)] for trip_id, points in stops_by_trip.items()}
