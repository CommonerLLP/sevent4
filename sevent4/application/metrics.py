from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

import geopandas as gpd
import pandas as pd

from sevent4.ports.metrics import (
    ServiceAccessCompositeInput,
    ServiceAccessCompositeWriter,
    WardServiceAccessInput,
    WardServiceAccessWriter,
    WardTransitFrequencyInput,
    WardTransitFrequencyWriter,
)


SERVICE_COLUMNS = (
    "libraries",
    "schools",
    "health",
    "toilets",
    "police",
    "fire",
    "universities",
    "gtfs_stops",
)

OUTPUT_COLUMNS = [
    "Name",
    "ward_area_km2",
    "builtup_km2",
    "population_cells_proxy",
    *SERVICE_COLUMNS,
    "service_access",
    "service_gap",
    "service_priority",
]

SERVICE_COMPOSITE_COMPONENTS = ("libraries", "schools", "health", "buses_per_stop")
METERS_PER_DEGREE = 111_000.0


@dataclass(frozen=True)
class WardServiceAccessResult:
    rows: list[dict]


@dataclass(frozen=True)
class WardTransitFrequencyResult:
    document: dict
    summary: dict[str, object]


@dataclass(frozen=True)
class ServiceAccessCompositeResult:
    wards: dict
    acs: dict
    summary: dict[str, object]


def build_ward_service_access(
    inputs: WardServiceAccessInput,
    writer: WardServiceAccessWriter,
) -> WardServiceAccessResult:
    wards = inputs.wards[["Name", "geometry"]].copy().to_crs(inputs.crs_metric)
    wards["ward_area_km2"] = wards.geometry.area / 1e6

    for column in SERVICE_COLUMNS:
        points = inputs.service_points.get(column, _empty_points())
        _count_in_wards(wards, points.to_crs(inputs.crs_metric), column)

    _add_builtup_area(wards, inputs.builtup, inputs.crs_metric)
    _add_population_proxy(wards, inputs.population, inputs.crs_metric)

    population_proxy = wards["population_cells_proxy"].clip(lower=1)
    access_parts = []
    for service in ["libraries", "schools", "health", "gtfs_stops"]:
        access_parts.append(_norm(wards[service] / population_proxy))
    access = sum(access_parts) / len(access_parts)
    wards["service_access"] = access.round(3)
    wards["service_gap"] = (1 - access).round(3)
    wards["service_priority"] = (wards["service_gap"] * _norm(wards["population_cells_proxy"])).round(3)

    rows = (
        pd.DataFrame(wards.drop(columns="geometry"))[OUTPUT_COLUMNS]
        .sort_values("service_priority", ascending=False)
        .to_dict(orient="records")
    )
    writer.write_rows(rows)
    return WardServiceAccessResult(rows=rows)


