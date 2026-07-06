from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sevent4.ports.transit import GtfsCorridorInput, GtfsCorridorWriter, GtfsRow


@dataclass(frozen=True)
class GtfsCorridorResult:
    document: dict


@dataclass(frozen=True)
class TransitFeedSpec:
    feed_id: str
    city: str
    mode: str
    operator: str
    stop_layer: str
    route_layer: str
    source_url: str = ""
    license: str = ""
    status: str = "available"
    provenance_status: str = "ok"
    missing_reason: str = ""
    notes: str = ""
    route_types: tuple[str, ...] = ()
    bbox: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class GtfsLayerBundleResult:
    layers: dict[str, dict]
    provenance: dict


def build_gtfs_corridors(
    inputs: GtfsCorridorInput,
    writer: GtfsCorridorWriter,
) -> GtfsCorridorResult:
    document = _route_feature_collection(inputs)
    writer.write_geojson(document)
    return GtfsCorridorResult(document=document)


def build_multimodal_gtfs_layers(
    feed_specs: list[TransitFeedSpec],
    inputs_by_feed: dict[str, GtfsCorridorInput],
) -> GtfsLayerBundleResult:
    layers: dict[str, dict] = {}
    feeds = []
    for spec in feed_specs:
        inputs = inputs_by_feed.get(spec.feed_id)
        if spec.status != "available":
            feeds.append(_feed_provenance(spec, spec.status, 0, 0))
            continue
        if inputs is None:
            feeds.append(_feed_provenance(spec, "missing", 0, 0))
            continue

        if spec.route_types:
            inputs = _filter_inputs_by_route_type(inputs, spec.route_types)
        if spec.bbox is not None:
            inputs = _filter_inputs_by_bbox(inputs, spec.bbox)
        stops_document = _stop_feature_collection(inputs, spec)
        routes_document = _route_feature_collection(inputs, spec)
        layers[f"{spec.stop_layer}.geojson"] = stops_document
        layers[f"{spec.route_layer}.geojson"] = routes_document
        feeds.append(
            _feed_provenance(
                spec,
                spec.provenance_status,
                len(stops_document["features"]),
                len(routes_document["features"]),
            )
        )

    return GtfsLayerBundleResult(
        layers=layers,
        provenance={
            "schema": "sevent4.multimodal_transit.sources.v1",
            "feeds": feeds,
        },
    )


def coastal_multimodal_feed_specs() -> list[TransitFeedSpec]:
    missing = "No local GTFS feed path configured."
    return [
        TransitFeedSpec(
            feed_id="chennai_southern_rail_suburban",
            city="chennai",
            mode="suburban_rail",
            operator="Southern Railway",
            stop_layer="suburban_rail_stations",
            route_layer="suburban_rail",
            status="missing",
            missing_reason=missing,
        ),
        TransitFeedSpec(
            feed_id="chennai_mrts",
            city="chennai",
            mode="mrts",
            operator="Southern Railway / Chennai Metro Rail Limited",
            stop_layer="mrts_stations",
            route_layer="mrts",
            status="missing",
            missing_reason=missing,
            notes="MRTS is retained as a distinct Chennai feed while service integration is incomplete.",
        ),
        TransitFeedSpec(
            feed_id="chennai_mtc_bus",
            city="chennai",
            mode="bus",
            operator="Metropolitan Transport Corporation Chennai",
            stop_layer="bus_stops",
            route_layer="bus_routes",
            status="missing",
            missing_reason=missing,
        ),
        TransitFeedSpec(
            feed_id="kolkata_eastern_se_suburban",
            city="kolkata",
            mode="suburban_rail",
            operator="Eastern Railway / South Eastern Railway",
            stop_layer="suburban_rail_stations",
            route_layer="suburban_rail",
            status="missing",
            missing_reason=missing,
        ),
        TransitFeedSpec(
            feed_id="kolkata_metro",
            city="kolkata",
            mode="metro",
            operator="Kolkata Metro Railway",
            stop_layer="metro_gtfs_stops",
            route_layer="metro_gtfs_routes",
            status="missing",
            missing_reason=missing,
        ),
        TransitFeedSpec(
            feed_id="kolkata_wbtc_bus",
            city="kolkata",
            mode="bus",
            operator="West Bengal Transport Corporation",
            stop_layer="bus_stops",
            route_layer="bus_routes",
            status="missing",
            missing_reason=missing,
        ),
        TransitFeedSpec(
            feed_id="kolkata_regulated_private_bus",
            city="kolkata",
            mode="regulated_private_bus",
            operator="Kolkata regulated private bus permit network",
            stop_layer="regulated_private_bus_stops",
            route_layer="regulated_private_bus_routes",
            status="missing",
            missing_reason=missing,
        ),
        TransitFeedSpec(
            feed_id="mumbai_western_central_suburban",
            city="mumbai",
            mode="suburban_rail",
            operator="Western Railway / Central Railway",
            stop_layer="suburban_rail_stations",
            route_layer="suburban_rail",
            status="missing",
            missing_reason=missing,
        ),
        TransitFeedSpec(
            feed_id="mumbai_best_bus",
            city="mumbai",
            mode="bus",
            operator="Brihanmumbai Electric Supply and Transport",
            stop_layer="bus_stops",
            route_layer="bus_routes",
            status="missing",
            missing_reason=missing,
        ),
        TransitFeedSpec(
            feed_id="mumbai_metro",
            city="mumbai",
            mode="metro",
            operator="Mumbai Metro",
            stop_layer="metro_gtfs_stops",
            route_layer="metro_gtfs_routes",
            status="missing",
            missing_reason=missing,
        ),
    ]


