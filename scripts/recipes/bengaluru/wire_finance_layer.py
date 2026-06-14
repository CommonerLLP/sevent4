#!/usr/bin/env python3
"""Join the ward work-order ledger onto BBMP-2023 ward geometry, build the teaching popup,
and patch the layer into the console manifest. Run AFTER build_finance_layer.py and build_city.py.

  .venv/bin/python scripts/recipes/bengaluru/wire_finance_layer.py
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CITY = ROOT / "data" / "cities" / "bengaluru"
LAYERS = CITY / "layers"


def nk(s: str) -> str:
    return re.sub(r"[^a-z]", "", str(s or "").lower())


def _work_text(works: list[dict]) -> str:
    return "  •  ".join(
        f"{x['name'][:60]} — ₹{x['lakh']}L ({x['contractor'][:24]})"
        for x in works[:5]
    ) or "—"


def _ledger_key(record: dict) -> str:
    return nk(str(record["ward_name"]).split(" ", 1)[-1])


def _ward_label(properties: dict) -> str:
    return (
        properties.get("name_en")
        or properties.get("proposed_ward_name_en")
        or properties.get("Name")
        or properties.get("Ward")
        or ""
    )


def build_yearly_geojson(boundary: dict, yearly_records: list[dict], years: list[int]) -> dict:
    ledger = {(_ledger_key(w), int(w["year"])): w for w in yearly_records}
    features = []
    for ft in boundary["features"]:
        p = ft["properties"]
        nm = _ward_label(p)
        key = nk(nm)
        for year in years:
            out = deepcopy(ft)
            w = ledger.get((key, year))
            keep = {"Ward": nm, "year": year}
            if w:
                tc = w["top_contractors"][0] if w["top_contractors"] else None
                th = w["top_budget_heads"][0] if w["top_budget_heads"] else None
                keep.update({
                    "works_spend_cr": w["total_nett_cr"],
                    "work_count": w["work_count"],
                    "top_contractor": f"{tc['name'][:30]} (₹{tc['cr']} cr)" if tc else "—",
                    "top_budget_head": f"{th['head'][:50]} (₹{th['cr']} cr)" if th else "—",
                    "flagged_works": _work_text(w["flagged_works"]),
                    "note_74a": "BBMP work orders by Order Date year; cumulative layer is separate.",
                })
            else:
                keep.update({
                    "works_spend_cr": None,
                    "work_count": None,
                    "top_contractor": "—",
                    "top_budget_head": "—",
                    "flagged_works": "(no matched work orders for this ward/year)",
                    "note_74a": "BBMP work orders by Order Date year; cumulative layer is separate.",
                })
            out["properties"] = keep
            features.append(out)
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    ledger = {nk(w["ward_name"].split(" ", 1)[-1]): w
              for w in json.load(open(CITY / "source" / "finance" / "ward_workorders.json"))}
    boundary_path = CITY / "source" / "boundaries" / "wards_bbmp198.geojson"
    if boundary_path.exists():
        boundary = json.load(open(boundary_path))
    else:
        boundary = json.load(open(LAYERS / "ward_workorders.geojson"))
    g = deepcopy(boundary)
    yearly_records = json.load(open(CITY / "source" / "finance" / "ward_workorders_yearly.json"))
    years = sorted({int(row["year"]) for row in yearly_records})

    matched = 0
    for ft in g["features"]:
        p = ft["properties"]
        nm = _ward_label(p)
        w = ledger.get(nk(nm))
        keep = {"Ward": nm}
        if w:
            matched += 1
            tc = w["top_contractors"][0] if w["top_contractors"] else None
            th = w["top_budget_heads"][0] if w["top_budget_heads"] else None
            keep.update({
                "works_spend_cr": w["total_nett_cr"],
                "work_count": w["work_count"],
                "top_contractor": f"{tc['name'][:30]} (₹{tc['cr']} cr)" if tc else "—",
                "top_budget_head": f"{th['head'][:50]} (₹{th['cr']} cr)" if th else "—",
                "flagged_works": _work_text(w["flagged_works"]),
                "note_74a": "BBMP work orders 2013-22; budget head shows which discretionary pocket paid.",
            })
        else:
            keep.update({"works_spend_cr": None, "work_count": None,
                         "flagged_works": "(ward not matched to 2013-22 ledger — vintage gap)"})
        ft["properties"] = keep

    out = LAYERS / "ward_workorders.geojson"
    out.write_text(json.dumps(g, ensure_ascii=False))
    print(f"joined {matched}/{len(g['features'])} ward polygons to the ledger -> {out.name}")
    yearly_out = build_yearly_geojson(boundary, yearly_records, years)
    (LAYERS / "ward_workorders_yearly.geojson").write_text(json.dumps(yearly_out, ensure_ascii=False))
    print(f"wrote ward_workorders_yearly.geojson ({len(yearly_out['features'])} ward-year features)")

    # patch manifest
    mpath = LAYERS / "layer_manifest.json"
    m = json.load(open(mpath))
    m["layers"] = [l for l in m["layers"] if l["id"] not in {"ward_workorders", "ward_workorders_yearly"}]
    m["layers"].insert(1, {
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
    m["layers"].insert(2, {
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
    mpath.write_text(json.dumps(m, ensure_ascii=False, indent=2))
    print(f"patched manifest: ward_workorders + ward_workorders_yearly layers added (group 'Who pays')")


if __name__ == "__main__":
    main()
