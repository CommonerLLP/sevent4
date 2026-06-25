from __future__ import annotations

from dataclasses import dataclass

from sevent4.domain.library_exclusion import build_index, fnum, summarize


@dataclass
class LibraryExclusionResult:
    wards: dict
    exclusion_layer: dict
    indexed: list[dict]
    summary: dict
    meta: dict
    report_lines: list[str]


def build_library_exclusion(km_by_name: dict[str, float], wards: dict) -> LibraryExclusionResult:
    """Cross deprivation x library access at the ward level, enrich the ward
    polygons additively, build the focused exclusion atlas layer, and produce the
    summary + report lines. Pure transformation over plain dicts."""
    rows = [
        {
            "Name": feature["properties"]["Name"],
            "nearest_library_km": km_by_name[feature["properties"]["Name"]],
            "deprivation": fnum(feature["properties"].get("deprivation")),
            "population_2020": fnum(feature["properties"].get("population_2020")),
        }
        for feature in wards["features"]
    ]
    indexed, meta = build_index(rows)
    by_name = {r["Name"]: r for r in indexed}

    # additive write-back onto the ward features (new keys only)
    for feature in wards["features"]:
        record = by_name[feature["properties"]["Name"]]
        feature["properties"]["nearest_library_km"] = record["nearest_library_km"]
        feature["properties"]["exclusion_index"] = record["exclusion_index"]
        feature["properties"]["double_locked"] = record["double_locked"]

    features = []
    for feature in wards["features"]:
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
    exclusion_layer = {"type": "FeatureCollection", "crs": wards.get("crs"), "features": features}
    summary = summarize(indexed, meta)
    return LibraryExclusionResult(
        wards=wards,
        exclusion_layer=exclusion_layer,
        indexed=indexed,
        summary=summary,
        meta=meta,
        report_lines=_report_lines(indexed, summary, meta),
    )


def _report_lines(indexed: list[dict], summary: dict, meta: dict) -> list[str]:
    lines = [
        f"medians: deprivation {meta['median_deprivation']}, "
        f"nearest-library {meta['median_nearest_library_km']} km",
        f"double-locked: {summary['double_locked_ward_count']}/{summary['ward_count']} wards, "
        f"{summary['people_in_double_locked']:,} residents "
        f"({summary['pct_population_double_locked']}% of mapped population)\n",
        "DOUBLE-LOCKED WARDS (high deprivation AND far from a library), worst exclusion first:",
    ]
    locked = sorted(
        (r for r in indexed if r["double_locked"] == "True"),
        key=lambda r: -r["exclusion_index"],
    )
    for r in locked:
        lines.append(
            f"  excl {r['exclusion_index']:.3f}  dep {r['deprivation']:.3f}  "
            f"{r['nearest_library_km']:.2f} km  pop {r['population_2020']:>7,}  {r['Name']}"
        )
    return lines