def _route_feature_collection(inputs: GtfsCorridorInput, spec: TransitFeedSpec | None = None) -> dict:
    stops = _stops(inputs.stops)
    routes = _routes(inputs.routes)
    trips = _trips(inputs.trips)
    shapes = _shapes(inputs.shapes) if inputs.shapes else {}
    if not shapes and not inputs.stop_times:
        # With no shapes.txt, corridors are drawn from stop_times. A feed missing
        # both would silently yield an empty FeatureCollection, hiding a bad or
        # incomplete acquisition — fail loudly instead.
        raise ValueError("GTFS feed has neither shapes.txt nor stop_times.txt; cannot build corridors")
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
        properties = {
            "route_id": route_id,
            "route_short_name": route.get("route_short_name", ""),
            "route_long_name": route.get("route_long_name", ""),
            "agency_id": route.get("agency_id", ""),
        }
        if spec is not None:
            properties.update(
                {
                    "mode": spec.mode,
                    "operator": spec.operator,
                    "source_feed_id": spec.feed_id,
                }
            )
        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {"type": "LineString", "coordinates": line},
            }
        )

    return {"type": "FeatureCollection", "features": features}


def _stop_feature_collection(inputs: GtfsCorridorInput, spec: TransitFeedSpec) -> dict:
    features = []
    for row in inputs.stops:
        try:
            lon, lat = float(row["stop_lon"]), float(row["stop_lat"])
        except (KeyError, ValueError):
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "stop_id": row.get("stop_id", ""),
                    "stop_name": row.get("stop_name", ""),
                    "stop_code": row.get("stop_code", ""),
                    "mode": spec.mode,
                    "operator": spec.operator,
                    "source_feed_id": spec.feed_id,
                },
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _feed_provenance(spec: TransitFeedSpec, status: str, stop_count: int, route_count: int) -> dict:
    entry = {
        "feed_id": spec.feed_id,
        "city": spec.city,
        "mode": spec.mode,
        "operator": spec.operator,
        "status": status,
        "source_url": spec.source_url,
        "license": spec.license,
        "stop_layer": f"{spec.stop_layer}.geojson",
        "route_layer": f"{spec.route_layer}.geojson",
        "stop_features": stop_count,
        "route_features": route_count,
    }
    if status == "missing":
        entry["missing_reason"] = spec.missing_reason or "Feed not supplied to this run."
    elif spec.missing_reason:
        entry["missing_reason"] = spec.missing_reason
    if spec.notes:
        entry["notes"] = spec.notes
    if spec.route_types:
        entry["route_types"] = list(spec.route_types)
    if spec.bbox is not None:
        entry["bbox"] = list(spec.bbox)
    return entry


