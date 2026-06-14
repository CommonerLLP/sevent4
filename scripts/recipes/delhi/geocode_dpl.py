#!/usr/bin/env python3
"""Geocode Delhi Public Library locations.

Prefers the Google Maps Geocoding API when GOOGLE_MAPS_API_KEY is set in the
environment (accurate, ROOFTOP/RANGE precision), falling back to Nominatim (OSM).
Source-verified coordinates are kept as-is. Focus on the fixed network
(fixed/zonal/sub-branch/community libraries).

SECURITY: the API key is read ONLY from the environment — never hardcode it; this
is a public repo. Run as:
    GOOGLE_MAPS_API_KEY=... .venv/bin/python scripts/recipes/delhi/geocode_dpl.py

Output: data/cities/delhi/derived/geocoding/dpl_geocoded.csv
"""
from __future__ import annotations

import os
import pathlib
import re
import time

import pandas as pd
import requests

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "data/cities/delhi/source/libraries/dpl_library_locations.csv"
OUT = ROOT / "data/cities/delhi/derived/geocoding/dpl_geocoded.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

UA = "r2r-atlas-research/1.0"
GKEY = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
FIXED = {"fixed_library", "zonal_library", "sub_branch_library", "community_library"}
# Google precision -> our confidence label
_G_GOOD = {"ROOFTOP", "RANGE_INTERPOLATED"}


def clean(addr: str, name: str) -> str:
    a = str(addr or "").strip()
    a = a.replace("Delhi Public Library,", "").strip(" ,")
    if not a or a.lower() == "nan":
        a = str(name)
    if "delhi" not in a.lower():
        a += ", Delhi"
    if "india" not in a.lower():
        a += ", India"
    return a


def resolve_maps_url(url: str):
    """Resolve a DPL-published goo.gl/maps shortlink to its place-pin coordinates.
    Prefers the !3d<lat>!4d<lon> place pin over the @lat,lng viewport centre."""
    try:
        r = requests.get(url, allow_redirects=True, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        u = r.url
        m = (re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", u)
             or re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", u)
             or re.search(r"[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)", u))
        if m:
            return float(m.group(1)), float(m.group(2)), u
    except Exception as e:
        print("  maps-url err", e)
    return None, None, None


def geocode_google(q: str):
    """Return (lat, lon, formatted, precision) via Google, or Nones."""
    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": q, "key": GKEY, "region": "in",
                    "bounds": "28.40,76.83|28.89,77.36"}, timeout=20,
        )
        j = r.json()
        if j.get("status") == "OK" and j.get("results"):
            top = j["results"][0]
            loc = top["geometry"]["location"]
            return loc["lat"], loc["lng"], top.get("formatted_address", ""), top["geometry"].get("location_type", "")
    except Exception as e:
        print("  google err", e)
    return None, None, None, None


def geocode(q: str):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1, "countrycodes": "in"},
            headers={"User-Agent": UA}, timeout=20,
        )
        if r.status_code == 200 and r.json():
            j = r.json()[0]
            return float(j["lat"]), float(j["lon"]), j.get("display_name", "")
    except Exception as e:
        print("  err", e)
    return None, None, None


def main():
    df = pd.read_csv(SRC)
    rows = []
    print(f"{len(df)} total DPL locations ({df['location_type'].isin(FIXED).sum()} fixed, "
          f"{(~df['location_type'].isin(FIXED)).sum()} mobile); "
          f"{df['map_url'].notna().sum()} have a DPL map link; google={'ON' if GKEY else 'off'}")
    for _, r in df.iterrows():
        lat, lon, conf, prov, label = r.get("latitude"), r.get("longitude"), None, None, None
        lat = None if pd.isna(lat) else lat   # empty cells read as NaN, not None
        lon = None if pd.isna(lon) else lon
        is_fixed = r["location_type"] in FIXED
        if lat is not None and lon is not None:
            conf, prov = "verified", str(r.get("coordinate_source") or "source")
        elif pd.notna(r.get("map_url")):  # DPL-published map pin — authoritative
            lat, lon, label = resolve_maps_url(str(r["map_url"]))
            if lat is not None:
                conf, prov = "dpl_maps_pin", "dpl_google_maps"
            time.sleep(0.2)
        if lat is None:  # geocode by address
            q = clean(r.get("address"), r.get("name"))
            if GKEY:
                lat, lon, label, prec = geocode_google(q)
                if lat is None:
                    lat, lon, label, prec = geocode_google(f"{r['name']}, Delhi, India")
                if lat is not None:
                    conf = "google_verified" if prec in _G_GOOD else "google_approx"
                    prov = f"google:{prec}"
                time.sleep(0.1)
            if lat is None:  # Nominatim fallback
                lat, lon, label = geocode(q)
                time.sleep(1.1)
                if lat is not None:
                    conf, prov = "nominatim_approx", "nominatim"
        if lat is None:
            conf, prov = "failed", None
        print(f"  [{'FIX' if is_fixed else 'mob'}] {str(r['name'])[:38]:38s} -> {conf}")
        rows.append({
            "library_id": r["library_id"], "name": r["name"],
            "location_type": r["location_type"], "is_fixed": is_fixed, "zone": r.get("zone"),
            "latitude": lat, "longitude": lon, "geocode_confidence": conf,
            "geocode_provider": prov, "geocode_label": label, "address": r.get("address"),
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    ok = out["latitude"].notna().sum()
    breakdown = out["geocode_confidence"].value_counts().to_dict()
    print(f"\nwrote {OUT.relative_to(ROOT)}: {ok}/{len(out)} located; confidence={breakdown}")


if __name__ == "__main__":
    main()