def build_ward_transit_frequency(
    inputs: WardTransitFrequencyInput,
    writer: WardTransitFrequencyWriter,
) -> WardTransitFrequencyResult:
    document = _copy_feature_collection(inputs.wards)
    features = document["features"]
    if not features:
        summary = _empty_transit_frequency_summary(inputs.buffer_m)
        writer.write_wards(document)
        return WardTransitFrequencyResult(document=document, summary=summary)
    ward_rings, ward_bbox = _ward_geometry_index(features)
    coslat = math.cos(math.radians(sum(b[1] + b[3] for b in ward_bbox) / (2 * len(ward_bbox))))
    events = _gtfs_stop_events(inputs.gtfs_routes, inputs.gtfs_trips, inputs.gtfs_stop_times)
    stops = _gtfs_stops(inputs.gtfs_stops)

    strict_assign: dict[str, int] = {}
    unassigned: list[str] = []
    for stop_id in events:
        if stop_id not in stops:
            continue
        x, y = stops[stop_id]
        hit = None
        for ward_index, rings in enumerate(ward_rings):
            if _point_in_rings(x, y, rings):
                hit = ward_index
                break
        if hit is None:
            unassigned.append(stop_id)
        else:
            strict_assign[stop_id] = hit

    buckets = {"<250m": 0, "250m-1km": 0, "1-2.5km": 0, ">2.5km (left out)": 0}
    inclusive_assign = dict(strict_assign)
    reassigned_events = 0
    for stop_id in unassigned:
        x, y = stops[stop_id]
        ward_index, distance_m = _nearest_ward(
            x,
            y,
            ward_rings,
            ward_bbox,
            coslat,
            inputs.buffer_m,
        )
        if ward_index is None or distance_m is None or distance_m > inputs.buffer_m:
            buckets[">2.5km (left out)"] += 1
            continue
        inclusive_assign[stop_id] = ward_index
        reassigned_events += events[stop_id]["AMTS"]
        if distance_m < 250:
            buckets["<250m"] += 1
        elif distance_m < 1000:
            buckets["250m-1km"] += 1
        else:
            buckets["1-2.5km"] += 1

    strict_agg = _aggregate_transit(events, strict_assign)
    inclusive_agg = _aggregate_transit(events, inclusive_assign)
    buses_per_stop = []
    for ward_index, feature in enumerate(features):
        props = feature.setdefault("properties", {})
        inclusive = inclusive_agg.get(ward_index, {})
        strict = strict_agg.get(ward_index, {})
        amts_events = inclusive.get("amts_ev", 0)
        amts_stops = inclusive.get("amts_stops", 0)
        frequency = round(amts_events / amts_stops, 1) if amts_stops else 0.0
        props["amts_buses_day"] = amts_events
        props["amts_buses_day_core"] = strict.get("amts_ev", 0)
        props["amts_stops_freq"] = amts_stops
        props["buses_per_stop"] = frequency
        props["brts_stops"] = inclusive.get("brts_stops", 0)
        buses_per_stop.append(frequency)

    served = sorted(value for value in buses_per_stop if value > 0)
    first_quartile = served[len(served) // 4] if served else 0
    for feature in features:
        props = feature.setdefault("properties", {})
        props["transit_desert"] = bool(_float_value(props.get("buses_per_stop")) <= first_quartile)

    summary = {
        "service_stops": len(strict_assign) + len(unassigned),
        "strict_assigned_stops": len(strict_assign),
        "outside_ward_stops": len(unassigned),
        "reassigned_stops": len(unassigned) - buckets[">2.5km (left out)"],
        "reassigned_amts_events": reassigned_events,
        "distance_buckets": buckets,
        "buffer_m": inputs.buffer_m,
        "strict_correlations": _transit_correlations(features, strict_agg),
        "inclusive_correlations": _transit_correlations(features, inclusive_agg),
        "deprivation_quartiles": _deprivation_quartiles(features),
        "lowest_buses_per_stop": _lowest_buses_per_stop(features),
    }
    writer.write_wards(document)
    return WardTransitFrequencyResult(document=document, summary=summary)


def build_service_access_composite(
    inputs: ServiceAccessCompositeInput,
    writer: ServiceAccessCompositeWriter,
) -> ServiceAccessCompositeResult:
    wards = _copy_feature_collection(inputs.wards)
    acs = _copy_feature_collection(inputs.acs)
    features = wards["features"]
    if not features:
        summary = {
            "components": list(SERVICE_COMPOSITE_COMPONENTS),
            "wards_scored": 0,
            "acs_scored": 0,
            "ac_rankings": [],
            "worst_wards": [],
        }
        writer.write_documents(wards, acs)
        return ServiceAccessCompositeResult(wards=wards, acs=acs, summary=summary)

    columns = {
        component: [_float_value(feature.get("properties", {}).get(component)) for feature in features]
        for component in SERVICE_COMPOSITE_COMPONENTS
    }
    normalized = {component: _normalize_values(values) for component, values in columns.items()}
    ward_access: dict[str, float] = {}
    for index, feature in enumerate(features):
        props = feature.setdefault("properties", {})
        access = sum(normalized[component][index] for component in SERVICE_COMPOSITE_COMPONENTS) / len(
            SERVICE_COMPOSITE_COMPONENTS
        )
        props["composite_access"] = round(access, 3)
        props["composite_gap"] = round(1 - access, 3)
        name = props.get("Name")
        if name:
            ward_access[str(name)] = access

    ac_num: dict[str, float] = defaultdict(float)
    ac_den: dict[str, float] = defaultdict(float)
    ac_wards: dict[str, set[str]] = defaultdict(set)
    for record in inputs.crosswalk_records:
        ward_name = record.get("ward_name")
        ac_name = record.get("ac_name")
        if ward_name not in ward_access or not ac_name:
            continue
        area = _float_value(record.get("overlap_area_m2"))
        if area <= 0:
            continue
        ac_num[str(ac_name)] += ward_access[str(ward_name)] * area
        ac_den[str(ac_name)] += area
        ac_wards[str(ac_name)].add(str(ward_name))
    ac_access = {ac_name: ac_num[ac_name] / ac_den[ac_name] for ac_name in ac_num if ac_den[ac_name] > 0}

    written = 0
    for feature in acs["features"]:
        props = feature.setdefault("properties", {})
        ac_name = props.get("ac_name")
        if ac_name in ac_access:
            access = ac_access[str(ac_name)]
            props["ac_service_access"] = round(access, 3)
            props["ac_service_gap"] = round(1 - access, 3)
            props["ac_amc_wards"] = len(ac_wards[str(ac_name)])
            written += 1
        else:
            props["ac_service_gap"] = ""
            props["ac_amc_wards"] = 0

    summary = {
        "components": list(SERVICE_COMPOSITE_COMPONENTS),
        "wards_scored": len(ward_access),
        "acs_scored": written,
        "ac_rankings": _ac_service_rankings(acs, ac_access, ac_wards),
        "worst_wards": _worst_composite_gap(features),
    }
    writer.write_documents(wards, acs)
    return ServiceAccessCompositeResult(wards=wards, acs=acs, summary=summary)


def _add_builtup_area(wards: gpd.GeoDataFrame, builtup: gpd.GeoDataFrame | None, crs_metric: str) -> None:
    if builtup is None:
        wards["builtup_km2"] = 0.0
        return
    builtup = builtup.to_crs(crs_metric)
    builtup["geometry"] = builtup.geometry.buffer(0)
    centroids = builtup.copy()
    centroids["geometry"] = builtup.geometry.centroid
    centroids["area"] = builtup.geometry.area
    joined = gpd.sjoin(
        centroids[["area", "geometry"]],
        wards.reset_index()[["index", "geometry"]],
        predicate="within",
        how="inner",
    )
    area = joined.groupby("index")["area"].sum() / 1e6
    wards["builtup_km2"] = wards.index.map(area).fillna(0.0).round(2)


def _add_population_proxy(wards: gpd.GeoDataFrame, population: gpd.GeoDataFrame | None, crs_metric: str) -> None:
    if population is None:
        wards["population_cells_proxy"] = 1
        return
    population = population.to_crs(crs_metric)
    centroids = population.copy()
    centroids["geometry"] = population.geometry.centroid
    joined = gpd.sjoin(
        centroids[["geometry"]],
        wards.reset_index()[["index", "geometry"]],
        predicate="within",
        how="inner",
    )
    wards["population_cells_proxy"] = wards.index.map(joined.groupby("index").size()).fillna(0).astype(int)


def _count_in_wards(wards: gpd.GeoDataFrame, points: gpd.GeoDataFrame, column: str) -> None:
    if len(points) == 0:
        wards[column] = 0
        return
    joined = gpd.sjoin(points, wards.reset_index()[["index", "geometry"]], predicate="within", how="inner")
    counts = joined.groupby("index").size()
    wards[column] = wards.index.map(counts).fillna(0).astype(int)


def _norm(series: pd.Series) -> pd.Series:
    series = series.astype(float).fillna(0)
    span = series.max() - series.min()
    return (series - series.min()) / span if span > 0 else series * 0.0


def _empty_points() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(geometry=[], crs=4326)


def _copy_feature_collection(document: dict) -> dict:
    return {
        **document,
        "features": [
            {
                **feature,
                "properties": dict(feature.get("properties", {})),
                "geometry": feature.get("geometry"),
            }
            for feature in document.get("features", [])
        ],
    }


def _empty_transit_frequency_summary(buffer_m: float) -> dict[str, object]:
    return {
        "service_stops": 0,
        "strict_assigned_stops": 0,
        "outside_ward_stops": 0,
        "reassigned_stops": 0,
        "reassigned_amts_events": 0,
        "distance_buckets": {"<250m": 0, "250m-1km": 0, "1-2.5km": 0, ">2.5km (left out)": 0},
        "buffer_m": buffer_m,
        "strict_correlations": _zero_transit_correlations(),
        "inclusive_correlations": _zero_transit_correlations(),
        "deprivation_quartiles": [],
        "lowest_buses_per_stop": [],
    }


def _zero_transit_correlations() -> dict[str, float]:
    return {
        "deprivation_buses_pearson": 0.0,
        "deprivation_buses_spearman": 0.0,
        "deprivation_buses_per_stop_pearson": 0.0,
        "deprivation_buses_per_stop_spearman": 0.0,
    }


def _rings_of(geometry: dict):
    geometry_type = geometry["type"]
    if geometry_type == "Polygon":
        yield geometry["coordinates"][0]
    elif geometry_type == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            yield polygon[0]


def _ward_geometry_index(features: list[dict]):
    ward_rings = []
    ward_bbox = []
    for feature in features:
        ring_boxes = []
        all_x = []
        all_y = []
        for ring in _rings_of(feature["geometry"]):
            xs = [point[0] for point in ring]
            ys = [point[1] for point in ring]
            ring_boxes.append((ring, (min(xs), min(ys), max(xs), max(ys))))
            all_x.extend(xs)
            all_y.extend(ys)
        ward_rings.append(ring_boxes)
        ward_bbox.append((min(all_x), min(all_y), max(all_x), max(all_y)))
    return ward_rings, ward_bbox


def _point_in_rings(x: float, y: float, rings_with_bbox) -> bool:
    for ring, (x0, y0, x1, y1) in rings_with_bbox:
        if x < x0 or x > x1 or y < y0 or y > y1:
            continue
        inside = False
        previous = len(ring) - 1
        for index, point in enumerate(ring):
            xi, yi = point[0], point[1]
            xj, yj = ring[previous][0], ring[previous][1]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi):
                inside = not inside
            previous = index
        if inside:
            return True
    return False


