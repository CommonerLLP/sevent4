"""Pure shaping for the first-pass suburban/commuter rail layer from OSM
(Overpass): bbox tiling, the rail/station query builders, element dedup +
GeoJSON feature shaping, and the provenance record. No network/IO here.

NOTE: the original recipe was corrupted (`.encode`, `.read`, `.lower`, `.values`
missing their parentheses); repaired here as part of the fix-and-refactor.
"""
from __future__ import annotations

# (south, west, north, east) — generous, to capture the network beyond the corp boundary
BBOX = {
    "kolkata":   (21.50, 86.00, 24.50, 89.90),
    "chennai":   (12.55, 79.55, 13.32, 80.40),
    "mumbai":    (18.75, 72.70, 19.45, 73.35),
    "bengaluru": (12.70, 77.30, 13.25, 77.95),
}
CONSTRUCTION = {"bengaluru": True}


def tiles(bbox, nx=3, ny=3):
    s, w, n, e = bbox
    dy, dx = (n - s) / ny, (e - w) / nx
    for i in range(ny):
        for j in range(nx):
            yield (round(s + i * dy, 4), round(w + j * dx, 4),
                   round(s + (i + 1) * dy, 4), round(w + (j + 1) * dx, 4))


def q_rail(bb) -> str:
    s, w, n, e = bb
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


def collect_ways(elements, ways: dict) -> None:
    for el in elements:
        if el.get("type") == "way" and el.get("geometry") and el["id"] not in ways:
            ways[el["id"]] = el


def collect_stations(elements, snodes: dict) -> None:
    for el in elements:
        if (
            el.get("type") == "node"
            and "lat" in el
            and el["id"] not in snodes
            and not _is_metro_station(el.get("tags", {}))
        ):
            snodes[el["id"]] = el


def line_features(ways: dict) -> list[dict]:
    feats = []
    for el in ways.values():
        t = el.get("tags", {})
        feats.append({
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
    return feats


def station_features(snodes: dict) -> list[dict]:
    features = []
    for el in snodes.values():
        tags = el.get("tags") or {}
        props = {
            "name": tags.get("name", "Station"),
            "operator": tags.get("operator") or "Indian Railways",
            "source": "OpenStreetMap",
        }
        if tags.get("kolkata_suburban_line"):
            props["line"] = tags["kolkata_suburban_line"]
        if tags.get("membership_source"):
            props["membership_source"] = tags["membership_source"]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [el["lon"], el["lat"]]},
                "properties": props,
            }
        )
    return features


def _is_metro_station(tags: dict) -> bool:
    text = " ".join(
        str(tags.get(key, ""))
        for key in ("name", "operator", "network", "station", "railway:ref")
    ).lower()
    return "metro" in text or "kmrc" in text


def rail_sources(city: str) -> dict:
    return {
        "layer": "suburban_rail",
        "publisher": "OpenStreetMap contributors",
        "licence": "ODbL",
        "decided_by": "Union — Indian Railways (Railways = Union List, Entry 22)",
        "trust": "NON-AUTHORITATIVE (OSM) — illustrative network geometry, first pass",
        "under_construction": bool(CONSTRUCTION.get(city)),
        "to_improve": "filter freight/yard ways; dedupe with metro; verify route membership; add divisions",
        "citation": "OpenStreetMap contributors -> sevent4 (first pass)",
    }
