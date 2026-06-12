#!/usr/bin/env python3
"""Build the jurisdiction_crosswalk.json the console needs for its ward/AC/PC dropdowns.

The scaffold cities shipped with EMPTY dropdowns because only Ahmedabad had this sidecar.
This derives it for any city by spatially joining ward -> AC and ward -> PC (each from its
own layer), so it works whether or not the AC layer carries PC_NAME. Emits schema
sevent4.jurisdiction_crosswalk.v1 (a flat `records` list of {ward_name, ac_name, pc_name,
district_name}) — exactly what _jurisdiction_context() in build_city_console.py consumes.

Robustness notes:
- pick() prefers a candidate column that actually HAS DATA (Bengaluru's AC layer carries both
  `AC_NAME`='Yelahanka' and an empty `ac_name`; a naive case-insensitive match picked the empty
  one and produced 0 records).
- Spatial ops run in a projected CRS (EPSG:3857) so sjoin_nearest is valid (no geographic-CRS
  warning / wrong nearest).

Run:  .venv/bin/python scripts/recipes/build_jurisdiction_crosswalk.py <city> [<city> ...]
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
M = 3857  # projected CRS for spatial joins


def pick(df, *cands):
    """First candidate that exists (exact, else case-insensitive first-occurrence) AND has data."""
    cols = list(df.columns)
    ci: dict[str, str] = {}
    for c in cols:
        ci.setdefault(c.lower(), c)  # first occurrence wins (AC_NAME before ac_name)
    for cand in cands:
        col = cand if cand in cols else ci.get(cand.lower())
        if col is not None and df[col].notna().any():
            return col
    return None


def _s(v) -> str:
    s = "" if v is None else str(v).strip()
    return "" if s.lower() in ("nan", "none", "") else s


def _nearest_attr(points, polys, col):
    """Value of `col` from the polygon each point falls in (nearest fallback). Indexed to points."""
    pp = polys.to_crs(M)[[col, "geometry"]].rename(columns={col: "_v"})
    j = gpd.sjoin(points[["geometry"]], pp, predicate="within", how="left")
    j = j[~j.index.duplicated(keep="first")]
    miss = j["_v"].isna()
    if miss.any():
        idx = miss[miss].index
        nr = gpd.sjoin_nearest(points.loc[idx][["geometry"]], pp, how="left")
        nr = nr[~nr.index.duplicated(keep="first")]
        j.loc[nr.index, "_v"] = nr["_v"]
    return j["_v"].reindex(points.index)


def build(city: str):
    ld = ROOT / "data" / "cities" / city / "layers"
    wards = gpd.read_file(ld / "wards.geojson")
    acs = gpd.read_file(ld / "acs.geojson")
    pcs = gpd.read_file(ld / "pcs.geojson") if (ld / "pcs.geojson").exists() else None

    ac_name = pick(acs, "AC_NAME", "ac_name", "ASSEM_CSTNY_NAME", "ASSMBLY_NAME", "Name", "name")
    dist = pick(acs, "DIST_NAME", "district", "DISTRICT", "dt_name")
    w_name = pick(wards, "ward_name", "Name", "name", "ward_no", "WARD_NO")
    # PC name fields vary by source (ECI / KGIS / DataMeet) — include the KGIS convention
    pc_name = pick(pcs, "PC_NAME", "pc_name", "PARLY_CSTNY_NAME", "Name", "name") if pcs is not None else None
    pc_name_ac = pick(acs, "PC_NAME", "pc_name", "PARLY_CSTNY_NAME")  # fallback: PC carried on the AC layer
    if not ac_name or not w_name:
        sys.exit(f"{city}: missing AC name ({ac_name}) or ward name ({w_name}) field")

    wsrc = wards.to_crs(M)
    wpts = wsrc.copy()
    wpts["geometry"] = wsrc.representative_point()

    ac_s = _nearest_attr(wpts, acs, ac_name)
    dist_s = _nearest_attr(wpts, acs, dist) if dist else None
    if pcs is not None and pc_name:
        pc_s = _nearest_attr(wpts, pcs, pc_name)
    elif pc_name_ac:
        pc_s = _nearest_attr(wpts, acs, pc_name_ac)
    else:
        pc_s = None

    records, matched = [], 0
    for idx, r in wards.iterrows():
        wn = _s(r[w_name])
        if w_name in ("ward_no", "WARD_NO") and wn and not wn.lower().startswith("ward"):
            wn = f"Ward {wn}"
        an = _s(ac_s.get(idx))
        if not (wn and an):
            continue
        matched += 1
        records.append({
            "ward_name": wn,
            "ac_name": an,
            "pc_name": _s(pc_s.get(idx)) if pc_s is not None else "",
            "district_name": _s(dist_s.get(idx)) if dist_s is not None else "",
        })

    out = {
        "schema": "sevent4.jurisdiction_crosswalk.v1",
        "city": city,
        "country": "India",
        "levels": ["state", "district"],
        "thresholds": {"method": "ward representative point within AC/PC polygon (nearest fallback), EPSG:3857"},
        "excluded_acs": [],
        "source": "spatial join of city ward/AC/PC layers",
        "records": records,
    }
    (ld / "jurisdiction_crosswalk.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    nac = len({r["ac_name"] for r in records})
    npc = len({r["pc_name"] for r in records if r["pc_name"]})
    print(f"[{city}] crosswalk: {matched}/{len(wards)} wards -> {nac} ACs, {npc} PCs", file=sys.stderr)


if __name__ == "__main__":
    for c in (sys.argv[1:] or ["kolkata", "chennai"]):
        build(c)
