from __future__ import annotations

import math
from typing import Any, Iterable


EARTH_RADIUS_M = 6_371_000.0
DEFAULT_WALK_SPEED_KMPH = 4.8


def weighted_quantile(rows: Iterable[dict[str, Any]], value_key: str, weight_key: str, quantile: float) -> float:
    """Return the weighted quantile value for row dictionaries."""
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between 0 and 1")

    pairs = sorted(
        (_as_float(row[value_key]), _as_float(row[weight_key]))
        for row in rows
        if _present(row.get(value_key)) and _present(row.get(weight_key))
    )
    if not pairs:
        raise ValueError("at least one value/weight pair is required")

    total_weight = sum(weight for _, weight in pairs)
    if total_weight <= 0:
        raise ValueError("total weight must be positive")
    if quantile == 0:
        return pairs[0][0]

    target = total_weight * quantile
    cumulative = 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative > target:
            return value
    return pairs[-1][0]


def threshold_share(rows: Iterable[dict[str, Any]], value_key: str, weight_key: str, threshold: float) -> float:
    """Return percent of weighted population whose value is within threshold."""
    values = [
        (_as_float(row[value_key]), _as_float(row[weight_key]))
        for row in rows
        if _present(row.get(value_key)) and _present(row.get(weight_key))
    ]
    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0:
        raise ValueError("total weight must be positive")

    included = sum(weight for value, weight in values if value <= threshold)
    return round(included / total_weight * 100.0, 6)


def haversine_m(lat1: float | str, lon1: float | str, lat2: float | str, lon2: float | str) -> float:
    """Great-circle distance in meters between two WGS84 coordinates."""
    phi1 = math.radians(_as_float(lat1))
    phi2 = math.radians(_as_float(lat2))
    d_phi = math.radians(_as_float(lat2) - _as_float(lat1))
    d_lambda = math.radians(_as_float(lon2) - _as_float(lon1))

    a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    return EARTH_RADIUS_M * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def nearest_library_access(
    origins: Iterable[dict[str, Any]],
    libraries: Iterable[dict[str, Any]],
    *,
    walk_speed_kmph: float = DEFAULT_WALK_SPEED_KMPH,
) -> list[dict[str, Any]]:
    """Calculate nearest-library walk access for each population origin."""
    library_rows = [row for row in libraries if _present(row.get("latitude")) and _present(row.get("longitude"))]
    if not library_rows:
        raise ValueError("at least one library with latitude/longitude is required")
    if walk_speed_kmph <= 0:
        raise ValueError("walk_speed_kmph must be positive")

    meters_per_minute = walk_speed_kmph * 1000.0 / 60.0
    output: list[dict[str, Any]] = []
    for origin in origins:
        origin_lat = origin.get("latitude")
        origin_lon = origin.get("longitude")
        if not _present(origin_lat) or not _present(origin_lon):
            raise ValueError(f"origin lacks latitude/longitude: {origin!r}")

        best_library = min(
            library_rows,
            key=lambda library: haversine_m(origin_lat, origin_lon, library["latitude"], library["longitude"]),
        )
        distance_m = haversine_m(origin_lat, origin_lon, best_library["latitude"], best_library["longitude"])
        output.append(
            {
                **origin,
                "nearest_library_id": best_library.get("library_id", best_library.get("id", "")),
                "nearest_library_name": best_library.get("name", ""),
                "distance_m_to_nearest_library": round(distance_m, 3),
                "walk_minutes_to_nearest_library": round(distance_m / meters_per_minute, 3),
            }
        )
    return output


def summarize_origin_access(rows: list[dict[str, Any]], *, value_key: str, weight_key: str) -> dict[str, float]:
    """Summarize population-weighted access rows."""
    return {
        "p50_minutes_to_nearest_library": weighted_quantile(rows, value_key, weight_key, 0.50),
        "p75_minutes_to_nearest_library": weighted_quantile(rows, value_key, weight_key, 0.75),
        "p90_minutes_to_nearest_library": weighted_quantile(rows, value_key, weight_key, 0.90),
        "pct_population_within_10_min": threshold_share(rows, value_key, weight_key, 10.0),
        "pct_population_within_15_min": threshold_share(rows, value_key, weight_key, 15.0),
        "pct_population_within_20_min": threshold_share(rows, value_key, weight_key, 20.0),
        "pct_population_within_30_min": threshold_share(rows, value_key, weight_key, 30.0),
        "pct_population_within_45_min": threshold_share(rows, value_key, weight_key, 45.0),
    }


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _as_float(value: Any) -> float:
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return float(value)
