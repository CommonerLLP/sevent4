"""Pure transforms for Delhi acquisition recipes (boundaries, OpenCity harvest,
OSM/Overpass, GTFS). No network or filesystem IO lives here — adapters fetch
bytes/tables and these shape geometry, manifests, and provenance.
"""
from __future__ import annotations

import re

# ============================ boundaries ============================

DM = "https://raw.githubusercontent.com/datameet"
AC_BASE = f"{DM}/maps/master/assembly-constituencies/India_AC"
PC_URL = f"{DM}/maps/master/parliamentary-constituencies/india_pc_2019_simplified.geojson"
WARDS_URL = f"{DM}/Municipal_Spatial_Data/master/Delhi/Delhi_Wards.geojson"

BOUNDARY_SOURCES = {
    "acs": {
        "url": f"{AC_BASE}.shp",
        "label": "Delhi Assembly Constituencies (70)",
        "publisher": "Election Commission of India delimitation, via DataMeet datameet/maps",
        "vintage": "current (2008 delimitation order, in force)",
        "license": "DataMeet community data",
    },
    "pcs": {
        "url": PC_URL,
        "label": "Delhi Parliamentary Constituencies (7)",
        "publisher": "Election Commission of India 2019, via DataMeet datameet/maps",
        "vintage": "current",
        "license": "DataMeet community data",
    },
    "wards": {
        "url": WARDS_URL,
        "label": "Delhi municipal wards (INTERIM, pre-2022)",
        "publisher": "DataMeet datameet/Municipal_Spatial_Data (scraped from ArcGIS Online)",
        "vintage": "PRE-2022 (~290 features incl. NDMC + Cantonment charges); "
                   "predates the 2022 unified-MCD 250-ward delimitation",
        "license": "CC BY-SA 2.5 IN",
    },
}


def boundary_credits_md(sources: dict, counts: dict) -> str:
    return (
        "# Delhi boundary spine — provenance\n\n"
        "| Layer | Features | Source | Vintage |\n|---|---|---|---|\n"
        f"| ACs | {counts['acs']} | {sources['acs']['publisher']} | {sources['acs']['vintage']} |\n"
        f"| PCs | {counts['pcs']} | {sources['pcs']['publisher']} | {sources['pcs']['vintage']} |\n"
        f"| Districts | {counts['districts']} | dissolved from ACs (DIST_NAME) | derived (none: DIST_NAME blank) |\n"
        f"| Wards | {counts['wards']} | {sources['wards']['publisher']} | {sources['wards']['vintage']} |\n\n"
        "**Ward caveat:** the 2022 unified-MCD 250-ward delimitation geometry is not "
        "openly available (SEC-Delhi published PDFs only). The ward layer here is the "
        "pre-2022 set, shipped as labelled interim. ACs and PCs are current.\n"
    )


# ============================ OpenCity harvest ============================

OPENCITY_KEEP = {"CSV", "GEOJSON", "KML", "XLSX", "JSON"}


def slugify(s: str, fallback: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", (s or "").strip())[:80].strip("_")
    return s or fallback


def usable_opencity_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["resource_format"].upper() in OPENCITY_KEEP and r["resource_url"]]


def skipped_opencity_formats(rows: list[dict]) -> list[str]:
    return sorted({r["resource_format"].upper() for r in rows if r["resource_format"].upper() not in OPENCITY_KEEP})


def opencity_record(row: dict, local_rel: str, size: int, sha: str, status: str) -> dict:
    return {
        "dataset": row["dataset_title"], "organization": row["organization"],
        "axis": row["axis_labels"], "format": row["resource_format"],
        "url": row["resource_url"], "local": local_rel,
        "bytes": size, "sha256": sha, "status": status,
    }


def opencity_manifest(records: list[dict], skipped_formats: list[str]) -> dict:
    ok = [m for m in records if m["status"] == "ok"]
    return {
        "downloaded": len(ok), "failed": len(records) - len(ok),
        "skipped_formats": skipped_formats, "total_bytes": sum(m["bytes"] for m in ok),
        "resources": records,
    }


# ============================ OSM / Overpass ============================

