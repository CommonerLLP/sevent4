"""Pure Chennai GCC finance parsing and zone-layer shaping."""
from __future__ import annotations

import re


DATASET_TITLE = "Great Chennai Corporation Finances"
VINTAGE = "2012-16 (latest GCC accounts on OpenCity; not current)"
ACTUALS_COL = "2013-14  Actuals"
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV"]


def num(value) -> float:
    try:
        return float(str(value or "").replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def safe_filename(value: str, fallback: str = "res") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", str(value or "").strip()).strip("_")
    return cleaned or fallback


def finance_resource_jobs(catalogue: dict) -> list[dict]:
    dataset = next(
        (row for row in catalogue.get("datasets", []) if row.get("title") == DATASET_TITLE),
        None,
    )
    if not dataset:
        raise ValueError("GCC Finances dataset not found in catalogue")
    jobs = []
    for index, resource in enumerate(dataset.get("resources", [])):
        resource_name = resource.get("name") or f"res_{index}"
        filename = f"{safe_filename(resource_name, f'res_{index}')}.csv"
        jobs.append(
            {
                "filename": filename,
                "url": resource["url"],
                "record": {
                    "resource_name": resource_name,
                    "filename": filename,
                    "url": resource["url"],
                },
            }
        )
    return jobs


def zone_roman(label: str) -> str | None:
    match = re.match(r"\s*Zone\s+([IVX]+)\b", str(label))
    return match.group(1) if match and match.group(1) in ROMAN else None


def normalise_zone_no(value) -> str:
    text = str(value or "").strip()
    if text in ROMAN:
        return text
    if text.isdigit() and 1 <= int(text) <= len(ROMAN):
        return ROMAN[int(text) - 1]
    return text


def build_zone_capex(resource_tables: list[tuple[str, object]]) -> dict[str, dict]:
    rows = next(
        (
            table
            for name, table in resource_tables
            if "Zones" in name and "1" in name and "Tools" not in name
        ),
        None,
    )
    if rows is None:
        raise ValueError("zone capex CSV not found")

    zones: dict[str, dict] = {}
    for row in rows:
        roman = zone_roman(row.get("Zone", ""))
        if not roman:
            continue
        zone = zones.setdefault(roman, {"capex": 0.0, "state_grant": 0.0, "heads": {}})
        value = num(row.get(ACTUALS_COL))
        zone["capex"] += value
        head = (row.get("Account Head") or "").strip()
        minor = (row.get("Minor Account") or "").strip()
        if re.search(r"GoTN|Specific Grants", head, re.I) or minor == "Specific Grants":
            zone["state_grant"] += value
        if head:
            zone["heads"][head] = zone["heads"].get(head, 0.0) + value
    return zones


def build_budget_summary(resource_tables: list[tuple[str, object]]) -> dict | None:
    rows = next((table for name, table in resource_tables if "summary" in name.lower()), None)
    if rows is None:
        return None
    lines = {}
    for row in rows:
        if len(row) < 5:
            continue
        key = str(row[1] or "").strip()
        if key and key.upper() != "PARTICULARS":
            lines[key] = num(row[4])
    return {"vintage": VINTAGE, "unit": "Rs lakh", "year": "2013-14 actuals", "lines": lines}


def build_zone_finance_feature_collection(zone_features: list[dict], zones: dict[str, dict]) -> dict:
    features = []
    for row in zone_features:
        zone_no = normalise_zone_no(row.get("zone_no"))
        zone = zones.get(zone_no, {})
        capex = round(zone.get("capex", 0.0), 1)
        state_grant = round(zone.get("state_grant", 0.0), 1)
        top_heads = sorted(zone.get("heads", {}).items(), key=lambda item: -item[1])[:4]
        features.append(
            {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {
                    "zone_no": zone_no,
                    "zone_name": row.get("zone_name") or zone_no,
                    "capex_lakh": capex,
                    "capex_cr": round(capex / 100, 2),
                    "state_grant_lakh": state_grant,
                    "state_grant_pct": round(state_grant / capex * 100) if capex else None,
                    "top_heads": [{"head": head, "lakh": round(value, 1)} for head, value in top_heads],
                    "vintage": VINTAGE,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def finance_sources_record() -> dict:
    return {
        "layer": "zone_finance",
        "publisher": "Greater Chennai Corporation",
        "portal": "data.opencity.in",
        "dataset": DATASET_TITLE,
        "dataset_url": "https://data.opencity.in/dataset/great-chennai-corporation-finances",
        "vintage": VINTAGE,
        "grain": "zone (15) - GCC publishes finance by zone, not ward",
        "processing": "sevent4: dissolve 200 wards -> 15 zones; join 2013-14 capex actuals; GoTN-grant share",
        "citation": "Greater Chennai Corporation -> data.opencity.in -> sevent4 (processed)",
    }
