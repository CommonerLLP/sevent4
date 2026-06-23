from __future__ import annotations

import math
from itertools import combinations
from typing import Any, Iterable

from sevent4.ports.library_access import (
    CityLibraryComparison,
    CityLibraryComparisonInput,
    CityLibraryServiceDetailInput,
    CityLibrarySummary,
    CityLibrarySummaryInput,
    LIBRARY_COMPARISON_FIELDS,
    LIBRARY_SERVICE_DETAIL_FIELDS,
    SUMMARY_FIELDS,
)


EARTH_RADIUS_M = 6_371_000.0
DEFAULT_WALK_SPEED_KMPH = 4.8


def weighted_quantile(rows: Iterable[dict[str, Any]], value_key: str, weight_key: str, quantile: float) -> float:
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


def build_city_library_summary(input_data: CityLibrarySummaryInput) -> CityLibrarySummary:
    total = len(input_data.rows)
    mobile = sum(1 for row in input_data.rows if row.get("location_type") == "mobile_service_point")
    fixed = total - mobile if input_data.fixed_library_policy == "exclude_mobile_service_points" else total
    verified = sum(1 for row in input_data.rows if _present(row.get("latitude")) and _present(row.get("longitude")))
    pending = total - verified
    coverage = verified / total * 100 if total else 0.0
    access_status = input_data.complete_status if pending == 0 else input_data.pending_status
    return CityLibrarySummary(
        rows=[
            {
                "city": input_data.city,
                "source_path": input_data.source_path,
                "library_locations": str(total),
                "fixed_library_locations": str(fixed),
                "mobile_service_points": str(mobile),
                "coordinate_verified_locations": str(verified),
                "coordinate_pending_locations": str(pending),
                "coordinate_coverage_pct": f"{coverage:.1f}",
                "coordinate_coverage_status": "complete" if pending == 0 else "partial",
                "routing_tier": "not_computed",
                "access_status": access_status,
                "confidence": "high" if pending == 0 else "medium",
                "notes": input_data.notes,
            }
        ],
        fields=SUMMARY_FIELDS,
    )


def library_pair_key(city_a: str, city_b: str) -> str:
    return "_".join(sorted([city_a, city_b]))


def build_library_access_comparison(input_data: CityLibraryComparisonInput) -> CityLibraryComparison:
    rows: list[dict[str, str]] = []
    for city_a, city_b in combinations(input_data.cities, 2):
        summary_a = input_data.summaries.get(city_a)
        summary_b = input_data.summaries.get(city_b)
        status = "available" if summary_a and summary_b else "missing_city_summary"
        rows.append(
            {
                "pair": library_pair_key(city_a, city_b),
                "comparison_status": status,
                "city_a": city_a,
                "city_b": city_b,
                "city_a_library_locations": (summary_a or {}).get("library_locations", ""),
                "city_b_library_locations": (summary_b or {}).get("library_locations", ""),
                "city_a_access_status": (summary_a or {}).get("access_status", ""),
                "city_b_access_status": (summary_b or {}).get("access_status", ""),
                "notes": _comparison_notes(city_a, city_b, summary_a, summary_b),
            }
        )
    return CityLibraryComparison(rows=rows, fields=LIBRARY_COMPARISON_FIELDS)


