#!/usr/bin/env python3
"""Pull Delhi transit + service layers from OpenStreetMap (Overpass) into the
atlas. OSM is the standard open source for Delhi's well-mapped Metro network and
service points; boundaries still come from DataMeet (see acquire_boundaries.py).

Writes directly into data/cities/delhi/layers/ and registers each layer in
layer_manifest.json (idempotent), so it composes with the OpenCity layers
without re-running build_city.py.

    python3 scripts/recipes/delhi/acquire_osm.py

Layers: metro_lines (subway tracks), metro (stations), stops (bus), libraries,
health (hospitals/clinics), schools, police, fire, toilets.
"""
from __future__ import annotations
import json, time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
LAYERS = ROOT / "data/cities/delhi/layers"
OVERPASS = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas)"}
BBOX = (28.4043, 76.8388, 28.8835, 77.3475)  # S,W,N,E (NCT)

# layer id -> (geometry kind, Overpass selector body, popup field, paint)
POINT_QUERIES = {
    "metro":     ('node["station"="subway"];node["railway"="station"]["station"="subway"];', "name", "#5c8af2"),
    "stops":     ('node["highway"="bus_stop"];', "name", "#9ca3ad"),
    # NOTE: no generic OSM `libraries` layer for Delhi — the authoritative DPL fixed
    # network (build_library_spatial.py -> dpl_libraries.geojson) supersedes OSM's
    # partial amenity=library set, which only duplicated it confusingly.
    "health":    ('node["amenity"~"hospital|clinic"];way["amenity"~"hospital|clinic"];', "name", "#49a35f"),
    "schools":   ('node["amenity"="school"];way["amenity"="school"];', "name", "#1e9f8f"),
    "police":    ('node["amenity"="police"];way["amenity"="police"];', "name", "#4d76c7"),
    "fire":      ('node["amenity"="fire_station"];way["amenity"="fire_station"];', "name", "#db4c45"),
    "toilets":   ('node["amenity"="toilets"];', "name", "#46c1b4"),
}
LINE_QUERIES = {
    "metro_lines": ('way["railway"="subway"];', "name", "#dc4c4c"),
    "rrts":        ('way["railway"="rail"]["usage"="main"]["name"~"Namo|RRTS|Rapid",i];'
                    'relation["route"="train"]["name"~"Namo|RRTS|Rapid",i];', "name", "#9b59b6"),
    "rail":        ('way["railway"="rail"]["usage"="main"];', "name", "#8a8f98"),
    "roads":       ('way["highway"~"^(motorway|trunk|primary)$"];', "name", "#58606d"),
}
LABELS = {
    "metro": "Metro stations", "stops": "Bus stops",
    "health": "Health facilities", "schools": "Schools", "police": "Police",
    "fire": "Fire & emergency", "toilets": "Public toilets", "metro_lines": "Metro lines",
    "rrts": "RRTS (Namo Bharat)", "rail": "Railway (suburban)", "roads": "Major roads",
}
GROUPS = {"metro": "Transit", "metro_lines": "Transit", "stops": "Transit",
          "rrts": "Transit", "rail": "Transit", "roads": "Mobility"}
DEFAULTS = {"metro", "metro_lines", "rrts"}


def overpass(body: str) -> dict:
    s, w, n, e = BBOX
    # body is one or more selectors separated by ';'. Append the bbox to each.
    q = "[out:json][timeout:90];(" + "".join(
        f"{sel.strip()}({s},{w},{n},{e});" for sel in body.split(";") if sel.strip()
    ) + ");out geom;"
    for attempt in range(3):
        try:
            r = requests.post(OVERPASS, data={"data": q}, headers=UA, timeout=120)
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(8)
    return {"elements": []}


def points(data: dict, field: str) -> dict:
    feats = []
    for el in data.get("elements", []):
        if el["type"] == "node":
            lon, lat = el["lon"], el["lat"]
        elif el.get("center"):
            lon, lat = el["center"]["lon"], el["center"]["lat"]
        else:
            continue
        feats.append({"type": "Feature", "properties": {"name": el.get("tags", {}).get(field, "")},
                      "geometry": {"type": "Point", "coordinates": [lon, lat]}})
    return {"type": "FeatureCollection", "features": feats}


def lines(data: dict, field: str) -> dict:
    feats = []
    for el in data.get("elements", []):
        geom = el.get("geometry")
        if el["type"] != "way" or not geom:
            continue
        coords = [[p["lon"], p["lat"]] for p in geom]
        if len(coords) < 2:
            continue
        feats.append({"type": "Feature", "properties": {"name": el.get("tags", {}).get(field, "")},
                      "geometry": {"type": "LineString", "coordinates": coords}})
    return {"type": "FeatureCollection", "features": feats}


def register(entries: list[dict]) -> None:
    mp = LAYERS / "layer_manifest.json"
    m = json.loads(mp.read_text())
    ids = {l["id"] for l in m["layers"]}
    for e in entries:
        m["layers"] = [e if l["id"] == e["id"] else l for l in m["layers"]] if e["id"] in ids \
            else m["layers"] + [e]
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    entries, counts = [], {}
    width = {"roads": 0.6, "rail": 1.1, "rrts": 2.8, "metro_lines": 2.2}
    for lid, (body, field, color) in LINE_QUERIES.items():
        fc = lines(overpass(body), field)
        (LAYERS / f"{lid}.geojson").write_text(json.dumps(fc), encoding="utf-8")
        counts[lid] = len(fc["features"])
        if not fc["features"]:
            continue  # don't register an empty layer (e.g. RRTS may be unmapped in OSM)
        entries.append({"id": lid, "label": LABELS[lid], "file": f"{lid}.geojson", "kind": "line",
                        "group": GROUPS.get(lid, "Mobility"), "default": lid in DEFAULTS, "popup": ["name"],
                        "paint": {"line-color": color, "line-width": width.get(lid, 1.6),
                                  "line-opacity": 0.85 if lid == "roads" else 0.9}})
    for lid, (body, field, color) in POINT_QUERIES.items():
        fc = points(overpass(body), field)
        (LAYERS / f"{lid}.geojson").write_text(json.dumps(fc), encoding="utf-8")
        counts[lid] = len(fc["features"])
        entries.append({"id": lid, "label": LABELS[lid], "file": f"{lid}.geojson", "kind": "circle",
                        "group": GROUPS.get(lid, "Public services"), "default": lid in DEFAULTS, "popup": ["name"],
                        "paint": {"circle-color": color, "circle-radius": 3.2, "circle-stroke-color": "#101318",
                                  "circle-stroke-width": 0.6, "circle-opacity": 0.85}})
    register(entries)
    print("delhi OSM layers:", ", ".join(f"{k} {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
