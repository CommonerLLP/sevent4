#!/usr/bin/env python3
"""Geocode Delhi Public Library locations via Nominatim (OSM).

User explicitly approved Nominatim geocoding for the Delhi maps. Coordinates are
marked `nominatim_approx` confidence; the 5 already-verified rows are kept as-is.
Focus on the fixed network (fixed/zonal/sub-branch/community libraries); mobile
service points are geocoded best-effort.

Output: data/cities/delhi/derived/geocoding/dpl_geocoded.csv
"""
from __future__ import annotations

import pathlib
import time

import pandas as pd
import requests

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "data/cities/delhi/source/libraries/dpl_library_locations.csv"
OUT = ROOT / "data/cities/delhi/derived/geocoding/dpl_geocoded.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

UA = "r2r-atlas-research/1.0"
FIXED = {"fixed_library", "zonal_library", "sub_branch_library", "community_library"}


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
    fixed = df[df["location_type"].isin(FIXED)].copy()
    print(f"{len(fixed)} fixed-network locations; {fixed['latitude'].notna().sum()} already have coords")
    for _, r in fixed.iterrows():
        lat, lon, conf, prov, label = r.get("latitude"), r.get("longitude"), None, None, None
        if pd.notna(lat) and pd.notna(lon):
            conf, prov = "verified", str(r.get("coordinate_source") or "source")
        else:
            q = clean(r.get("address"), r.get("name"))
            lat, lon, label = geocode(q)
            time.sleep(1.1)
            if lat is None:  # fallback to name-based query
                lat, lon, label = geocode(f"{r['name']}, Delhi, India")
                time.sleep(1.1)
            conf = "nominatim_approx" if lat is not None else "failed"
            prov = "nominatim" if lat is not None else None
            print(f"  {r['name'][:40]:40s} -> {conf}")
        rows.append({
            "library_id": r["library_id"], "name": r["name"],
            "location_type": r["location_type"], "zone": r.get("zone"),
            "latitude": lat, "longitude": lon, "geocode_confidence": conf,
            "geocode_provider": prov, "geocode_label": label, "address": r.get("address"),
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    ok = out["latitude"].notna().sum()
    print(f"\nwrote {OUT.relative_to(ROOT)}: {ok}/{len(out)} located "
          f"({(out['geocode_confidence']=='nominatim_approx').sum()} via Nominatim, "
          f"{(out['geocode_confidence']=='verified').sum()} pre-verified, "
          f"{(out['geocode_confidence']=='failed').sum()} failed)")


if __name__ == "__main__":
    main()