OSM_BBOX = (28.4043, 76.8388, 28.8835, 77.3475)  # S,W,N,E (NCT)

OSM_POINT_QUERIES = {
    "metro":   ('node["station"="subway"];node["railway"="station"]["station"="subway"];', "name", "#5c8af2"),
    "stops":   ('node["highway"="bus_stop"];', "name", "#9ca3ad"),
    "health":  ('node["amenity"~"hospital|clinic"];way["amenity"~"hospital|clinic"];', "name", "#49a35f"),
    "schools": ('node["amenity"="school"];way["amenity"="school"];', "name", "#1e9f8f"),
    "police":  ('node["amenity"="police"];way["amenity"="police"];', "name", "#4d76c7"),
    "fire":    ('node["amenity"="fire_station"];way["amenity"="fire_station"];', "name", "#db4c45"),
    "toilets": ('node["amenity"="toilets"];', "name", "#46c1b4"),
}
OSM_LINE_QUERIES = {
    "metro_lines": ('way["railway"="subway"];', "name", "#dc4c4c"),
    "rrts":        ('way["railway"="rail"]["usage"="main"]["name"~"Namo|RRTS|Rapid",i];'
                    'relation["route"="train"]["name"~"Namo|RRTS|Rapid",i];', "name", "#9b59b6"),
    "rail":        ('way["railway"="rail"]["usage"="main"];', "name", "#8a8f98"),
    "roads":       ('way["highway"~"^(motorway|trunk|primary)$"];', "name", "#58606d"),
}
OSM_LABELS = {
    "metro": "Metro stations", "stops": "Bus stops", "health": "Health facilities",
    "schools": "Schools", "police": "Police", "fire": "Fire & emergency",
    "toilets": "Public toilets", "metro_lines": "Metro lines", "rrts": "RRTS (Namo Bharat)",
    "rail": "Railway (suburban)", "roads": "Major roads",
}
OSM_GROUPS = {"metro": "Transit", "metro_lines": "Transit", "stops": "Transit",
              "rrts": "Transit", "rail": "Transit", "roads": "Mobility"}
OSM_DEFAULTS = {"metro", "metro_lines", "rrts"}
OSM_LINE_WIDTH = {"roads": 0.6, "rail": 1.1, "rrts": 2.8, "metro_lines": 2.2}


def overpass_query(body: str, bbox=OSM_BBOX) -> str:
    s, w, n, e = bbox
    return "[out:json][timeout:90];(" + "".join(
        f"{sel.strip()}({s},{w},{n},{e});" for sel in body.split(";") if sel.strip()
    ) + ");out geom;"


def osm_points(data: dict, field: str) -> dict:
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


def osm_lines(data: dict, field: str) -> dict:
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


def osm_line_entry(lid: str, color: str) -> dict:
    return {"id": lid, "label": OSM_LABELS[lid], "file": f"{lid}.geojson", "kind": "line",
            "group": OSM_GROUPS.get(lid, "Mobility"), "default": lid in OSM_DEFAULTS, "popup": ["name"],
            "paint": {"line-color": color, "line-width": OSM_LINE_WIDTH.get(lid, 1.6),
                      "line-opacity": 0.85 if lid == "roads" else 0.9}}


def osm_point_entry(lid: str, color: str) -> dict:
    return {"id": lid, "label": OSM_LABELS[lid], "file": f"{lid}.geojson", "kind": "circle",
            "group": OSM_GROUPS.get(lid, "Public services"), "default": lid in OSM_DEFAULTS, "popup": ["name"],
            "paint": {"circle-color": color, "circle-radius": 3.2, "circle-stroke-color": "#101318",
                      "circle-stroke-width": 0.6, "circle-opacity": 0.85}}


def merge_layer_entries(manifest: dict, entries: list[dict]) -> dict:
    ids = {layer["id"] for layer in manifest["layers"]}
    for e in entries:
        manifest["layers"] = (
            [e if layer["id"] == e["id"] else layer for layer in manifest["layers"]]
            if e["id"] in ids else manifest["layers"] + [e]
        )
        ids.add(e["id"])
    return manifest


# ============================ GTFS geometry ============================