def _filter_inputs_by_route_type(inputs: GtfsCorridorInput, route_types: tuple[str, ...]) -> GtfsCorridorInput:
    allowed_types = {str(route_type) for route_type in route_types}
    routes = [row for row in inputs.routes if row.get("route_type") in allowed_types]
    route_ids = {row["route_id"] for row in routes if row.get("route_id")}
    trips = [row for row in inputs.trips if row.get("route_id") in route_ids]
    trip_ids = {row["trip_id"] for row in trips if row.get("trip_id")}
    stop_times = [row for row in inputs.stop_times if row.get("trip_id") in trip_ids]
    stop_ids = {row["stop_id"] for row in stop_times if row.get("stop_id")}
    shape_ids = {row.get("shape_id", "") for row in trips if row.get("shape_id")}
    return GtfsCorridorInput(
        stops=[row for row in inputs.stops if not stop_ids or row.get("stop_id") in stop_ids],
        routes=routes,
        trips=trips,
        shapes=[row for row in inputs.shapes if row.get("shape_id") in shape_ids],
        stop_times=stop_times,
    )


def _filter_inputs_by_bbox(inputs: GtfsCorridorInput, bbox: tuple[float, float, float, float]) -> GtfsCorridorInput:
    stops_by_id = {row["stop_id"]: row for row in inputs.stops if row.get("stop_id")}
    stop_times_by_trip: dict[str, list[GtfsRow]] = defaultdict(list)
    for row in inputs.stop_times:
        if row.get("trip_id"):
            stop_times_by_trip[row["trip_id"]].append(row)

    selected_trips = []
    selected_stop_ids: set[str] = set()
    for trip in inputs.trips:
        trip_id = trip.get("trip_id")
        if not trip_id:
            continue
        hit_stop_ids = [
            row["stop_id"]
            for row in stop_times_by_trip.get(trip_id, [])
            if row.get("stop_id") in stops_by_id and _stop_in_bbox(stops_by_id[row["stop_id"]], bbox)
        ]
        if len(hit_stop_ids) >= 2:
            selected_trips.append(trip)
            selected_stop_ids.update(hit_stop_ids)

    selected_trip_ids = {row["trip_id"] for row in selected_trips if row.get("trip_id")}
    selected_route_ids = {row["route_id"] for row in selected_trips if row.get("route_id")}
    selected_shape_ids = {row.get("shape_id", "") for row in selected_trips if row.get("shape_id")}
    return GtfsCorridorInput(
        stops=[row for row in inputs.stops if row.get("stop_id") in selected_stop_ids],
        routes=[row for row in inputs.routes if row.get("route_id") in selected_route_ids],
        trips=selected_trips,
        shapes=[
            row
            for row in inputs.shapes
            if row.get("shape_id") in selected_shape_ids and _shape_point_in_bbox(row, bbox)
        ],
        stop_times=[
            row
            for row in inputs.stop_times
            if row.get("trip_id") in selected_trip_ids and row.get("stop_id") in selected_stop_ids
        ],
    )


def _stop_in_bbox(row: GtfsRow, bbox: tuple[float, float, float, float]) -> bool:
    try:
        lon, lat = float(row["stop_lon"]), float(row["stop_lat"])
    except (KeyError, ValueError):
        return False
    minlon, minlat, maxlon, maxlat = bbox
    return minlon <= lon <= maxlon and minlat <= lat <= maxlat


def _shape_point_in_bbox(row: GtfsRow, bbox: tuple[float, float, float, float]) -> bool:
    try:
        lon, lat = float(row["shape_pt_lon"]), float(row["shape_pt_lat"])
    except (KeyError, ValueError):
        return False
    minlon, minlat, maxlon, maxlat = bbox
    return minlon <= lon <= maxlon and minlat <= lat <= maxlat


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
