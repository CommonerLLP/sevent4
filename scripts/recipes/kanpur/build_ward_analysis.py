#!/usr/bin/env python3
"""Per-ward analysis for Kanpur's PARTIAL ward layer (56 of 110 wards).

Honest-by-construction. Kanpur's only open ward vector (DataMeet, 2018) holds 56 of the
city's 110 wards (see data/cities/kanpur/source/PROVENANCE.md). Per-ward values are
individually valid — each WorldPop population is computed from that ward's real polygon,
and each heat value from the Landsat LST raster — but the SUM is NOT the city total
(it covers ~53% of the city; Census-2011 KMC = 2,765,348 across 110 wards).

This recipe:
  1. reads source/boundaries/wards.geojson (must already carry population_2020 from
     worldpop_robust.py),
  2. computes area_km2 (equirectangular at city latitude) and pop_density_km2 per ward,
  3. joins per-ward heat (mean_lst_c / max_lst_c) from ward_heat.geojson,
  4. derives a heat-vulnerability flag (top-tertile density AND top-tertile mean LST),
  5. stamps a `ward_coverage` caveat string onto every ward (shows in the popup),
  6. writes the enriched wards into data/.../layers + public/.../layers and refreshes
     ward_heat population, and prints partial-only summary stats (NO city total claim).

Run (after the population join):  python3 scripts/recipes/kanpur/build_ward_analysis.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "data" / "cities" / "kanpur" / "source" / "boundaries" / "wards.geojson"
LAYER_WARDS = REPO / "data" / "cities" / "kanpur" / "layers" / "wards.geojson"
PUB_WARDS = REPO / "public" / "cities" / "kanpur" / "layers" / "wards.geojson"
LAYER_HEAT = REPO / "data" / "cities" / "kanpur" / "layers" / "ward_heat.geojson"
PUB_HEAT = REPO / "public" / "cities" / "kanpur" / "layers" / "ward_heat.geojson"

COVERAGE_NOTE = "56 of 110 wards (partial layer, DataMeet 2018) — not a complete city map"
CITY_LAT = 26.45  # mean latitude, Kanpur
# A real Kanpur ward averages ~436 km2 / 110 ≈ 4 km2. Polygons far larger than that in the
# DataMeet 2018 file are mis-delimited (zone-sized units mislabelled as wards, e.g. Panki 45 km2,
# Naramau 46 km2) and their WorldPop counts are not meaningful as a single ward. Flag > 12 km2 (3x).
SUSPECT_AREA_KM2 = 12.0


def ring_area_m2(ring, lat0):
    R = 6371000.0
    k = math.cos(math.radians(lat0))
    xs, ys = [], []
    for lon, lat in ring:
        xs.append(math.radians(lon) * R * k)
        ys.append(math.radians(lat) * R)
    s = 0.0
    for i in range(len(xs) - 1):
        s += xs[i] * ys[i + 1] - xs[i + 1] * ys[i]
    return abs(s) / 2


def feat_area_km2(geom):
    if not geom:
        return None
    t, c = geom["type"], geom["coordinates"]
    polys = [c] if t == "Polygon" else c
    a = 0.0
    for poly in polys:
        a += ring_area_m2(poly[0], CITY_LAT) - sum(ring_area_m2(h, CITY_LAT) for h in poly[1:])
    return a / 1e6


def tertile_cut(values, frac=2 / 3):
    """Return the value at `frac` quantile (top tertile threshold by default)."""
    vs = sorted(v for v in values if v is not None)
    if not vs:
        return None
    idx = min(len(vs) - 1, int(round(frac * (len(vs) - 1))))
    return vs[idx]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def dump(obj, p):
    Path(p).write_text(json.dumps(obj), encoding="utf-8")


def heat_index(heat):
    """Map (ward_no, id) -> (mean_lst_c, max_lst_c)."""
    idx = {}
    for f in heat["features"]:
        p = f["properties"]
        key = (p.get("ward_no"), p.get("id"))
        idx[key] = (p.get("mean_lst_c"), p.get("max_lst_c"))
    return idx


def main():
    wards = load(SRC)
    heat = load(LAYER_HEAT) if LAYER_HEAT.exists() else {"features": []}
    hidx = heat_index(heat)

    # pass 1: area, density, heat join
    rows = []
    for f in wards["features"]:
        p = f["properties"]
        pop = p.get("population_2020")
        area = feat_area_km2(f.get("geometry"))
        p["area_km2"] = round(area, 3) if area else None
        dens = round(pop / area) if (pop and area) else None
        p["pop_density_km2"] = dens
        mean_lst, max_lst = hidx.get((p.get("ward_no"), p.get("id")), (None, None))
        if mean_lst is not None:
            p["mean_lst_c"] = mean_lst
        if max_lst is not None:
            p["max_lst_c"] = max_lst
        suspect = bool(area and area > SUSPECT_AREA_KM2)
        p["geometry_suspect"] = suspect
        p["ward_coverage"] = (
            COVERAGE_NOTE + " · OVERSIZED polygon (~zone, not one ward): population unreliable"
            if suspect else COVERAGE_NOTE
        )
        rows.append((p.get("ward_no"), pop, p["area_km2"], dens, mean_lst, suspect))

    # pass 2: heat-vulnerability = top tertile density AND top tertile mean LST.
    # Computed over NON-suspect wards only (oversized polygons distort the cuts).
    clean = [r for r in rows if not r[5]]
    dens_cut = tertile_cut([r[3] for r in clean])
    lst_cut = tertile_cut([r[4] for r in clean])
    n_vuln = 0
    for f in wards["features"]:
        p = f["properties"]
        if p.get("geometry_suspect"):
            p["heat_vulnerable"] = False
            continue
        d, l = p.get("pop_density_km2"), p.get("mean_lst_c")
        vuln = bool(d is not None and l is not None and dens_cut is not None
                    and d >= dens_cut and l >= lst_cut)
        p["heat_vulnerable"] = vuln
        n_vuln += vuln

    dump(wards, SRC)

    # propagate population + analysis fields into layers/ and public/ wards
    for target in (LAYER_WARDS, PUB_WARDS):
        tgt = load(target)
        by_key = {(f["properties"].get("ward_no"), f["properties"].get("id")): f["properties"]
                  for f in wards["features"]}
        for f in tgt["features"]:
            sp = by_key.get((f["properties"].get("ward_no"), f["properties"].get("id")))
            if sp:
                for k in ("population_2020", "area_km2", "pop_density_km2",
                          "mean_lst_c", "max_lst_c", "heat_vulnerable",
                          "geometry_suspect", "ward_coverage"):
                    if k in sp:
                        f["properties"][k] = sp[k]
        dump(tgt, target)

    # refresh population on ward_heat copies (display parity)
    for target in (LAYER_HEAT, PUB_HEAT):
        if not Path(target).exists():
            continue
        tgt = load(target)
        by_key = {(f["properties"].get("ward_no"), f["properties"].get("id")): f["properties"]
                  for f in wards["features"]}
        for f in tgt["features"]:
            sp = by_key.get((f["properties"].get("ward_no"), f["properties"].get("id")))
            if sp:
                for k in ("population_2020", "pop_density_km2", "heat_vulnerable", "ward_coverage"):
                    if k in sp:
                        f["properties"][k] = sp[k]
        dump(tgt, target)

    # ── summary (PARTIAL — never a city total; lead with robust medians) ──
    n_susp = sum(1 for r in rows if r[5])
    clean_rows = [r for r in rows if not r[5]]
    pops = [r[1] for r in clean_rows if r[1]]          # exclude oversized polygons
    dens = [r[3] for r in clean_rows if r[3]]
    null_real = sum(1 for f in wards["features"]
                    if f["properties"].get("population_2020") is None
                    and f["properties"].get("ward_no") is not None)
    print(f"features populated:        {len([r for r in rows if r[1]])}/{len(wards['features'])}  "
          f"({null_real} real wards unfetched: invalid geometry)")
    print(f"oversized/suspect polygons (area>{SUSPECT_AREA_KM2} km2): {n_susp}  "
          f"-> excluded from stats (zone-sized, not single wards)")
    print(f"** No city total reported. Authoritative city figure = 2,765,348 "
          f"(Census 2011, all 110 wards). **")
    if pops:
        sp = sorted(pops)
        print(f"clean per-ward population: min {round(min(pops)):,}  "
              f"median {round(sp[len(sp)//2]):,}  max {round(max(pops)):,}  (n={len(pops)})")
    if dens:
        ds = sorted(dens)
        print(f"clean per-ward density /km2: min {min(ds):,}  median {ds[len(ds)//2]:,}  max {max(ds):,}")
    print(f"heat-vulnerable wards (top-tertile density AND mean LST, clean only): {n_vuln}  "
          f"[density>={dens_cut}/km2, LST>={lst_cut}C]")


if __name__ == "__main__":
    main()
