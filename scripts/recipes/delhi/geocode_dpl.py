#!/usr/bin/env python3
"""Geocode Delhi Public Library locations (thin CLI wrapper).

Prefers Google Maps Geocoding when GOOGLE_MAPS_API_KEY is set, falling back to a
DPL-published map pin and then Nominatim. Address cleaning, pin extraction, and
confidence labelling live in sevent4.domain.dpl_geocode; the resolution order in
sevent4.application.dpl_geocode; all network/CSV IO in the dpl-geocode adapter.

SECURITY: the API key is read ONLY from the environment — never hardcode it; this
is a public repo. Run as:
    GOOGLE_MAPS_API_KEY=... .venv/bin/python scripts/recipes/delhi/geocode_dpl.py

Output: data/cities/delhi/derived/geocoding/dpl_geocoded.csv
"""
from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

from sevent4.adapters.dpl_geocode_net import DplGeocoder, read_source_rows, write_geocoded
from sevent4.application.dpl_geocode import geocode_locations
from sevent4.domain.dpl_geocode import FIXED, OUTPUT_FIELDS

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data/cities/delhi/source/libraries/dpl_library_locations.csv"
OUT = ROOT / "data/cities/delhi/derived/geocoding/dpl_geocoded.csv"


def main() -> None:
    source_rows = read_source_rows(SRC)
    geocoder = DplGeocoder(os.environ.get("GOOGLE_MAPS_API_KEY", ""))
    fixed = sum(1 for row in source_rows if row.get("location_type") in FIXED)
    have_link = sum(1 for row in source_rows if (row.get("map_url") or "").strip())
    print(f"{len(source_rows)} total DPL locations ({fixed} fixed, "
          f"{len(source_rows) - fixed} mobile); {have_link} have a DPL map link; "
          f"google={'ON' if geocoder.has_google else 'off'}")
    rows = geocode_locations(source_rows, geocoder)
    write_geocoded(OUT, rows, OUTPUT_FIELDS)
    located = sum(1 for row in rows if row["latitude"] not in (None, ""))
    breakdown = dict(Counter(row["geocode_confidence"] for row in rows))
    print(f"\nwrote {OUT.relative_to(ROOT)}: {located}/{len(rows)} located; confidence={breakdown}")


if __name__ == "__main__":
    main()
