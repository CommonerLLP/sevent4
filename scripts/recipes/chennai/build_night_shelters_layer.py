#!/usr/bin/env python3
"""Build the Chennai night-shelters layer from the OpenCity/GCC facility register.

The register (data/cities/chennai/source/corporation/facilities/chennai_night_shelters.csv)
gives zone, ward, and address per shelter but no coordinates and no capacity
figures. Each shelter is placed at its own ward's centroid (this repo's
wards.geojson), matching the ward-centroid method already used for Kochi's
shelters.geojson when no street-level geocode is available.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import geopandas as gpd

REPO = Path(__file__).resolve().parents[3]
SOURCE_CSV = REPO / "data/cities/chennai/source/corporation/facilities/chennai_night_shelters.csv"
WARDS_GEOJSON = REPO / "data/cities/chennai/layers/wards.geojson"
OUT = REPO / "data/cities/chennai/layers/shelters.geojson"

SOURCE_URL = "https://data.opencity.in/dataset/chennai-civic-amenities/resource/4bcbb9cf-e9f6-47bd-b726-679703e71875"

NOTES = (
    "OpenCity/GCC Chennai Civic Amenities register gives zone, ward, and address "
    "only -- no coordinates and no capacity figures. Capacity is undisclosed here: "
    "GCC's own night-shelter dashboard login-gates per-shelter bed counts (the "
    "public aggregate reported elsewhere is 50 shelters citywide = 32 adult + 5 "
    "children + 13 special, not attributable to this specific site). Placed at "
    "this shelter's ward centroid (this repo's wards.geojson), not a street-level "
    "geocode."
)


def ward_centroids(wards_path: Path) -> dict[int, tuple[float, float, str]]:
    wards = gpd.read_file(wards_path)
    centroids: dict[int, tuple[float, float, str]] = {}
    for _, row in wards.iterrows():
        ward_no = int(row["ward_no"])
        point = row.geometry.centroid
        centroids[ward_no] = (point.x, point.y, str(row.get("zone_name") or ""))
    return centroids


def build_features(rows: list[dict[str, str]], centroids: dict[int, tuple[float, float, str]]) -> list[dict]:
    features = []
    skipped = []
    for row in rows:
        ward_no = int(row["Ward"])
        centroid = centroids.get(ward_no)
        if centroid is None:
            skipped.append(ward_no)
            continue
        lon, lat, zone_name = centroid
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "name": row["Location address of the shelter"].strip(),
                    "zone": zone_name or f"Zone {row['Zone']}",
                    "ward": f"Ward {ward_no}",
                    "capacity": None,
                    "day_service": None,
                    "shelter_type": row["Type of shelter"].strip(),
                    "source": SOURCE_URL,
                    "geocode_confidence": "approximate",
                    "notes": NOTES,
                },
            }
        )
    if skipped:
        print(f"WARNING: {len(skipped)} shelters skipped, ward not found in wards.geojson: {skipped}")
    return features


def main() -> None:
    with SOURCE_CSV.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    centroids = ward_centroids(WARDS_GEOJSON)
    features = build_features(rows, centroids)
    document = {"type": "FeatureCollection", "features": features}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(features)}/{len(rows)} Chennai night shelters -> {OUT}")


if __name__ == "__main__":
    main()