def _nearest_ward(
    x: float,
    y: float,
    ward_rings,
    ward_bbox,
    coslat: float,
    buffer_m: float,
) -> tuple[int | None, float | None]:
    best_index = None
    best_distance_sq = None
    buffer_degrees = buffer_m / METERS_PER_DEGREE
    for ward_index, (x0, y0, x1, y1) in enumerate(ward_bbox):
        if x < x0 - buffer_degrees or x > x1 + buffer_degrees or y < y0 - buffer_degrees or y > y1 + buffer_degrees:
            continue
        for ring, _ in ward_rings[ward_index]:
            for point in ring:
                dx = (point[0] - x) * coslat
                dy = point[1] - y
                distance_sq = dx * dx + dy * dy
                if best_distance_sq is None or distance_sq < best_distance_sq:
                    best_distance_sq = distance_sq
                    best_index = ward_index
    if best_index is None or best_distance_sq is None:
        return None, None
    return best_index, math.sqrt(best_distance_sq) * METERS_PER_DEGREE


def _gtfs_stops(rows: list[dict[str, str]]) -> dict[str, tuple[float, float]]:
    stops = {}
    for row in rows:
        try:
            stops[row["stop_id"]] = (float(row["stop_lon"]), float(row["stop_lat"]))
        except (KeyError, TypeError, ValueError):
            continue
    return stops


