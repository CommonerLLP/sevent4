"""Pure Bengaluru work-order finance aggregation and layer shaping."""
from __future__ import annotations

import re
from collections import Counter
from copy import deepcopy
from datetime import datetime


def num(value) -> int:
    digits = re.sub(r"[^0-9]", "", str(value or ""))
    return int(digits) if digits else 0


def nk(value: str) -> str:
    return re.sub(r"[^a-z]", "", str(value or "").lower())


def norm_ward(value: str) -> tuple[str, str]:
    value = (value or "").strip()
    match = re.match(r"^0*(\d+)\s+(.*?)(?:\s+ward)?\s*$", value, re.I)
    if match:
        return match.group(1), nk(match.group(2))
    return "", nk(value)


def ward_from_filename(path: str) -> tuple[str, str]:
    stem = str(path).rsplit("/", 1)[-1].rsplit(".", 1)[0]
    match = re.search(r"Work_Orders_for_(.+?)_Num-(\d+)_Ward", stem)
    if match:
        return match.group(2), match.group(1).replace("_", " ").strip()
    return "", stem


def order_year(row: dict) -> int | None:
    for key in ("Order Date", "Start Date"):
        value = str(row.get(key) or "").strip()
        if not value:
            continue
        for fmt in ("%d-%b-%Y", "%d-%b-%y", "%d-%B-%Y", "%d-%B-%y", "%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(value.title(), fmt).year
            except ValueError:
                pass
    return None


def build_finance_tables(
    file_rows: list[tuple[str, list[dict]]],
    min_year: int = 2013,
    max_year: int = 2022,
) -> tuple[list[dict], list[dict]]:
    cumulative: dict[str, dict] = {}
    yearly: dict[tuple[str, int], dict] = {}
    for filename, rows in file_rows:
        ward_num, ward_name = ward_from_filename(filename)
        base_key = ward_num or nk(ward_name)
        if not base_key:
            continue
        ward = cumulative.setdefault(base_key, empty_ward(ward_num, ward_name))
        for row in rows:
            add_workorder(ward, row)
            year = order_year(row)
            if year is None or year < min_year or year > max_year:
                continue
            add_workorder(yearly.setdefault((base_key, year), empty_ward(ward_num, ward_name)), row)

    cumulative_rows = [finalise_workorder(row) for row in cumulative.values()]
    cumulative_rows.sort(key=lambda row: -row["total_nett_cr"])
    yearly_rows = [finalise_workorder(row, year) for (_, year), row in yearly.items()]
    yearly_rows.sort(key=lambda row: (row["year"], -row["total_nett_cr"]))
    return cumulative_rows, yearly_rows


def build_yearly_table(
    file_rows: list[tuple[str, list[dict]]],
    min_year: int = 2013,
    max_year: int = 2022,
) -> list[dict]:
    return build_finance_tables(file_rows, min_year, max_year)[1]


def empty_ward(ward_num: str, ward_name: str) -> dict:
    return {
        "ward_num": ward_num,
        "ward_name": f"{int(ward_num):03d} {ward_name}" if ward_num.isdigit() else ward_name,
        "total_nett": 0,
        "count": 0,
        "contractors": Counter(),
        "heads": Counter(),
        "works": [],
    }


def add_workorder(ward: dict, row: dict) -> None:
    nett = num(row.get("Nett"))
    ward["total_nett"] += nett
    ward["count"] += 1
    contractor = (row.get("Contractor") or "").strip()
    if contractor:
        ward["contractors"][contractor] += nett
    head = (row.get("Budget Head") or "").strip()
    if head:
        ward["heads"][head[:70]] += nett
    name = (row.get("Name of Work") or "").strip()
    if name and nett > 0:
        ward["works"].append((nett, name, contractor, head[:40]))


def finalise_workorder(ward: dict, year: int | None = None) -> dict:
    works = sorted(ward["works"], reverse=True)[:8]
    row = {
        "ward_num": ward["ward_num"],
        "ward_name": ward["ward_name"],
        "total_nett_cr": round(ward["total_nett"] / 1e7, 2),
        "work_count": ward["count"],
        "top_contractors": [
            {"name": contractor, "cr": round(value / 1e7, 2)}
            for contractor, value in ward["contractors"].most_common(3)
        ],
        "top_budget_heads": [
            {"head": head, "cr": round(value / 1e7, 2)}
            for head, value in ward["heads"].most_common(3)
        ],
        "flagged_works": [
            {"name": name, "contractor": contractor, "head": head, "lakh": round(value / 1e5)}
            for value, name, contractor, head in works
        ],
    }
    if year is not None:
        row["year"] = year
    return row


def boundary_name_keys(boundary: dict) -> dict[str, str]:
    keys = {}
    for feature in boundary.get("features", []):
        properties = feature.get("properties", {})
        name = properties.get("name_en") or properties.get("proposed_ward_name_en") or properties.get("Name") or ""
        keys[nk(str(name))] = name
    return keys


def matched_ledger_count(ledger_rows: list[dict], boundary: dict) -> int:
    keys = boundary_name_keys(boundary)
    return sum(1 for row in ledger_rows if nk(row["ward_name"].split(" ", 1)[-1].replace("Ward", "")) in keys)


def ledger_key(record: dict) -> str:
    return nk(str(record["ward_name"]).split(" ", 1)[-1])


def ward_label(properties: dict) -> str:
    return (
        properties.get("name_en")
        or properties.get("proposed_ward_name_en")
        or properties.get("Name")
        or properties.get("Ward")
        or ""
    )


def work_text(works: list[dict]) -> str:
    return "  •  ".join(
        f"{item['name'][:60]} — ₹{item['lakh']}L ({item['contractor'][:24]})"
        for item in works[:5]
    ) or "—"


def build_cumulative_geojson(boundary: dict, ledger_records: list[dict]) -> tuple[dict, int]:
    ledger = {ledger_key(row): row for row in ledger_records}
    output = deepcopy(boundary)
    matched = 0
    for feature in output["features"]:
        properties = feature["properties"]
        name = ward_label(properties)
        row = ledger.get(nk(name))
        keep = {"Ward": name}
        if row:
            matched += 1
            contractor = row["top_contractors"][0] if row["top_contractors"] else None
            head = row["top_budget_heads"][0] if row["top_budget_heads"] else None
            keep.update(
                {
                    "works_spend_cr": row["total_nett_cr"],
                    "work_count": row["work_count"],
                    "top_contractor": f"{contractor['name'][:30]} (₹{contractor['cr']} cr)" if contractor else "—",
                    "top_budget_head": f"{head['head'][:50]} (₹{head['cr']} cr)" if head else "—",
                    "flagged_works": work_text(row["flagged_works"]),
                    "note_74a": "BBMP work orders 2013-22; budget head shows which discretionary pocket paid.",
                }
            )
        else:
            keep.update(
                {
                    "works_spend_cr": None,
                    "work_count": None,
                    "flagged_works": "(ward not matched to 2013-22 ledger — vintage gap)",
                }
            )
        feature["properties"] = keep
    return output, matched


def build_yearly_geojson(boundary: dict, yearly_records: list[dict], years: list[int]) -> dict:
    ledger = {(ledger_key(row), int(row["year"])): row for row in yearly_records}
    features = []
    for feature in boundary["features"]:
        name = ward_label(feature["properties"])
        key = nk(name)
        for year in years:
            output = deepcopy(feature)
            row = ledger.get((key, year))
            keep = {"Ward": name, "year": year}
            if row:
                contractor = row["top_contractors"][0] if row["top_contractors"] else None
                head = row["top_budget_heads"][0] if row["top_budget_heads"] else None
                keep.update(
                    {
                        "works_spend_cr": row["total_nett_cr"],
                        "work_count": row["work_count"],
                        "top_contractor": f"{contractor['name'][:30]} (₹{contractor['cr']} cr)" if contractor else "—",
                        "top_budget_head": f"{head['head'][:50]} (₹{head['cr']} cr)" if head else "—",
                        "flagged_works": work_text(row["flagged_works"]),
                        "note_74a": "BBMP work orders by Order Date year; cumulative layer is separate.",
                    }
                )
            else:
                keep.update(
                    {
                        "works_spend_cr": None,
                        "work_count": None,
                        "top_contractor": "—",
                        "top_budget_head": "—",
                        "flagged_works": "(no matched work orders for this ward/year)",
                        "note_74a": "BBMP work orders by Order Date year; cumulative layer is separate.",
                    }
                )
            output["properties"] = keep
            features.append(output)
    return {"type": "FeatureCollection", "features": features}


def patch_finance_manifest(manifest: dict, years: list[int]) -> dict:
    output = deepcopy(manifest)
    output["layers"] = [
        layer for layer in output["layers"]
        if layer["id"] not in {"ward_workorders", "ward_workorders_yearly"}
    ]
    output["layers"].insert(1, {
        "id": "ward_workorders",
        "label": "BBMP works spend by ward (2013-22)",
        "file": "ward_workorders.geojson",
        "kind": "fill",
        "group": "Who pays",
        "default": False,
        "outline": True,
        "popup": ["Ward", "works_spend_cr", "work_count", "top_contractor",
                  "top_budget_head", "flagged_works", "note_74a"],
        "paint": {
            "fill-color": ["interpolate", ["linear"], ["to-number", ["get", "works_spend_cr"], 0],
                           0, "#1f6f8b", 30, "#6b7f64", 70, "#d9a94f", 120, "#c84646"],
            "fill-opacity": 0.6,
        },
    })
    output["layers"].insert(2, {
        "id": "ward_workorders_yearly",
        "label": "BBMP works spend by ward, by year",
        "file": "ward_workorders_yearly.geojson",
        "kind": "fill",
        "group": "Who pays",
        "default": False,
        "outline": True,
        "year_field": "year",
        "year_values": years,
        "default_year": max(years),
        "popup": ["Ward", "year", "works_spend_cr", "work_count", "top_contractor",
                  "top_budget_head", "flagged_works", "note_74a"],
        "paint": {
            "fill-color": ["interpolate", ["linear"], ["to-number", ["get", "works_spend_cr"], 0],
                           0, "#1f6f8b", 5, "#6b7f64", 15, "#d9a94f", 30, "#c84646"],
            "fill-opacity": 0.6,
        },
    })
    return output
