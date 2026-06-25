"""Orchestrate Delhi-DPL geocoding: prefer source-verified coordinates, then the
DPL-published map pin, then Google, then Nominatim. Network IO is injected via a
geocoder port; this layer owns only the resolution order and output shaping.
"""
from __future__ import annotations

from sevent4.domain.dpl_geocode import (
    FIXED,
    clean,
    google_confidence,
    is_present,
    output_row,
)


def geocode_locations(source_rows, geocoder) -> list[dict]:
    rows: list[dict] = []
    for source in source_rows:
        is_fixed = source.get("location_type") in FIXED
        lat = source.get("latitude") if is_present(source.get("latitude")) else None
        lon = source.get("longitude") if is_present(source.get("longitude")) else None
        confidence = provider = label = None
        if lat is not None and lon is not None:
            confidence, provider = "verified", str(source.get("coordinate_source") or "source")
        elif is_present(source.get("map_url")):  # DPL-published map pin — authoritative
            lat, lon, label = geocoder.resolve_maps_url(str(source["map_url"]))
            if lat is not None:
                confidence, provider = "dpl_maps_pin", "dpl_google_maps"
        if lat is None:  # geocode by address
            query = clean(source.get("address"), source.get("name"))
            if geocoder.has_google:
                lat, lon, label, precision = geocoder.geocode_google(query)
                if lat is None:
                    lat, lon, label, precision = geocoder.geocode_google(
                        f"{source.get('name', '')}, Delhi, India"
                    )
                if lat is not None:
                    confidence, provider = google_confidence(precision), f"google:{precision}"
            if lat is None:  # Nominatim fallback
                lat, lon, label = geocoder.geocode_nominatim(query)
                if lat is not None:
                    confidence, provider = "nominatim_approx", "nominatim"
        if lat is None:
            confidence, provider = "failed", None
        print(f"  [{'FIX' if is_fixed else 'mob'}] {str(source.get('name'))[:38]:38s} -> {confidence}")
        rows.append(output_row(source, is_fixed, lat, lon, confidence, provider, label))
    return rows
