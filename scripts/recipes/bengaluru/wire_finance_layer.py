#!/usr/bin/env python3
"""Join the ward work-order ledger onto BBMP-2023 ward geometry, build the teaching popup,
and patch the layer into the console manifest. Run AFTER build_finance_layer.py and build_city.py.

  .venv/bin/python scripts/recipes/bengaluru/wire_finance_layer.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CITY = ROOT / "data" / "cities" / "bengaluru"
LAYERS = CITY / "layers"


def nk(s: str) -> str:
    return re.sub(r"[^a-z]", "", str(s or "").lower())


def main() -> None:
    ledger = {nk(w["ward_name"].split(" ", 1)[-1]): w
              for w in json.load(open(CITY / "source" / "finance" / "ward_workorders.json"))}
    g = json.load(open(CITY / "source" / "boundaries" / "wards_bbmp198.geojson"))

    matched = 0
    for ft in g["features"]:
        p = ft["properties"]
        nm = p.get("name_en") or p.get("proposed_ward_name_en") or p.get("Name") or ""
        w = ledger.get(nk(nm))
        keep = {"Ward": nm}
        if w:
            matched += 1
            tc = w["top_contractors"][0] if w["top_contractors"] else None
            th = w["top_budget_heads"][0] if w["top_budget_heads"] else None
            works = "  •  ".join(f"{x['name'][:60]} — ₹{x['lakh']}L ({x['contractor'][:24]})"
                                 for x in w["flagged_works"][:5])
            keep.update({
                "works_spend_cr": w["total_nett_cr"],
                "work_count": w["work_count"],
                "top_contractor": f"{tc['name'][:30]} (₹{tc['cr']} cr)" if tc else "—",
                "top_budget_head": f"{th['head'][:50]} (₹{th['cr']} cr)" if th else "—",
                "flagged_works": works or "—",
                "note_74a": "BBMP work orders 2013-22; budget head shows which discretionary pocket paid.",
            })
        else:
            keep.update({"works_spend_cr": None, "work_count": None,
                         "flagged_works": "(ward not matched to 2013-22 ledger — vintage gap)"})
        ft["properties"] = keep

    out = LAYERS / "ward_workorders.geojson"
    out.write_text(json.dumps(g, ensure_ascii=False))
    print(f"joined {matched}/{len(g['features'])} ward polygons to the ledger -> {out.name}")

    # patch manifest
    mpath = LAYERS / "layer_manifest.json"
    m = json.load(open(mpath))
    m["layers"] = [l for l in m["layers"] if l["id"] != "ward_workorders"]
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
    mpath.write_text(json.dumps(m, ensure_ascii=False, indent=2))
    print(f"patched manifest: ward_workorders layer added (group 'Who pays')")


if __name__ == "__main__":
    main()