def _gtfs_stop_events(
    routes: list[dict[str, str]],
    trips: list[dict[str, str]],
    stop_times: list[dict[str, str]],
) -> dict[str, dict[str, int]]:
    route_agency = {row.get("route_id", ""): row.get("agency_id", "?") for row in routes}
    trip_agency = {row.get("trip_id", ""): route_agency.get(row.get("route_id", ""), "?") for row in trips}
    events = defaultdict(lambda: {"AMTS": 0, "AJL": 0})
    for row in stop_times:
        agency = trip_agency.get(row.get("trip_id", ""), "?")
        stop_id = row.get("stop_id")
        if stop_id and agency in ("AMTS", "AJL"):
            events[stop_id][agency] += 1
    return events


def _aggregate_transit(events: dict[str, dict[str, int]], assignments: dict[str, int]) -> dict[int, dict[str, int]]:
    aggregate = defaultdict(lambda: defaultdict(int))
    for stop_id, event_counts in events.items():
        ward_index = assignments.get(stop_id)
        if ward_index is None:
            continue
        if event_counts["AMTS"]:
            aggregate[ward_index]["amts_ev"] += event_counts["AMTS"]
            aggregate[ward_index]["amts_stops"] += 1
        if event_counts["AJL"]:
            aggregate[ward_index]["brts_stops"] += 1
    return aggregate


