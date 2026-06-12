#!/usr/bin/env python3
"""Composite civic service-access score — libraries + schools + health + bus
frequency — computed per ward and rolled up to Assembly constituency.

Why: the atlas's accountability unit is the representative. A resident's services
are delivered by the ward (councillor) but contested at the AC (MLA). So the same
deprivation has to be readable at both levels. Bus frequency (buses/stop) goes
INTO the score, not beside it — a frequent bus is as much a public service as a
library.

Reads ward fields produced upstream (run build_ward_transit_frequency.py first),
writes composite_access/composite_gap onto wards.geojson, area-weights wards into
ACs via the jurisdiction crosswalk, and writes ac_service_access/ac_service_gap
onto acs.geojson (whose popup already carries the MLA). Stdlib only.

    python3 scripts/recipes/ahmedabad/build_service_access_composite.py
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
L = ROOT / "data/cities/ahmedabad/layers"
WARDS = L / "wards.geojson"
ACS = L / "acs.geojson"
CROSSWALK = L / "jurisdiction_crosswalk.json"

# components and weights (equal, transparent). buses_per_stop = service quality,
# not stop count. Per-capita would sharpen this but population isn't on the layer.
COMPONENTS = ["libraries", "schools", "health", "buses_per_stop"]
WEIGHTS = {c: 1.0 for c in COMPONENTS}


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def normalize(vals):
    lo, hi = min(vals), max(vals)
    span = hi - lo
    return [(v - lo) / span if span else 0.0 for v in vals]


def main():
    gj = json.loads(WARDS.read_text())
    feats = gj["features"]

    # normalize each component across wards, then weighted mean -> composite_access
    cols = {c: [fnum(f["properties"].get(c)) for f in feats] for c in COMPONENTS}
    norm = {c: normalize(cols[c]) for c in COMPONENTS}
    wsum = sum(WEIGHTS.values())
    ward_access = {}
    for i, f in enumerate(feats):
        acc = sum(WEIGHTS[c] * norm[c][i] for c in COMPONENTS) / wsum
        f["properties"]["composite_access"] = round(acc, 3)
        f["properties"]["composite_gap"] = round(1 - acc, 3)
        ward_access[f["properties"]["Name"]] = acc
    WARDS.write_text(json.dumps(gj, ensure_ascii=False))

    # roll wards up to ACs, area-weighted by overlap_area_m2
    cw = json.loads(CROSSWALK.read_text()).get("records", [])
    ac_num = defaultdict(float)   # sum(access * area)
    ac_den = defaultdict(float)   # sum(area)
    ac_wards = defaultdict(set)
    for r in cw:
        wname = r.get("ward_name")
        ac = r.get("ac_name")
        if wname not in ward_access or not ac:
            continue
        w = float(r.get("overlap_area_m2") or 0.0)
        if w <= 0:
            continue
        ac_num[ac] += ward_access[wname] * w
        ac_den[ac] += w
        ac_wards[ac].add(wname)
    ac_access = {ac: ac_num[ac] / ac_den[ac] for ac in ac_num if ac_den[ac] > 0}

    # write onto acs.geojson
    agj = json.loads(ACS.read_text())
    written = 0
    for f in agj["features"]:
        ac = f["properties"].get("ac_name")
        if ac in ac_access:
            f["properties"]["ac_service_access"] = round(ac_access[ac], 3)
            f["properties"]["ac_service_gap"] = round(1 - ac_access[ac], 3)
            f["properties"]["ac_amc_wards"] = len(ac_wards[ac])
            written += 1
        else:
            f["properties"]["ac_service_gap"] = ""
            f["properties"]["ac_amc_wards"] = 0
    ACS.write_text(json.dumps(agj, ensure_ascii=False))

    # report: AC service-gap ranking with the MLA who owns it
    rep = {f["properties"].get("ac_name"): (f["properties"].get("representative", "?"),
                                            f["properties"].get("party", "?"))
           for f in agj["features"]}
    print(f"composite components (equal-weight): {', '.join(COMPONENTS)}")
    print(f"wards scored: {len(ward_access)}  |  ACs with AMC wards scored: {written}\n")
    print("ASSEMBLY CONSTITUENCIES by service gap (worst first) — gap, AMC wards, MLA:")
    for ac, acc in sorted(ac_access.items(), key=lambda kv: kv[1]):
        mla, party = rep.get(ac, ("?", "?"))
        print(f"  gap {1-acc:.3f}  ({len(ac_wards[ac]):2d} wards)  {ac:22s} {mla} [{party}]")
    print("\nWARDS by composite gap (worst first):")
    worst = sorted(feats, key=lambda f: -f["properties"]["composite_gap"])[:8]
    for f in worst:
        p = f["properties"]
        print(f"  gap {p['composite_gap']:.3f}  {p['Name']:26s} "
              f"lib={p.get('libraries')} sch={p.get('schools')} hlth={p.get('health')} "
              f"buses/stop={p.get('buses_per_stop')} dep={p.get('deprivation')}")


if __name__ == "__main__":
    main()
