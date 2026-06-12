#!/usr/bin/env python3
"""Merge AMTS/Janmarg bus *frequency* onto the ward layer, and test whether bus
service is rationed against deprivation — or not.

Why frequency, not stop count: a stop is not service. A ward can be blanketed
with stops yet see a bus twice an hour. So we compute buses/day per stop (a
frequency proxy) per ward and correlate it with the existing `deprivation` field.

The 26% problem: many GTFS stops fall OUTSIDE the 48 AMC ward polygons — they are
the lived agglomeration beyond the official municipal boundary (peri-urban
termini). Dropping them biases exactly the deprived eastern edge. So we (a) assign
each stop strictly by point-in-polygon, then (b) pull each still-unassigned stop
into its NEAREST ward within a distance buffer, and report the correlation BOTH
ways so the effect of closing the hole is explicit.

Stdlib only (no geopandas/venv needed).

    python3 scripts/recipes/ahmedabad/build_ward_transit_frequency.py [buffer_m]
"""
from __future__ import annotations
import csv, json, math, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GTFS = ROOT / "data/cities/ahmedabad/source/gtfs/amts_janmarg"
WARDS = ROOT / "data/cities/ahmedabad/layers/wards.geojson"
BUFFER_M = float(sys.argv[1]) if len(sys.argv) > 1 else 2500.0
M_PER_DEG = 111_000.0


def rings_of(geom):
    t = geom["type"]
    if t == "Polygon":
        yield geom["coordinates"][0]
    elif t == "MultiPolygon":
        for poly in geom["coordinates"]:
            yield poly[0]


def point_in_rings(x, y, rings_with_bbox):
    for ring, (x0, y0, x1, y1) in rings_with_bbox:
        if x < x0 or x > x1 or y < y0 or y > y1:
            continue
        inside = False
        n = len(ring); j = n - 1
        for i in range(n):
            xi, yi = ring[i][0], ring[i][1]
            xj, yj = ring[j][0], ring[j][1]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi):
                inside = not inside
            j = i
        if inside:
            return True
    return False


def nearest_ward(x, y, ward_rings, ward_bbox, coslat):
    """Return (ward_index, distance_m) to the nearest ward boundary vertex,
    considering only wards whose buffered bbox contains the point."""
    best_i, best_d2 = None, None
    bufdeg = BUFFER_M / M_PER_DEG
    for wi, (x0, y0, x1, y1) in enumerate(ward_bbox):
        if x < x0 - bufdeg or x > x1 + bufdeg or y < y0 - bufdeg or y > y1 + bufdeg:
            continue
        for ring, _ in ward_rings[wi]:
            for px, py in ring:
                dx = (px - x) * coslat
                dy = (py - y)
                d2 = dx * dx + dy * dy
                if best_d2 is None or d2 < best_d2:
                    best_d2, best_i = d2, wi
    if best_i is None:
        return None, None
    return best_i, math.sqrt(best_d2) * M_PER_DEG


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    vy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return cov / (vx * vy) if vx and vy else 0.0


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v); i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))


def aggregate(events, stops, assign):
    """assign: stop_id -> ward_index. Returns per-ward dict."""
    agg = defaultdict(lambda: defaultdict(int))
    for sid, e in events.items():
        wi = assign.get(sid)
        if wi is None:
            continue
        if e["AMTS"]:
            agg[wi]["amts_ev"] += e["AMTS"]; agg[wi]["amts_stops"] += 1
        if e["AJL"]:
            agg[wi]["brts_stops"] += 1
    return agg


def correlate(features, agg, label):
    deps, buses, bpss = [], [], []
    for wi, feat in enumerate(features):
        a = agg.get(wi, {})
        ev = a.get("amts_ev", 0); st = a.get("amts_stops", 0)
        bps = ev / st if st else 0.0
        try:
            d = float(feat["properties"].get("deprivation", ""))
        except (TypeError, ValueError):
            continue
        deps.append(d); buses.append(ev); bpss.append(bps)
    print(f"  {label:18s}  dep×buses/day  r={pearson(deps,buses):+.2f} rho={spearman(deps,buses):+.2f}"
          f"   |  dep×buses/stop  r={pearson(deps,bpss):+.2f} rho={spearman(deps,bpss):+.2f}")
    return deps, buses, bpss


