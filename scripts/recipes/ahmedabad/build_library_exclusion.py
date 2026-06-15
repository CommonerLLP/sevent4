#!/usr/bin/env python3
"""Per-ward library exclusion cross for Ahmedabad.

The paper documents two exclusion mechanisms separately — administrative
gatekeeping (Aadhaar / guarantor / deposit) and spatial library deserts — but
never crosses them. This recipe runs that cross at the ward level.

Two axes, both already on wards.geojson:
  * deprivation (0-1, already ward-resolved)
  * nearest_library_km, computed SPATIALLY from the 83-point library inventory
    (centroid -> nearest library point, EPSG:32643). The precomputed
    `library_desert` field is the string 'True' for all 48 wards and is unusable,
    so access is recomputed here the way make_ahmedabad_library_paper_figures.py
    does.

The headline is the DOUBLE-LOCKED quadrant: wards above the median on BOTH axes
(high deprivation AND far from a library), reported with the count of wards and
the total population affected. `exclusion_index` (equal-weight average of the two
normalized axes) is only the choropleth fill value — the claim rests on the
quadrant, not the scalar.

Writes:
  * data/cities/ahmedabad/derived/library_access/library_exclusion_index.csv
  * data/cities/ahmedabad/derived/library_access/library_exclusion_summary.csv
  * data/cities/ahmedabad/layers/ward_library_exclusion.geojson  (atlas layer)
  * additive keys (exclusion_index, nearest_library_km, double_locked) onto
    wards.geojson — new keys only, existing properties untouched.

    .venv/bin/python scripts/recipes/ahmedabad/build_library_exclusion.py
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LAYERS = REPO / "data" / "cities" / "ahmedabad" / "layers"
WARDS = LAYERS / "wards.geojson"
EXCL_GEOJSON = LAYERS / "ward_library_exclusion.geojson"
LIB_CSV = REPO / "data" / "cities" / "ahmedabad" / "source" / "libraries" / "ahmedabad_library_locations.csv"
OUT_DIR = REPO / "data" / "cities" / "ahmedabad" / "derived" / "library_access"

WGS84 = "EPSG:4326"
METRIC = "EPSG:32643"

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


# ---------------------------------------------------------------------------
# pure functions (importable, geopandas-free) — covered by tests
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# spatial layer (geopandas) — thin wrapper over the pure helpers
# ---------------------------------------------------------------------------
def compute_nearest_library_km() -> dict[str, float]:
    """Return {ward Name: nearest-library km} via a metric-CRS spatial join."""
    import geopandas as gpd
    import pandas as pd

    wards = gpd.read_file(WARDS).to_crs(METRIC)
    raw = pd.read_csv(LIB_CSV)
    libraries = gpd.GeoDataFrame(
        raw,
        geometry=gpd.points_from_xy(raw["longitude"], raw["latitude"]),
        crs=WGS84,
    ).to_crs(METRIC)
    points = [(geom.x, geom.y) for geom in libraries.geometry]
    out: dict[str, float] = {}
    for _, ward in wards.iterrows():
        centroid = ward.geometry.centroid
        out[ward["Name"]] = nearest_point_distance_m(centroid.x, centroid.y, points) / 1000.0
    return out


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    km_by_name = compute_nearest_library_km()

    gj = json.loads(WARDS.read_text())
    rows = [
        {
            "Name": f["properties"]["Name"],
            "nearest_library_km": km_by_name[f["properties"]["Name"]],
            "deprivation": fnum(f["properties"].get("deprivation")),
            "population_2020": fnum(f["properties"].get("population_2020")),
        }
        for f in gj["features"]
    ]
    indexed, meta = build_index(rows)
    by_name = {r["Name"]: r for r in indexed}

    # additive write-back onto wards.geojson (new keys only)
    for feature in gj["features"]:
        record = by_name[feature["properties"]["Name"]]
        feature["properties"]["nearest_library_km"] = record["nearest_library_km"]
        feature["properties"]["exclusion_index"] = record["exclusion_index"]
        feature["properties"]["double_locked"] = record["double_locked"]
    WARDS.write_text(json.dumps(gj, ensure_ascii=False))

    # dedicated atlas layer — geometry + focused index properties
    features = []
    for feature in gj["features"]:
        record = by_name[feature["properties"]["Name"]]
        features.append(
            {
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": {
                    "Name": record["Name"],
                    "exclusion_index": record["exclusion_index"],
                    "nearest_library_km": record["nearest_library_km"],
                    "deprivation": record["deprivation"],
                    "deprivation_norm": record["deprivation_norm"],
                    "access_norm": record["access_norm"],
                    "population_2020": record["population_2020"],
                    "double_locked": record["double_locked"],
                },
            }
        )
    exclusion_layer = {"type": "FeatureCollection", "crs": gj.get("crs"), "features": features}
    EXCL_GEOJSON.write_text(json.dumps(exclusion_layer, ensure_ascii=False))

    # derived tables
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_DIR / "library_exclusion_index.csv", indexed, INDEX_FIELDS)
    summary = summarize(indexed, meta)
    write_csv(OUT_DIR / "library_exclusion_summary.csv", [summary], SUMMARY_FIELDS)

    # report
    print(
        f"medians: deprivation {meta['median_deprivation']}, "
        f"nearest-library {meta['median_nearest_library_km']} km"
    )
    print(
        f"double-locked: {summary['double_locked_ward_count']}/{summary['ward_count']} wards, "
        f"{summary['people_in_double_locked']:,} residents "
        f"({summary['pct_population_double_locked']}% of mapped population)\n"
    )
    print("DOUBLE-LOCKED WARDS (high deprivation AND far from a library), worst exclusion first:")
    locked = sorted(
        (r for r in indexed if r["double_locked"] == "True"),
        key=lambda r: -r["exclusion_index"],
    )
    for r in locked:
        print(
            f"  excl {r['exclusion_index']:.3f}  dep {r['deprivation']:.3f}  "
            f"{r['nearest_library_km']:.2f} km  pop {r['population_2020']:>7,}  {r['Name']}"
        )
    print(f"\nwrote {OUT_DIR / 'library_exclusion_index.csv'} ({len(indexed)} wards)")
    print(f"wrote {EXCL_GEOJSON.relative_to(REPO)}")


if __name__ == "__main__":
    main()