def build_library_service_detail_audit(systems: Iterable[CityLibraryServiceDetailInput]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for system in systems:
        for field in ("max_seating_capacity", "opening_hours", "branch_collection_size", "collection_types"):
            count = system.values[field]
            rows.append(
                {
                    "city": system.city,
                    "library_system": system.library_system,
                    "detail_field": field,
                    "locations_with_value": count or "0",
                    "total_locations": system.total_locations,
                    "status": "missing_branchwise_public_detail",
                    "source_path": system.source_path,
                    "notes": "Branch-wise field not available in the current public extract; request from librarian/board or file RTI.",
                    "request_priority": "rti_or_request",
                }
            )
    return rows


def build_toronto_library_headline_rows(physical_branches: int, total_square_feet: float) -> list[dict[str, str]]:
    about = "https://tpl.ca/about-the-library/"
    finance = "https://tpl.ca/about-the-library/library-finance/"
    open_data = "https://tpl.ca/about-the-library/open-data/"
    rows = [
        ("2024", "network", "branches", physical_branches, "count", open_data, "high", "PhysicalBranch=1 rows in TPL branch general information open data."),
        ("2024", "network", "bookmobiles", 2, "count", about, "high", "TPL About page reports two bookmobiles."),
        ("2024", "network", "collection_items", 10_500_000, "count", about, "medium", "TPL About page reports more than 10.5 million items; stored as 10.5m lower-bound value."),
        ("2024", "network", "branch_square_feet", int(total_square_feet), "square_feet", open_data, "high", "Sum of SquareFootage in TPL branch general information open data."),
        ("2024", "usage", "total_visits_branch_and_online", 45_000_000, "count", about, "medium", "TPL About page reports nearly 45 million visits; stored as 45m rounded value."),
        ("2024", "usage", "branch_visits", 13_400_000, "count", about, "medium", "TPL About page reports 13.4 million branch visits."),
        ("2024", "usage", "online_visits", 31_500_000, "count", about, "medium", "TPL About page reports 31.5 million visits to online platforms."),
        ("2024", "usage", "borrowings", 28_000_000, "count", about, "medium", "TPL About page reports materials borrowed 28 million times."),
        ("2024", "usage", "card_registrations", 235_270, "count", about, "high", "TPL About page reports 235,270 people registered for a library card."),
        ("2024", "technology", "wireless_sessions", 6_000_000, "count", about, "medium", "TPL About page reports nearly six million wireless sessions."),
        ("2024", "technology", "public_computer_workstation_hours", 1_200_000, "hours", about, "medium", "TPL About page reports more than 1.2 million workstation session hours."),
        ("2024", "programs", "in_person_programs", 38_000, "count", about, "medium", "TPL About page reports over 38,000 in-person programs."),
        ("2024", "programs", "in_person_program_attendance", 750_000, "count", about, "medium", "TPL About page reports more than 750,000 in-person program participants."),
        ("2026", "finance", "gross_expenditure", 296_057_196, "CAD", finance, "high", "TPL 2026 operating budget reports gross expenditure."),
        ("2026", "finance", "staffing_salaries_benefits", 217_954_794, "CAD", finance, "high", "TPL 2026 gross expenditure split."),
        ("2026", "finance", "library_materials", 23_082_883, "CAD", finance, "high", "TPL 2026 gross expenditure split."),
        ("2026", "finance", "operations_administration", 55_019_519, "CAD", finance, "high", "TPL 2026 gross expenditure split."),
        ("2026", "finance", "city_funding_property_taxes", 274_378_001, "CAD", finance, "high", "TPL 2026 revenue split."),
        ("2026", "finance", "revenues_fines_fees", 4_298_350, "CAD", finance, "high", "TPL 2026 revenue split."),
        ("2026", "finance", "other_sources", 17_380_845, "CAD", finance, "high", "TPL 2026 revenue split."),
        ("2026", "capital", "capital_budget_total", 72_776_219, "CAD", finance, "high", "TPL 2026 capital budget funding sources."),
        ("2026", "capital", "capital_debt", 51_087_186, "CAD", finance, "high", "TPL 2026 capital budget funding sources."),
    ]
    return [
        {
            "year": str(year),
            "metric_group": group,
            "metric_name": name,
            "value": str(value),
            "unit": unit,
            "source_url": source,
            "confidence": confidence,
            "notes": notes,
        }
        for year, group, name, value, unit, source, confidence, notes in rows
    ]


def _comparison_notes(
    city_a: str,
    city_b: str,
    summary_a: dict[str, str] | None,
    summary_b: dict[str, str] | None,
) -> str:
    missing = [city for city, summary in [(city_a, summary_a), (city_b, summary_b)] if summary is None]
    if missing:
        return f"Missing library access summary for: {', '.join(missing)}."
    statuses = {summary_a.get("access_status", ""), summary_b.get("access_status", "")}
    if statuses - {"ready_for_population_origins"}:
        return "Location coverage comparison only; population-weighted travel-time comparison is not ready."
    return "Both city summaries are ready for population-origin travel-time modelling."


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _as_float(value: Any) -> float:
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return float(value)