def main():
    route_agency = {}
    with (GTFS / "routes.txt").open() as f:
        for r in csv.DictReader(f):
            route_agency[r["route_id"]] = r["agency_id"]
    trip_agency = {}
    with (GTFS / "trips.txt").open() as f:
        for r in csv.DictReader(f):
            trip_agency[r["trip_id"]] = route_agency.get(r["route_id"], "?")
    stops = {}
    with (GTFS / "stops.txt").open() as f:
        for r in csv.DictReader(f):
            try:
                stops[r["stop_id"]] = (float(r["stop_lon"]), float(r["stop_lat"]))
            except ValueError:
                pass
    events = defaultdict(lambda: {"AMTS": 0, "AJL": 0})
    with (GTFS / "stop_times.txt").open() as f:
        rd = csv.reader(f); next(rd)
        for row in rd:
            ag = trip_agency.get(row[0], "?")
            if ag in ("AMTS", "AJL"):
                events[row[3]][ag] += 1

    gj = json.loads(WARDS.read_text())
    feats = gj["features"]
    ward_rings, ward_bbox = [], []
    for feat in feats:
        rb = []
        allx, ally = [], []
        for ring in rings_of(feat["geometry"]):
            xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
            rb.append((ring, (min(xs), min(ys), max(xs), max(ys))))
            allx += xs; ally += ys
        ward_rings.append(rb)
        ward_bbox.append((min(allx), min(ally), max(allx), max(ally)))
    coslat = math.cos(math.radians(sum(b[1] + b[3] for b in ward_bbox) / (2 * len(ward_bbox))))

    # pass 1: strict point-in-polygon
    strict_assign = {}
    unassigned = []
    for sid, e in events.items():
        if sid not in stops:
            continue
        x, y = stops[sid]
        hit = None
        for wi, rb in enumerate(ward_rings):
            if point_in_rings(x, y, rb):
                hit = wi; break
        if hit is None:
            unassigned.append(sid)
        else:
            strict_assign[sid] = hit

    # pass 2: nearest-ward for the unassigned, bucketed by distance
    buckets = {"<250m": 0, "250m-1km": 0, "1-2.5km": 0, ">2.5km (left out)": 0}
    incl_assign = dict(strict_assign)
    reassigned_ev = 0
    for sid in unassigned:
        x, y = stops[sid]
        wi, dist = nearest_ward(x, y, ward_rings, ward_bbox, coslat)
        if wi is None or dist is None or dist > BUFFER_M:
            buckets[">2.5km (left out)"] += 1
            continue
        incl_assign[sid] = wi
        reassigned_ev += events[sid]["AMTS"]
        if dist < 250:
            buckets["<250m"] += 1
        elif dist < 1000:
            buckets["250m-1km"] += 1
        else:
            buckets["1-2.5km"] += 1

    print(f"stops with service: {len(strict_assign)+len(unassigned)}  |  strict in-ward: {len(strict_assign)}"
          f"  |  outside AMC wards: {len(unassigned)}")
    print(f"closing the hole (nearest ward within {BUFFER_M:.0f} m):")
    for k, v in buckets.items():
        print(f"    {k:20s} {v:5d}")
    print(f"    -> reassigned {len(unassigned)-buckets['>2.5km (left out)']} stops "
          f"({reassigned_ev:,} extra AMTS buses/day pulled in)")
    print()

    strict_agg = aggregate(events, stops, strict_assign)
    incl_agg = aggregate(events, stops, incl_assign)
    print("CORRELATION  (deprivation higher = more deprived; negative = deprived get less)")
    correlate(feats, strict_agg, "strict (in-ward)")
    correlate(feats, incl_agg, "incl. peri-urban")
    print()

    # write the inclusive (better) numbers onto wards.geojson
    bps_all = []
    for wi, feat in enumerate(feats):
        a = incl_agg.get(wi, {})
        ev = a.get("amts_ev", 0); st = a.get("amts_stops", 0)
        bps = round(ev / st, 1) if st else 0.0
        sa = strict_agg.get(wi, {})
        feat["properties"]["amts_buses_day"] = ev
        feat["properties"]["amts_buses_day_core"] = sa.get("amts_ev", 0)
        feat["properties"]["amts_stops_freq"] = st
        feat["properties"]["buses_per_stop"] = bps
        feat["properties"]["brts_stops"] = a.get("brts_stops", 0)
        bps_all.append(bps)
    served = sorted(b for b in bps_all if b > 0)
    q1 = served[len(served) // 4] if served else 0
    for feat in feats:
        feat["properties"]["transit_desert"] = bool(feat["properties"]["buses_per_stop"] <= q1)
    WARDS.write_text(json.dumps(gj, ensure_ascii=False))

    # quartile table (inclusive) + named worst
    paired = []
    for wi, feat in enumerate(feats):
        try:
            d = float(feat["properties"].get("deprivation", ""))
        except (TypeError, ValueError):
            continue
        paired.append((feat["properties"].get("Name", "?"), d,
                       feat["properties"]["amts_buses_day"], feat["properties"]["buses_per_stop"],
                       feat["properties"]["brts_stops"]))
    by_dep = sorted(paired, key=lambda t: t[1])
    qn = max(1, len(by_dep) // 4)
    print("by deprivation quartile (Q4 = most deprived), INCLUSIVE:")
    print("  quartile   mean buses/day   mean buses/stop")
    for qi, nm in enumerate(["Q1", "Q2", "Q3", "Q4"]):
        chunk = by_dep[qi * qn:(qi + 1) * qn] if qi < 3 else by_dep[3 * qn:]
        if not chunk:
            continue
        print(f"  {nm:8s}   {sum(t[2] for t in chunk)/len(chunk):12.0f}   {sum(t[3] for t in chunk)/len(chunk):15.1f}")
    print()
    print("lowest buses/stop wards (name, deprivation, buses/day, buses/stop, brts):")
    for name, d, ev, bps, brts in sorted(paired, key=lambda t: t[3])[:6]:
        print(f"  {name:28s} dep={d:.3f}  buses/day={ev:6d}  buses/stop={bps:5.1f}  brts={brts}")


if __name__ == "__main__":
    main()
