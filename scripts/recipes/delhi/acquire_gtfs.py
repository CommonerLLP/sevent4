#!/usr/bin/env python3
"""Ingest a GTFS feed (zip or extracted dir) into atlas layer GeoJSONs.

The headline gap in the Delhi console is bus *route* line geometry: OSM gives us
metro lines, bus stops and roads, but not the DTC / cluster (DIMTS) route network.
The Open Transit Data (OTD) Delhi portal -- https://otd.delhi.gov.in -- publishes a
free static GTFS bundle (agency / calendar / stops / routes / trips / stop_times /
fares) for DTC + DIMTS cluster buses. It does NOT ship shapes.txt, so this recipe
reconstructs one LineString per route from the ordered stop sequence of a
representative trip. If a feed *does* carry shapes.txt (e.g. the DMRC rail feed),
the richer shape geometry is used instead.

Outputs (into data/cities/delhi/layers/):
  bus_routes.geojson  -- one LineString per route (route_short_name/route_long_name,
                         agency_id, n_stops); from shapes.txt if present, else
                         reconstructed from stop_times.
  bus_stops.geojson   -- all stops from stops.txt (stop_name, stop_code, stop_id).

Usage:
    .venv/bin/python scripts/recipes/delhi/acquire_gtfs.py --zip /path/to/GTFS.zip
    .venv/bin/python scripts/recipes/delhi/acquire_gtfs.py --dir /path/to/extracted
    # If neither is given, attempts a live download from the OTD static endpoint.

OTD API key:
  The *static* GTFS download needs NO key (it is a public CSRF-protected POST form).
  The *real-time* GTFS-RT feeds (VehiclePositions / TripUpdates) DO need a free
  per-user key, read ONLY from the environment:
      export OTD_API_KEY=...        # never hardcode -- this is a public repo
  This recipe never embeds a key and never commits one.

Prefixes (--prefix): set output basenames, e.g. --prefix metro writes
metro_routes.geojson / metro_stops.geojson (used for the DMRC feed).
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
LAYERS = ROOT / "data/cities/delhi/layers"

# OTD static GTFS download (public form; no key). Realtime needs OTD_API_KEY.
OTD_STATIC_URL = "https://otd.delhi.gov.in/data/static/"
UA = "sevent4-atlas/1.0 (74th-amendment atlas)"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def _read_csv(buf, **kw) -> pd.DataFrame:
    return pd.read_csv(buf, dtype=str, keep_default_na=False, **kw)


def load_feed(zip_path: str | None, dir_path: str | None) -> dict[str, pd.DataFrame]:
    """Return {filename_stem: DataFrame} for the GTFS tables we care about."""
    want = ("routes", "trips", "stops", "stop_times", "shapes", "agency")
    tables: dict[str, pd.DataFrame] = {}
    if dir_path:
        d = Path(dir_path)
        for name in want:
            f = d / f"{name}.txt"
            if f.exists():
                tables[name] = _read_csv(f)
    elif zip_path:
        with zipfile.ZipFile(zip_path) as zf:
            names = {Path(n).name: n for n in zf.namelist()}
            for name in want:
                if f"{name}.txt" in names:
                    with zf.open(names[f"{name}.txt"]) as fh:
                        tables[name] = _read_csv(io.TextIOWrapper(fh, "utf-8"))
    else:
        raise ValueError("need --zip or --dir")
    return tables


def download_otd_static(dest: Path, verify: bool = True) -> Path:
    """Download the public OTD static GTFS bundle (no API key). The endpoint is a
    Django CSRF-protected POST form; we fetch the token, then post name/email/purpose.

    TLS is verified by default. The OTD portal sometimes serves an expired cert; if
    so this raises an SSLError — pass --insecure to override (verify=False). We never
    silently disable verification, and the unpacked zip is sha256-logged either way.
    The recommended path is --zip with a pre-downloaded bundle (no network at all).
    """
    import requests

    s = requests.Session()
    s.headers["User-Agent"] = UA
    g = s.get(OTD_STATIC_URL, timeout=60, verify=verify)
    g.raise_for_status()
    token = ""
    for line in g.text.splitlines():
        if "csrfmiddlewaretoken" in line and "value=" in line:
            token = line.split("value=")[1].strip().strip("'\"").split(">")[0].strip("'\" ")
            break
    email = os.environ.get("OTD_EMAIL", "research@example.org")
    r = s.post(
        OTD_STATIC_URL,
        data={
            "csrfmiddlewaretoken": token,
            "dataDownloaded": "routes",  # any value triggers the full GTFS.zip
            "name": "research",
            "email": email,
            "purpose": "academic municipalities atlas",
        },
        headers={"Referer": OTD_STATIC_URL},
        timeout=180,
        verify=verify,
    )
    r.raise_for_status()
    if "zip" not in r.headers.get("Content-Type", ""):
        raise RuntimeError(f"OTD did not return a zip (got {r.headers.get('Content-Type')})")
    dest.write_bytes(r.content)
    import hashlib
    print(f"  downloaded {len(r.content)} bytes, sha256={hashlib.sha256(r.content).hexdigest()}")
    return dest


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
def build_stops(stops: pd.DataFrame) -> dict:
    feats = []
    for _, row in stops.iterrows():
        try:
            lon, lat = float(row["stop_lon"]), float(row["stop_lat"])
        except (ValueError, KeyError):
            continue
        if not (lon and lat):
            continue
        feats.append({
            "type": "Feature",
            "properties": {
                "stop_name": row.get("stop_name", ""),
                "stop_code": row.get("stop_code", ""),
                "stop_id": row.get("stop_id", ""),
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
        })
    return {"type": "FeatureCollection", "features": feats}


def _route_props(routes: pd.DataFrame) -> dict[str, dict]:
    by_id = {}
    for _, r in routes.iterrows():
        by_id[r["route_id"]] = {
            "route_id": r.get("route_id", ""),
            "route_short_name": r.get("route_short_name", ""),
            "route_long_name": r.get("route_long_name", ""),
            "agency_id": r.get("agency_id", ""),
            "route_type": r.get("route_type", ""),
        }
    return by_id


def build_routes_from_shapes(routes, trips, shapes) -> dict:
    """One LineString per route_id using the longest associated shape."""
    shapes = shapes.copy()
    shapes["shape_pt_sequence"] = shapes["shape_pt_sequence"].astype(int)
    shapes["shape_pt_lat"] = shapes["shape_pt_lat"].astype(float)
    shapes["shape_pt_lon"] = shapes["shape_pt_lon"].astype(float)
    # representative shape per route = the one with most points
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
    """Reconstruct one LineString per route_id from the ordered stop sequence of a
    representative trip (the trip with the most stops). Used when shapes.txt is
    absent -- as in the OTD DTC/DIMTS feed.
    """
    stop_xy = {}
    for _, s in stops.iterrows():
        try:
            stop_xy[s["stop_id"]] = (float(s["stop_lon"]), float(s["stop_lat"]))
        except (ValueError, KeyError):
            continue

    st = stop_times[["trip_id", "stop_id", "stop_sequence"]].copy()
    st["stop_sequence"] = pd.to_numeric(st["stop_sequence"], errors="coerce")
    st = st.dropna(subset=["stop_sequence"])
    # stops-per-trip, to pick the most complete trip per route
    trip_len = st.groupby("trip_id").size()
    trip_route = dict(zip(trips["trip_id"], trips["route_id"]))

    # best (longest) trip per route
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


# ---------------------------------------------------------------------------
def write_geojson(fc: dict, path: Path) -> int:
    import json
    path.write_text(json.dumps(fc), encoding="utf-8")
    return len(fc["features"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--zip", help="path to a GTFS .zip")
    g.add_argument("--dir", help="path to an extracted GTFS dir")
    ap.add_argument("--download", action="store_true",
                    help="download the public OTD static GTFS bundle (no key)")
    ap.add_argument("--prefix", default="bus",
                    help="output basename prefix (default 'bus' -> bus_routes/bus_stops)")
    ap.add_argument("--out", default=str(LAYERS), help="output layers dir")
    ap.add_argument("--insecure", action="store_true",
                    help="skip TLS verification for --download (only if OTD's cert is "
                         "expired; static open-gov data, no credentials sent)")
    args = ap.parse_args()

    zip_path = args.zip
    if args.download and not zip_path and not args.dir:
        import tempfile
        zip_path = str(Path(tempfile.gettempdir()) / "otd_gtfs.zip")
        print(f"downloading OTD static GTFS -> {zip_path}", file=sys.stderr)
        download_otd_static(Path(zip_path), verify=not args.insecure)

    if not zip_path and not args.dir:
        ap.error("provide --zip, --dir, or --download")

    tables = load_feed(zip_path, args.dir)
    for required in ("routes", "trips", "stops"):
        if required not in tables:
            ap.error(f"feed is missing {required}.txt")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    n_stops = write_geojson(build_stops(tables["stops"]), out / f"{args.prefix}_stops.geojson")

    if "shapes" in tables and not tables["shapes"].empty:
        routes_fc = build_routes_from_shapes(tables["routes"], tables["trips"], tables["shapes"])
        method = "shapes.txt"
    elif "stop_times" in tables:
        routes_fc = build_routes_from_stop_times(
            tables["routes"], tables["trips"], tables["stops"], tables["stop_times"])
        method = "reconstructed from stop_times"
    else:
        ap.error("feed has neither shapes.txt nor stop_times.txt -- cannot build route lines")

    n_routes = write_geojson(routes_fc, out / f"{args.prefix}_routes.geojson")
    print(f"{args.prefix}: {n_routes} routes ({method}), {n_stops} stops")


if __name__ == "__main__":
    main()
