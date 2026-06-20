#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "data" / "cities" / "delhi" / "source" / "libraries" / "dpl_library_locations.csv"
GEOCODED = REPO / "data" / "cities" / "delhi" / "derived" / "geocoding" / "dpl_geocoded.csv"
OUT_DIR = REPO / "data" / "cities" / "delhi" / "derived" / "library_access"
DETAIL_OUT = OUT_DIR / "dpl_service_hierarchy.csv"
SUMMARY_OUT = OUT_DIR / "dpl_service_hierarchy_summary.csv"

DETAIL_FIELDS = [
    "library_id",
    "name",
    "service_tier",
    "source_location_type",
    "hierarchy_rank",
    "physical_access_model",
    "zone",
    "address",
    "latitude",
    "longitude",
    "coordinate_status",
    "coordinate_provenance_group",
    "geocode_confidence",
    "geocode_provider",
    "max_seating_capacity",
    "opening_hours",
    "weekly_open_hours",
    "branch_collection_size",
    "collection_types",
    "branch_detail_status",
    "usable_for_internal_access_model",
    "usable_for_public_open_dataset",
    "notes",
]

SUMMARY_FIELDS = [
    "total_locations",
    "fixed_physical_locations",
    "mobile_service_points",
    "headquarters",
    "zonal_libraries",
    "branch_libraries",
    "special_fixed_libraries",
    "sub_branch_libraries",
    "community_libraries",
    "internal_geocoded_locations",
    "public_provenance_coordinates",
    "google_geocode_coordinates",
    "branchwise_seating_capacity_locations",
    "branchwise_opening_hours_locations",
    "branchwise_collection_size_locations",
    "branchwise_collection_type_locations",
    "access_model_status",
    "notes",
]

TIER_RANK = {
    "headquarters": 10,
    "zonal_library": 20,
    "branch_library": 30,
    "special_fixed_library": 35,
    "sub_branch_library": 40,
    "community_library": 50,
    "mobile_service_point": 60,
    "other": 90,
}


