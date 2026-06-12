#!/usr/bin/env python3
"""First-pass suburban/commuter rail network from OpenStreetMap (Overpass).

WHY: suburban rail is a UNION subject (Indian Railways) — the city's biggest mass-transit
spine, run two rungs above the elected municipality. The consoles only carry METRO (state
SPV) today; this adds the suburban layer so the governance stack (Union rail vs state metro
vs city/state bus) is legible on one map.

DATA-TRUST: geometry is OSM — NON-AUTHORITATIVE per the atlas hierarchy. This is an
illustrative network layer (lines + stations), clearly labelled OSM, NOT a precise/official
source. Indian Railways publishes no open GIS. FIRST PASS — quality to be improved (filter
freight/yards, dedupe with metro, verify line membership).

Pulls commuter/suburban/regional train route relations + their member ways (lines) and
station nodes, within a generous metro-area bbox (suburban extends well past the corp
boundary — that's the point). Writes per city:
  data/cities/<city>/layers/suburban_rail.geojson           (lines, by route)
  data/cities/<city>/layers/suburban_rail_stations.geojson  (stations)
  data/cities/<city>/source/transit/suburban_rail.sources.json

Run:  .venv/bin/python scripts/recipes/transit/pull_suburban_rail.py <city>
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[3]
ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas)"}

# (south, west, north, east) — generous, to capture the network beyond the corp boundary
BBOX = {
    "kolkata":   (22.00, 88.00, 23.15, 88.65),
    "chennai":   (12.55, 79.55, 13.32, 80.40),
    "bengaluru": (12.70, 77.30, 13.25, 77.95),
}
# under-construction flag for the per-city note
CONSTRUCTION = {"bengaluru": True}


def overpass(query: str) -> dict:
    last = None
    for ep in ENDPOINTS:
        try:
            data = urlencode({"data": query}).encode()
            with urlopen(Request(ep, data=data, headers=UA), timeout=300) as r:
                j = json.loads(r.read())
            rk = j.get("remark", "")
            if "error" in rk.lower() or "timed out" in rk.lower():
                last = rk; print(f"  [overpass remark] {rk[:120]}", file=sys.stderr); time.sleep(3); continue
            return j
        except Exception as e:
            last = e; print(f"  [warn] {ep}: {e}", file=sys.stderr); time.sleep(3)
    raise RuntimeError(f"Overpass failed: {last}")


def tiles(bbox, nx=3, ny=3):
    s, w, n, e = bbox
    dy, dx = (n - s) / ny, (e - w) / nx
    for i in range(ny):
        for j in range(nx):
            yield (round(s + i * dy, 4), round(w + j * dx, 4),
                   round(s + (i + 1) * dy, 4), round(w + (j + 1) * dx, 4))


def q_rail(bb) -> str:
    s, w, n, e = bb
    # physical heavy-rail network (excludes metro=subway, yards/sidings/industrial)
    return f"""[out:json][timeout:120];
(
  way["railway"="rail"]["service"!~"yard|siding|spur|crossover"]["usage"!="industrial"]({s},{w},{n},{e});
);
out geom tags;"""


def q_stations(bb) -> str:
    s, w, n, e = bb
    return f"""[out:json][timeout:90];
(
  node["railway"="station"]["station"!="subway"]({s},{w},{n},{e});
  node["railway"="halt"]({s},{w},{n},{e});
);
out tags;"""


def build(city: str):
    if city not in BBOX:
        sys.exit(f"unknown city {city}; known: {list(BBOX)}")
    bbox = BBOX[city]
    out = ROOT / "data" / "cities" / city / "layers"
    src = ROOT / "data" / "cities" / city / "source" / "transit"
    out.mkdir(parents=True, exist_ok=True); src.mkdir(parents=True, exist_ok=True)

    # ---- lines: tile the physical rail network, dedupe ways by id ----
    ways = {}
    for bb in tiles(bbox):
        try:
            j = overpass(q_rail(bb))
        except RuntimeError as e:
            print(f"  [skip tile {bb}] {e}", file=sys.stderr); continue
        for el in j.get("elements", []):
            if el.get("type") == "way" and el.get("geometry") and el["id"] not in ways:
                ways[el["id"]] = el
        time.sleep(1)
    line_feats = []
    for el in ways.values():
        t = el.get("tags", {})
        line_feats.append({
            "type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": [[g["lon"], g["lat"]] for g in el["geometry"]]},
            "properties": {
                "name": t.get("name") or t.get("ref") or "",
                "usage": t.get("usage"),
                "operator": t.get("operator") or "Indian Railways",
                "decided_by": "Union (Indian Railways)",
                "source": "OpenStreetMap (railway=rail; first pass)",
            },
        })
    (out / "suburban_rail.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": line_feats}))

    # ---- stations: tile, dedupe by id ----
    snodes = {}
    for bb in tiles(bbox, 2, 2):
        try:
            j = overpass(q_stations(bb))
        except RuntimeError as e:
            print(f"  [skip stn tile {bb}] {e}", file=sys.stderr); continue
        for el in j.get("elements", []):
            if el.get("type") == "node" and "lat" in el and el["id"] not in snodes:
                snodes[el["id"]] = el
        time.sleep(1)
    st_feats = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [el["lon"], el["lat"]]},
        "properties": {"name": (el.get("tags") or {}).get("name", "Station"),
                       "operator": (el.get("tags") or {}).get("operator") or "Indian Railways",
                       "source": "OpenStreetMap"},
    } for el in snodes.values()]
    (out / "suburban_rail_stations.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": st_feats}))

    (src / "suburban_rail.sources.json").write_text(json.dumps({
        "layer": "suburban_rail",
        "publisher": "OpenStreetMap contributors",
        "licence": "ODbL",
        "decided_by": "Union — Indian Railways (Railways = Union List, Entry 22)",
        "trust": "NON-AUTHORITATIVE (OSM) — illustrative network geometry, first pass",
        "under_construction": bool(CONSTRUCTION.get(city)),
        "to_improve": "filter freight/yard ways; dedupe with metro; verify route membership; add divisions",
        "citation": "OpenStreetMap contributors -> sevent4 (first pass)",
    }, indent=1))

    note = " (network largely UNDER CONSTRUCTION)" if CONSTRUCTION.get(city) else ""
    print(f"[{city}] {len(line_feats)} route lines · {len(st_feats)} stations{note}", file=sys.stderr)
    return len(line_feats), len(st_feats)


if __name__ == "__main__":
    for c in (sys.argv[1:] or ["kolkata"]):
        build(c)