def build_stops(stops) -> dict:
    feats = []
    for _, row in stops.iterrows():
        try:
            lon, lat = float(row["stop_lon"]), float(row["stop_lat"])
        except (ValueError, KeyError):
            continue
        if not (lon and lat):
            continue
        feats.append({"type": "Feature", "properties": {
            "stop_name": row.get("stop_name", ""), "stop_code": row.get("stop_code", ""),
            "stop_id": row.get("stop_id", ""),
        }, "geometry": {"type": "Point", "coordinates": [lon, lat]}})
    return {"type": "FeatureCollection", "features": feats}


def _route_props(routes) -> dict[str, dict]:
    by_id = {}
    for _, r in routes.iterrows():
        by_id[r["route_id"]] = {
            "route_id": r.get("route_id", ""), "route_short_name": r.get("route_short_name", ""),
            "route_long_name": r.get("route_long_name", ""), "agency_id": r.get("agency_id", ""),
            "route_type": r.get("route_type", ""),
        }
    return by_id


def build_routes_from_shapes(routes, trips, shapes) -> dict:
    shapes = shapes.copy()
    shapes["shape_pt_sequence"] = shapes["shape_pt_sequence"].astype(int)
    shapes["shape_pt_lat"] = shapes["shape_pt_lat"].astype(float)
    shapes["shape_pt_lon"] = shapes["shape_pt_lon"].astype(float)
    shape_len = shapes.groupby("shape_id").size()
    route_shape: dict[str, str] = {}
    for rid, grp in trips.groupby("route_id"):
        sids = [s for s in grp["shape_id"].unique() if s and s in shape_len.index]
        if sids:
            route_shape[rid] = max(sids, key=lambda s: shape_len[s])
    props = _route_props(routes)
    feats = []
    for rid, sid in route_shape.items():
        g = shapes[shapes["shape_id"] == sid].sort_values("shape_pt_sequence")
        coords = list(zip(g["shape_pt_lon"], g["shape_pt_lat"]))
        if len(coords) < 2:
            continue
        p = dict(props.get(rid, {"route_id": rid}))
        p["n_points"] = len(coords)
        feats.append({"type": "Feature", "properties": p,
                      "geometry": {"type": "LineString", "coordinates": [[x, y] for x, y in coords]}})
    return {"type": "FeatureCollection", "features": feats}


def build_routes_from_stop_times(routes, trips, stops, stop_times) -> dict:
    import pandas as pd

    stop_xy = {}
    for _, s in stops.iterrows():
        try:
            stop_xy[s["stop_id"]] = (float(s["stop_lon"]), float(s["stop_lat"]))
        except (ValueError, KeyError):
            continue

    st = stop_times[["trip_id", "stop_id", "stop_sequence"]].copy()
    st["stop_sequence"] = pd.to_numeric(st["stop_sequence"], errors="coerce")
    st = st.dropna(subset=["stop_sequence"])
    trip_len = st.groupby("trip_id").size()
    trip_route = dict(zip(trips["trip_id"], trips["route_id"]))

    best_trip: dict[str, str] = {}
    best_len: dict[str, int] = {}
    for tid, n in trip_len.items():
        rid = trip_route.get(tid)
        if rid is None:
            continue
        if n > best_len.get(rid, 0):
            best_len[rid] = n
            best_trip[rid] = tid

    chosen = set(best_trip.values())
    seqs = (st[st["trip_id"].isin(chosen)]
            .sort_values(["trip_id", "stop_sequence"])
            .groupby("trip_id")["stop_id"].apply(list).to_dict())

    props = _route_props(routes)
    feats = []
    for rid, tid in best_trip.items():
        ids = seqs.get(tid, [])
        coords = [stop_xy[s] for s in ids if s in stop_xy]
        if len(coords) < 2:
            continue
        p = dict(props.get(rid, {"route_id": rid}))
        p["n_stops"] = len(coords)
        feats.append({"type": "Feature", "properties": p,
                      "geometry": {"type": "LineString", "coordinates": [[x, y] for x, y in coords]}})
    return {"type": "FeatureCollection", "features": feats}