def main() -> None:
    source_rows = read_csv(SOURCE)
    geocoded_rows = read_csv(GEOCODED) if GEOCODED.exists() else []
    detail_rows = hierarchy_rows(source_rows, geocoded_rows)
    summary = summarize_hierarchy(detail_rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(DETAIL_OUT, detail_rows, DETAIL_FIELDS)
    write_csv(SUMMARY_OUT, [summary], SUMMARY_FIELDS)
    print(f"wrote {DETAIL_OUT.relative_to(REPO)} ({len(detail_rows)} rows)")
    print(f"wrote {SUMMARY_OUT.relative_to(REPO)}")


def hierarchy_rows(source_rows: list[dict[str, str]], geocoded_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    geocoded_by_id = {row["library_id"]: row for row in geocoded_rows if row.get("library_id")}
    rows: list[dict[str, str]] = []
    for source in source_rows:
        geo = geocoded_by_id.get(source.get("library_id", ""), {})
        tier = classify_service_tier(source)
        lat = value(geo, "latitude") or value(source, "latitude")
        lon = value(geo, "longitude") or value(source, "longitude")
        geocode_confidence = value(geo, "geocode_confidence") or source.get("geocode_status", "")
        geocode_provider = value(geo, "geocode_provider") or source.get("coordinate_source", "")
        provenance = coordinate_provenance_group(geocode_confidence, geocode_provider)
        public_ok = "yes" if provenance in {"source_or_dpl_map", "open_or_manual"} else "no"
        internal_ok = "yes" if lat and lon else "no"
        rows.append(
            {
                "library_id": source.get("library_id", ""),
                "name": source.get("name", ""),
                "service_tier": tier,
                "source_location_type": source.get("location_type", ""),
                "hierarchy_rank": str(TIER_RANK.get(tier, TIER_RANK["other"])),
                "physical_access_model": physical_access_model(tier),
                "zone": source.get("zone", ""),
                "address": source.get("address", ""),
                "latitude": lat,
                "longitude": lon,
                "coordinate_status": "located" if lat and lon else "missing_coordinates",
                "coordinate_provenance_group": provenance,
                "geocode_confidence": geocode_confidence,
                "geocode_provider": geocode_provider,
                "max_seating_capacity": "",
                "opening_hours": "",
                "weekly_open_hours": "",
                "branch_collection_size": "",
                "collection_types": "",
                "branch_detail_status": "missing_branchwise_public_detail",
                "usable_for_internal_access_model": internal_ok,
                "usable_for_public_open_dataset": public_ok,
                "notes": notes_for_row(tier, provenance),
            }
        )
    return sorted(rows, key=lambda row: (int(row["hierarchy_rank"]), row["zone"], row["name"]))


def classify_service_tier(row: dict[str, str]) -> str:
    name = row.get("name", "").lower()
    location_type = row.get("location_type", "")
    if "head quarter" in name or "headquarter" in name:
        return "headquarters"
    if location_type == "zonal_library":
        return "zonal_library"
    if location_type == "sub_branch_library":
        return "sub_branch_library"
    if location_type == "community_library":
        return "community_library"
    if location_type == "mobile_service_point":
        return "mobile_service_point"
    if location_type == "fixed_library":
        if "braille" in name:
            return "special_fixed_library"
        return "branch_library"
    return "other"


def physical_access_model(tier: str) -> str:
    if tier == "mobile_service_point":
        return "scheduled_mobile_stop"
    if tier in {"headquarters", "zonal_library", "branch_library", "special_fixed_library"}:
        return "fixed_full_service"
    if tier in {"sub_branch_library", "community_library"}:
        return "fixed_local_service"
    return "unknown"


def coordinate_provenance_group(confidence: str, provider: str) -> str:
    combined = f"{confidence} {provider}".lower()
    if not combined.strip():
        return "missing"
    if "dpl_maps_pin" in combined:
        return "source_or_dpl_map"
    # google_maps_embed / google_maps_url coordinates are Google-derived: the source
    # policy forbids storing them in a public open dataset, so they are NOT public-usable.
    if "google" in combined:
        return "google_geocode"
    if "nominatim" in combined or "manual" in combined or "osm" in combined:
        return "open_or_manual"
    if "verified" in combined:
        return "source_or_dpl_map"
    return "other"


def summarize_hierarchy(rows: list[dict[str, str]]) -> dict[str, str]:
    tiers = Counter(row["service_tier"] for row in rows)
    provenance = Counter(row["coordinate_provenance_group"] for row in rows)
    fixed = sum(1 for row in rows if row["physical_access_model"].startswith("fixed_"))
    internal_located = sum(1 for row in rows if row["usable_for_internal_access_model"] == "yes")
    public_located = sum(1 for row in rows if row["usable_for_public_open_dataset"] == "yes")
    return {
        "total_locations": str(len(rows)),
        "fixed_physical_locations": str(fixed),
        "mobile_service_points": str(tiers["mobile_service_point"]),
        "headquarters": str(tiers["headquarters"]),
        "zonal_libraries": str(tiers["zonal_library"]),
        "branch_libraries": str(tiers["branch_library"]),
        "special_fixed_libraries": str(tiers["special_fixed_library"]),
        "sub_branch_libraries": str(tiers["sub_branch_library"]),
        "community_libraries": str(tiers["community_library"]),
        "internal_geocoded_locations": str(internal_located),
        "public_provenance_coordinates": str(public_located),
        "google_geocode_coordinates": str(provenance["google_geocode"]),
        "branchwise_seating_capacity_locations": str(count_present(rows, "max_seating_capacity")),
        "branchwise_opening_hours_locations": str(count_present(rows, "opening_hours")),
        "branchwise_collection_size_locations": str(count_present(rows, "branch_collection_size")),
        "branchwise_collection_type_locations": str(count_present(rows, "collection_types")),
        "access_model_status": "internal_full_geocode" if internal_located == len(rows) else "partial_geocode",
        "notes": (
            "DPL is a hierarchy, not a flat point set: headquarters, zonal libraries, branch/special "
            "fixed libraries, sub-branches, one community library, and scheduled mobile service points. "
            "Google-derived coordinates are accepted for internal modelling here and must be flagged before publication. "
            "Branch-wise max seating capacity, opening hours, collection size, and collection-type fields are not "
            "available in the current public extract and must be acquired or flagged as undisclosed."
        ),
    }


def notes_for_row(tier: str, provenance: str) -> str:
    tier_note = {
        "headquarters": "Central DPL administrative/full-service location.",
        "zonal_library": "Fixed zonal library; higher-order DPL public service point.",
        "branch_library": "Fixed branch-like public service point parsed from DPL zone pages.",
        "special_fixed_library": "Fixed special-service library parsed from DPL zone pages.",
        "sub_branch_library": "Fixed local sub-branch parsed from DPL zone pages.",
        "community_library": "Fixed community library parsed from DPL zone pages.",
        "mobile_service_point": "Scheduled mobile-library stop; not equivalent to a permanent branch.",
    }.get(tier, "DPL location parsed from source.")
    if provenance == "google_geocode":
        return f"{tier_note} Coordinates are Google-geocoded and are internal-use until independently verified."
    return tier_note


def value(row: dict[str, str], key: str) -> str:
    raw = row.get(key, "")
    if raw is None:
        return ""
    text = str(raw)
    return "" if text.lower() == "nan" else text


def count_present(rows: list[dict[str, str]], key: str) -> int:
    return sum(1 for row in rows if row.get(key, "").strip())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
