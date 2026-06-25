"""Pure feature and manifest shaping for Bengaluru four-axis ward analysis."""
from __future__ import annotations

import re


def nk(value: str) -> str:
    return re.sub(r"[^a-z]", "", str(value or "").lower())


def build_ward_analysis_feature_collection(rows: list[dict]) -> tuple[dict, list[tuple]]:
    features = []
    metrics = []
    for row in rows:
        props, metric_row = ward_analysis_properties(row)
        features.append({"type": "Feature", "properties": props, "geometry": row["geometry"]})
        metrics.append(metric_row)
    return {"type": "FeatureCollection", "features": features}, metrics


def ward_analysis_properties(row: dict) -> tuple[dict, tuple]:
    population = row.get("population") or 0
    sc_population = row.get("sc_population") or 0
    st_population = row.get("st_population") or 0
    ledger = row.get("ledger")
    spend = ledger["total_nett_cr"] if ledger else None
    top_contractor = ledger["top_contractors"][0] if ledger and ledger["top_contractors"] else None
    top_head = ledger["top_budget_heads"][0] if ledger and ledger["top_budget_heads"] else None
    works = "  •  ".join(f"{item['name'][:55]} — ₹{item['lakh']}L" for item in (ledger["flagged_works"][:4] if ledger else []))
    sc_share = round(100 * sc_population / population, 1) if population else None
    st_share = round(100 * st_population / population, 1) if population else None
    spend_per_capita = round(spend * 1e7 / population) if (spend and population) else None
    props = {
        "Ward": row["ward"],
        "population": int(population) if population else None,
        "sc_share_pct": sc_share,
        "st_share_pct": st_share,
        "sc_st_share_pct": round((sc_share or 0) + (st_share or 0), 1) if sc_share is not None else None,
        "assembly": row.get("assembly") or "",
        "parliament": row.get("parliament") or "",
        "works_spend_cr": spend,
        "spend_per_resident_rs": spend_per_capita,
        "top_contractor": f"{top_contractor['name'][:28]} (₹{top_contractor['cr']}cr)" if top_contractor else "—",
        "top_budget_head": f"{top_head['head'][:46]} (₹{top_head['cr']}cr)" if top_head else "—",
        "flagged_works": works or "—",
        "mean_lst_c": row.get("mean_lst_c"),
        "max_lst_c": row.get("max_lst_c"),
    }
    return props, (sc_share, st_share, spend, spend_per_capita, props["mean_lst_c"])


def correlation(first: list, second: list) -> tuple[float | None, int]:
    points = [(x, y) for x, y in zip(first, second) if x is not None and y is not None]
    if len(points) < 5:
        return None, len(points)
    count = len(points)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    mean_x = sum(xs) / count
    mean_y = sum(ys) / count
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in points)
    variance_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    variance_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    return (round(covariance / (variance_x * variance_y), 3) if variance_x and variance_y else None), count


def correlation_rows(metrics: list[tuple]) -> list[tuple[str, float | None, int]]:
    sc = [row[0] for row in metrics]
    spend = [row[2] for row in metrics]
    spend_per_capita = [row[3] for row in metrics]
    lst = [row[4] for row in metrics]
    pairs = [
        ("SC/ST share  ×  works spend (₹cr)", sc, spend),
        ("SC/ST share  ×  spend per resident", sc, spend_per_capita),
        ("SC/ST share  ×  surface temp (LST)", sc, lst),
        ("surface temp ×  works spend (₹cr)", lst, spend),
        ("surface temp ×  spend per resident", lst, spend_per_capita),
    ]
    return [(label, *correlation(left, right)) for label, left, right in pairs]


def patch_ward_analysis_manifest(manifest: dict) -> dict:
    layers = [layer for layer in manifest.get("layers", []) if layer["id"] != "ward_analysis"]
    layers.insert(0, {
        "id": "ward_analysis",
        "label": "Four-axis ward analysis (caste·spend·heat·rep)",
        "file": "ward_analysis.geojson",
        "kind": "fill",
        "group": "Four-axis",
        "default": False,
        "outline": True,
        "popup": ["Ward", "population", "sc_st_share_pct", "assembly", "parliament",
                  "works_spend_cr", "spend_per_resident_rs", "mean_lst_c",
                  "top_contractor", "top_budget_head", "flagged_works"],
        "paint": {"fill-color": ["interpolate", ["linear"], ["to-number", ["get", "sc_st_share_pct"], 0],
                                 0, "#f7f4ea", 15, "#d9a94f", 30, "#c84646", 50, "#7a1f1f"],
                  "fill-opacity": 0.62},
    })
    return {**manifest, "layers": layers}
