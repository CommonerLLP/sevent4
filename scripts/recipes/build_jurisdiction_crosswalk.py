#!/usr/bin/env python3
"""Build the jurisdiction_crosswalk.json the console needs for its ward/AC/PC dropdowns.

The scaffold cities shipped with EMPTY dropdowns because only Ahmedabad had this sidecar.
This derives it for any city by spatially joining ward -> AC (the AC layer already carries
PC_NAME + DIST_NAME, so PC/district come free). Emits schema sevent4.jurisdiction_crosswalk.v1
(a flat `records` list of {ward_name, ac_name, pc_name, district_name}) — exactly what
_jurisdiction_context() in build_city_console.py consumes.

Run:  .venv/bin/python scripts/recipes/build_jurisdiction_crosswalk.py <city> [<city> ...]
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]


def pick(cols, *cands):
    low = {c.lower(): c for c in cols}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    return None


def build(city: str):
    ld = ROOT / "data" / "cities" / city / "layers"
    wards = gpd.read_file(ld / "wards.geojson")
    acs = gpd.read_file(ld / "acs.geojson")

    ac_name = pick(acs.columns, "AC_NAME", "ac_name", "Name", "name")
    pc_name = pick(acs.columns, "PC_NAME", "pc_name")
    dist = pick(acs.columns, "DIST_NAME", "district", "DISTRICT", "dt_name")
    w_name = pick(wards.columns, "ward_name", "Name", "name", "ward_no", "WARD_NO")
    if not ac_name or not w_name:
        sys.exit(f"{city}: missing AC name ({ac_name}) or ward name ({w_name}) field")

    # spatial join on ward representative points -> AC polygon (within, then nearest fallback)
    wpts = wards.copy()
    wpts["geometry"] = wpts.representative_point()
    keep = [c for c in (ac_name, pc_name, dist) if c]
    joined = gpd.sjoin(wpts, acs[keep + ["geometry"]], predicate="within", how="left")
    miss = joined[ac_name].isna()
    if miss.any():  # boundary points: nearest AC
        near = gpd.sjoin_nearest(wpts[miss.values], acs[keep + ["geometry"]], how="left")
        joined.loc[miss.values, keep] = near[keep].values

    records, matched = [], 0
    for _, r in joined.iterrows():
        wn = str(r[w_name]).strip()
        an = str(r[ac_name]).strip() if r.get(ac_name) and str(r[ac_name]) != "nan" else ""
        if wn and not wn.lower().startswith("ward") and w_name in ("ward_no", "WARD_NO"):
            wn = f"Ward {wn}"
        if not (wn and an):
            continue
        matched += 1
        records.append({
            "ward_name": wn,
            "ac_name": an,
            "pc_name": (str(r[pc_name]).strip() if pc_name and str(r.get(pc_name)) not in ("nan", "None", "") else ""),
            "district_name": (str(r[dist]).strip() if dist and str(r.get(dist)) not in ("nan", "None", "") else ""),
        })

    out = {
        "schema": "sevent4.jurisdiction_crosswalk.v1",
        "city": city,
        "country": "India",
        "levels": ["state", "district"],
        "thresholds": {"method": "ward representative point within AC polygon (nearest fallback)"},
        "excluded_acs": [],
        "source": "spatial join of city ward/AC/PC layers (AC carries PC_NAME + DIST_NAME)",
        "records": records,
    }
    (ld / "jurisdiction_crosswalk.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    nac = len({r["ac_name"] for r in records}); npc = len({r["pc_name"] for r in records if r["pc_name"]})
    print(f"[{city}] crosswalk: {matched}/{len(wards)} wards -> {nac} ACs, {npc} PCs", file=sys.stderr)


if __name__ == "__main__":
    for c in (sys.argv[1:] or ["kolkata", "chennai"]):
        build(c)