def _transit_correlations(features: list[dict], aggregate: dict[int, dict[str, int]]) -> dict[str, float]:
    deprivation = []
    buses = []
    buses_per_stop = []
    for index, feature in enumerate(features):
        value = _optional_float(feature.get("properties", {}).get("deprivation"))
        if value is None:
            continue
        deprivation.append(value)
        record = aggregate.get(index, {})
        events = record.get("amts_ev", 0)
        stops = record.get("amts_stops", 0)
        buses.append(events)
        buses_per_stop.append(events / stops if stops else 0.0)
    return {
        "deprivation_buses_pearson": round(_pearson(deprivation, buses), 3),
        "deprivation_buses_spearman": round(_spearman(deprivation, buses), 3),
        "deprivation_buses_per_stop_pearson": round(_pearson(deprivation, buses_per_stop), 3),
        "deprivation_buses_per_stop_spearman": round(_spearman(deprivation, buses_per_stop), 3),
    }


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    variance_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    variance_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    return covariance / (variance_x * variance_y) if variance_x and variance_y else 0.0


def _spearman(xs: list[float], ys: list[float]) -> float:
    return _pearson(_ranks(xs), _ranks(ys))


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(values):
        tied = index
        while tied + 1 < len(values) and values[order[tied + 1]] == values[order[index]]:
            tied += 1
        average = (index + tied) / 2 + 1
        for rank_index in range(index, tied + 1):
            ranks[order[rank_index]] = average
        index = tied + 1
    return ranks


def _deprivation_quartiles(features: list[dict]) -> list[dict[str, float | str]]:
    paired = []
    for feature in features:
        props = feature.get("properties", {})
        deprivation = _optional_float(props.get("deprivation"))
        if deprivation is None:
            continue
        paired.append(
            (
                str(props.get("Name", "?")),
                deprivation,
                int(_float_value(props.get("amts_buses_day"))),
                _float_value(props.get("buses_per_stop")),
            )
        )
    by_deprivation = sorted(paired, key=lambda record: record[1])
    quartile_size = max(1, len(by_deprivation) // 4)
    rows = []
    for index, label in enumerate(["Q1", "Q2", "Q3", "Q4"]):
        chunk = (
            by_deprivation[index * quartile_size : (index + 1) * quartile_size]
            if index < 3
            else by_deprivation[3 * quartile_size :]
        )
        if not chunk:
            continue
        rows.append(
            {
                "quartile": label,
                "mean_buses_day": round(sum(record[2] for record in chunk) / len(chunk), 1),
                "mean_buses_per_stop": round(sum(record[3] for record in chunk) / len(chunk), 1),
            }
        )
    return rows


def _lowest_buses_per_stop(features: list[dict]) -> list[dict[str, object]]:
    rows = []
    for feature in features:
        props = feature.get("properties", {})
        rows.append(
            {
                "name": props.get("Name", "?"),
                "deprivation": _float_value(props.get("deprivation")),
                "amts_buses_day": int(_float_value(props.get("amts_buses_day"))),
                "buses_per_stop": _float_value(props.get("buses_per_stop")),
                "brts_stops": int(_float_value(props.get("brts_stops"))),
            }
        )
    return sorted(rows, key=lambda row: row["buses_per_stop"])[:6]


def _float_value(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _optional_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_values(values: list[float]) -> list[float]:
    low = min(values)
    high = max(values)
    span = high - low
    return [(value - low) / span if span else 0.0 for value in values]


def _ac_service_rankings(acs: dict, ac_access: dict[str, float], ac_wards: dict[str, set[str]]) -> list[dict[str, object]]:
    representatives = {
        feature.get("properties", {}).get("ac_name"): (
            feature.get("properties", {}).get("representative", "?"),
            feature.get("properties", {}).get("party", "?"),
        )
        for feature in acs.get("features", [])
    }
    rows = []
    for ac_name, access in sorted(ac_access.items(), key=lambda item: item[1]):
        representative, party = representatives.get(ac_name, ("?", "?"))
        rows.append(
            {
                "ac_name": ac_name,
                "service_gap": round(1 - access, 3),
                "amc_wards": len(ac_wards[ac_name]),
                "representative": representative,
                "party": party,
            }
        )
    return rows


def _worst_composite_gap(features: list[dict]) -> list[dict[str, object]]:
    rows = []
    for feature in features:
        props = feature.get("properties", {})
        rows.append(
            {
                "name": props.get("Name", "?"),
                "composite_gap": _float_value(props.get("composite_gap")),
                "libraries": props.get("libraries"),
                "schools": props.get("schools"),
                "health": props.get("health"),
                "buses_per_stop": props.get("buses_per_stop"),
                "deprivation": props.get("deprivation"),
            }
        )
    return sorted(rows, key=lambda row: -float(row["composite_gap"]))[:8]
