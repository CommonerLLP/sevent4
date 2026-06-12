#!/usr/bin/env python3
"""Reconcile Bengaluru's four ward vintages onto ONE canonical geometry (BBMP-2023, 225 wards)
so the four atlas axes line up on a single ward key:

  caste          <- BBMP-225 native sc_population / st_population
  representation <- BBMP-225 native assembly_constituency / parliamentary_constituency
  spend          <- BBMP work-orders ledger 2013-22 (joined by ward name)
  heat (LST)     <- KGIS-243 ward_heat, AREA-WEIGHTED-transferred onto BBMP-225 polygons

Writes data/cities/bengaluru/layers/ward_analysis.geojson (the canonical four-axis layer),
patches it into the manifest, and prints the cross-axis correlations.

  .venv/bin/python scripts/recipes/bengaluru/reconcile_wards.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[3]
CITY = ROOT / "data" / "cities" / "bengaluru"
LAYERS = CITY / "layers"
METRIC = 32643  # UTM 43N, metres, for area weighting


def nk(s: str) -> str:
    return re.sub(r"[^a-z]", "", str(s or "").lower())


def main() -> None:
    canon = gpd.read_file(CITY / "source" / "boundaries" / "wards_bbmp198.geojson").to_crs(METRIC)
    heat = gpd.read_file(LAYERS / "ward_heat.geojson").to_crs(METRIC)[["mean_lst_c", "max_lst_c", "geometry"]]

    # ── heat: area-weighted transfer KGIS-243 -> BBMP-225 ──────────────────
    canon["_cid"] = range(len(canon))
    inter = gpd.overlay(canon[["_cid", "geometry"]], heat, how="intersection")
    inter["_a"] = inter.geometry.area
    agg = {}
    for cid, grp in inter.groupby("_cid"):
        a = grp["_a"].sum()
        if a > 0:
            agg[cid] = (
                float((grp["mean_lst_c"] * grp["_a"]).sum() / a),
                float(grp["max_lst_c"].max()),
            )
    canon["mean_lst_c"] = canon["_cid"].map(lambda c: round(agg.get(c, (None, None))[0], 2) if agg.get(c) else None)
    canon["max_lst_c"] = canon["_cid"].map(lambda c: round(agg.get(c, (None, None))[1], 2) if agg.get(c) else None)

    # ── spend: join the work-orders ledger by ward name ────────────────────
    ledger = {nk(w["ward_name"].split(" ", 1)[-1]): w
              for w in json.load(open(CITY / "source" / "finance" / "ward_workorders.json"))}

    feats = []
    rows = []  # for correlations
    canon_wgs = canon.to_crs(4326)
    for i, (_, r) in enumerate(canon.iterrows()):
        nm = r.get("name_en") or r.get("proposed_ward_name_en") or r.get("Name") or ""
        pop = r.get("population") or 0
        sc = r.get("sc_population") or 0
        st = r.get("st_population") or 0
        w = ledger.get(nk(nm))
        spend = w["total_nett_cr"] if w else None
        tc = (w["top_contractors"][0] if w and w["top_contractors"] else None)
        th = (w["top_budget_heads"][0] if w and w["top_budget_heads"] else None)
        works = "  •  ".join(f"{x['name'][:55]} — ₹{x['lakh']}L" for x in (w["flagged_works"][:4] if w else []))
        sc_share = round(100 * sc / pop, 1) if pop else None
        st_share = round(100 * st / pop, 1) if pop else None
        spc = round(spend * 1e7 / pop) if (spend and pop) else None  # ₹ per resident
        props = {
            "Ward": nm,
            "population": int(pop) if pop else None,
            # caste axis
            "sc_share_pct": sc_share,
            "st_share_pct": st_share,
            "sc_st_share_pct": round((sc_share or 0) + (st_share or 0), 1) if sc_share is not None else None,
            # representation axis
            "assembly": r.get("assembly_constituency_name_en") or "",
            "parliament": r.get("parliamentary_constituency_name_en") or "",
            # spend axis
            "works_spend_cr": spend,
            "spend_per_resident_rs": spc,
            "top_contractor": f"{tc['name'][:28]} (₹{tc['cr']}cr)" if tc else "—",
            "top_budget_head": f"{th['head'][:46]} (₹{th['cr']}cr)" if th else "—",
            "flagged_works": works or "—",
            # heat axis
            "mean_lst_c": canon.iloc[i]["mean_lst_c"],
            "max_lst_c": canon.iloc[i]["max_lst_c"],
        }
        feats.append({"type": "Feature", "properties": props,
                      "geometry": json.loads(gpd.GeoSeries([canon_wgs.iloc[i].geometry]).to_json())["features"][0]["geometry"]})
        rows.append((sc_share, st_share, spend, spc, props["mean_lst_c"]))

    out = LAYERS / "ward_analysis.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False))

    # ── correlations across the four axes ──────────────────────────────────
    def corr(a, b):
        pts = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
        if len(pts) < 5:
            return None, len(pts)
        n = len(pts)
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        mx = sum(xs) / n; my = sum(ys) / n
        cov = sum((x - mx) * (y - my) for x, y in pts)
        vx = sum((x - mx) ** 2 for x in xs) ** 0.5
        vy = sum((y - my) ** 2 for y in ys) ** 0.5
        return (round(cov / (vx * vy), 3) if vx and vy else None), n

    sc = [r[0] for r in rows]; st = [r[1] for r in rows]
    spend = [r[2] for r in rows]; spc = [r[3] for r in rows]; lst = [r[4] for r in rows]
    matched = sum(1 for s in spend if s is not None)
    print(f"canonical wards: {len(feats)} (BBMP-2023) | spend-joined: {matched} | heat-transferred: "
          f"{sum(1 for x in lst if x is not None)}")
    print("\n── cross-axis correlations (Pearson r, n) ──")
    for label, a, b in [
        ("SC/ST share  ×  works spend (₹cr)", sc, spend),
        ("SC/ST share  ×  spend per resident", sc, spc),
        ("SC/ST share  ×  surface temp (LST)", sc, lst),
        ("surface temp ×  works spend (₹cr)", lst, spend),
        ("surface temp ×  spend per resident", lst, spc),
    ]:
        r, n = corr(a, b)
        print(f"  {label:42} r={r}  (n={n})")

    # patch manifest
    mp = LAYERS / "layer_manifest.json"
    m = json.load(open(mp))
    m["layers"] = [l for l in m["layers"] if l["id"] != "ward_analysis"]
    m["layers"].insert(1, {
        "id": "ward_analysis", "label": "Four-axis ward analysis (caste·spend·heat·rep)",
        "file": "ward_analysis.geojson", "kind": "fill", "group": "Four-axis", "default": False,
        "outline": True,
        "popup": ["Ward", "population", "sc_st_share_pct", "assembly", "parliament",
                  "works_spend_cr", "spend_per_resident_rs", "mean_lst_c",
                  "top_contractor", "top_budget_head", "flagged_works"],
        "paint": {"fill-color": ["interpolate", ["linear"], ["to-number", ["get", "sc_st_share_pct"], 0],
                                 0, "#f7f4ea", 15, "#d9a94f", 30, "#c84646", 50, "#7a1f1f"],
                  "fill-opacity": 0.62},
    })
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=2))
    print(f"\nwrote {out.name} + patched manifest (group 'Four-axis')")


if __name__ == "__main__":
    main()
