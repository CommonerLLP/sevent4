"""Pure per-ward analysis for Kanpur's PARTIAL ward layer (56 of 110 wards).

Honest-by-construction: per-ward values are individually valid, but the SUM is
NOT the city total. This module owns area/density math, the heat join, the
heat-vulnerability tertile cut, the `ward_coverage` caveat, the oversized-polygon
flag, the additive field propagation, and the partial-only summary lines. No
filesystem IO lives here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

COVERAGE_NOTE = "56 of 110 wards (partial layer, DataMeet 2018) — not a complete city map"
CITY_LAT = 26.45  # mean latitude, Kanpur
# A real Kanpur ward averages ~436 km2 / 110 ≈ 4 km2. Polygons far larger are
# mis-delimited (zone-sized units mislabelled as wards); flag > 12 km2 (3x).
SUSPECT_AREA_KM2 = 12.0

WARD_FIELD_KEYS = (
    "population_2020", "area_km2", "pop_density_km2", "mean_lst_c", "max_lst_c",
    "heat_vulnerable", "geometry_suspect", "ward_coverage",
)
HEAT_FIELD_KEYS = ("population_2020", "pop_density_km2", "heat_vulnerable", "ward_coverage")


@dataclass
class KanpurAnalysis:
    rows: list[tuple]
    dens_cut: float | None
    lst_cut: float | None
    n_vuln: int
    total_features: int
    null_real: int


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


def heat_index(heat):
    """Map (ward_no, id) -> (mean_lst_c, max_lst_c)."""
    idx = {}
    for f in heat["features"]:
        p = f["properties"]
        idx[(p.get("ward_no"), p.get("id"))] = (p.get("mean_lst_c"), p.get("max_lst_c"))
    return idx


def enrich_wards(wards: dict, heat: dict) -> KanpurAnalysis:
    """Mutate ward features in place with area/density/heat/coverage fields and
    the heat-vulnerability flag; return the aggregates the summary needs."""
    hidx = heat_index(heat)
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
        vuln = bool(d is not None and l is not None and dens_cut is not None and d >= dens_cut and l >= lst_cut)
        p["heat_vulnerable"] = vuln
        n_vuln += vuln

    null_real = sum(
        1 for f in wards["features"]
        if f["properties"].get("population_2020") is None and f["properties"].get("ward_no") is not None
    )
    return KanpurAnalysis(rows, dens_cut, lst_cut, n_vuln, len(wards["features"]), null_real)


def apply_fields(target: dict, wards: dict, keys) -> dict:
    """Additively copy the named keys from the source wards onto a target layer,
    matched on (ward_no, id). Mutates and returns target."""
    by_key = {
        (f["properties"].get("ward_no"), f["properties"].get("id")): f["properties"]
        for f in wards["features"]
    }
    for f in target["features"]:
        sp = by_key.get((f["properties"].get("ward_no"), f["properties"].get("id")))
        if sp:
            for k in keys:
                if k in sp:
                    f["properties"][k] = sp[k]
    return target


def summary_lines(a: KanpurAnalysis) -> list[str]:
    rows = a.rows
    n_susp = sum(1 for r in rows if r[5])
    clean_rows = [r for r in rows if not r[5]]
    pops = [r[1] for r in clean_rows if r[1]]
    dens = [r[3] for r in clean_rows if r[3]]
    n_populated = len([r for r in rows if r[1]])
    lines = [
        f"features populated:        {n_populated}/{a.total_features}  "
        f"({a.null_real} real wards unfetched: invalid geometry)",
        f"oversized/suspect polygons (area>{SUSPECT_AREA_KM2} km2): {n_susp}  "
        f"-> excluded from stats (zone-sized, not single wards)",
        "** No city total reported. Authoritative city figure = 2,765,348 "
        "(Census 2011, all 110 wards). **",
    ]
    if pops:
        sp = sorted(pops)
        lines.append(
            f"clean per-ward population: min {round(min(pops)):,}  "
            f"median {round(sp[len(sp) // 2]):,}  max {round(max(pops)):,}  (n={len(pops)})"
        )
    if dens:
        ds = sorted(dens)
        lines.append(
            f"clean per-ward density /km2: min {min(ds):,}  median {ds[len(ds) // 2]:,}  max {max(ds):,}"
        )
    lines.append(
        f"heat-vulnerable wards (top-tertile density AND mean LST, clean only): {a.n_vuln}  "
        f"[density>={a.dens_cut}/km2, LST>={a.lst_cut}C]"
    )
    return lines
