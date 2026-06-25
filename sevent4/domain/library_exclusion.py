"""Pure per-ward library-exclusion logic: normalisation, nearest-point distance,
population-weighted median, the deprivation x access cross, and the summary. No
filesystem or geospatial IO lives here (geopandas stays in the adapter).
"""
from __future__ import annotations

import math
import statistics

INDEX_FIELDS = [
    "Name",
    "nearest_library_km",
    "deprivation",
    "population_2020",
    "access_norm",
    "deprivation_norm",
    "exclusion_index",
    "double_locked",
]
SUMMARY_FIELDS = [
    "ward_count",
    "double_locked_ward_count",
    "people_in_double_locked",
    "total_population",
    "pct_population_double_locked",
    "pop_weighted_median_exclusion",
    "median_nearest_library_km",
    "median_deprivation",
]


def fnum(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def min_max_norm(values: list[float]) -> list[float]:
    """Scale to [0, 1]; a constant series maps to all-zeros (no spread)."""
    lo, hi = min(values), max(values)
    span = hi - lo
    return [(v - lo) / span if span else 0.0 for v in values]


def nearest_point_distance_m(cx: float, cy: float, points: list[tuple[float, float]]) -> float:
    """Min Euclidean distance (projected metres) from (cx, cy) to any point.

    In a metric CRS this equals centroid.distance(unary_union(points)).
    """
    return min(math.hypot(cx - px, cy - py) for px, py in points)


def weighted_median(values: list[float], weights: list[float]) -> float:
    """Population-weighted median of `values`."""
    pairs = sorted(zip(values, weights), key=lambda vw: vw[0])
    total = sum(w for _, w in pairs)
    if total <= 0:
        return 0.0
    cumulative = 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative >= total / 2:
            return value
    return pairs[-1][0]


def build_index(rows: list[dict]) -> tuple[list[dict], dict]:
    """Cross deprivation x access into a per-ward exclusion record.

    Each input row needs: Name, nearest_library_km (float), deprivation (float,
    already 0-1), population_2020 (float). Returns (enriched_rows, meta) where
    meta carries the median thresholds used for the quadrant split.
    """
    kms = [r["nearest_library_km"] for r in rows]
    deps = [r["deprivation"] for r in rows]
    access_norm = min_max_norm(kms)
    median_km = statistics.median(kms)
    median_dep = statistics.median(deps)

    enriched: list[dict] = []
    for row, a_norm in zip(rows, access_norm):
        dep = row["deprivation"]
        # deprivation is already on a 0-1 scale, so it doubles as its own norm.
        exclusion_index = 0.5 * dep + 0.5 * a_norm
        double_locked = dep >= median_dep and row["nearest_library_km"] >= median_km
        enriched.append(
            {
                "Name": row["Name"],
                "nearest_library_km": round(row["nearest_library_km"], 3),
                "deprivation": round(dep, 3),
                "population_2020": int(row["population_2020"]),
                "access_norm": round(a_norm, 3),
                "deprivation_norm": round(dep, 3),
                "exclusion_index": round(exclusion_index, 3),
                "double_locked": "True" if double_locked else "False",
            }
        )
    enriched.sort(key=lambda r: r["Name"])
    return enriched, {"median_nearest_library_km": round(median_km, 3), "median_deprivation": round(median_dep, 3)}


def summarize(rows: list[dict], meta: dict) -> dict:
    total_pop = sum(r["population_2020"] for r in rows)
    locked = [r for r in rows if r["double_locked"] == "True"]
    people_locked = sum(r["population_2020"] for r in locked)
    pop_weighted_median = weighted_median(
        [r["exclusion_index"] for r in rows],
        [float(r["population_2020"]) for r in rows],
    )
    return {
        "ward_count": len(rows),
        "double_locked_ward_count": len(locked),
        "people_in_double_locked": people_locked,
        "total_population": total_pop,
        "pct_population_double_locked": round(people_locked / total_pop * 100, 1) if total_pop else 0.0,
        "pop_weighted_median_exclusion": round(pop_weighted_median, 3),
        "median_nearest_library_km": meta["median_nearest_library_km"],
        "median_deprivation": meta["median_deprivation"],
    }
