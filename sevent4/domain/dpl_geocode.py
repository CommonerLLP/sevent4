"""Pure Delhi-DPL geocoding logic: address cleaning, map-pin coordinate
extraction, Google-precision confidence labels, and output-row shaping. No
network or filesystem IO.
"""
from __future__ import annotations

import re

FIXED = {"fixed_library", "zonal_library", "sub_branch_library", "community_library"}
GOOD_PRECISION = {"ROOFTOP", "RANGE_INTERPOLATED"}

OUTPUT_FIELDS = [
    "library_id", "name", "location_type", "is_fixed", "zone",
    "latitude", "longitude", "geocode_confidence", "geocode_provider",
    "geocode_label", "address",
]

# Prefer the !3d/!4d place pin over the @lat,lng viewport centre or a q= param.
_PIN_PATTERNS = (
    r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)",
    r"@(-?\d+\.\d+),(-?\d+\.\d+)",
    r"[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)",
)


def clean(addr, name) -> str:
    a = str(addr or "").strip()
    a = a.replace("Delhi Public Library,", "").strip(" ,")
    if not a or a.lower() == "nan":
        a = str(name)
    if "delhi" not in a.lower():
        a += ", Delhi"
    if "india" not in a.lower():
        a += ", India"
    return a


def extract_pin_coords(resolved_url: str):
    """Return (lat, lon) from a resolved Google Maps URL, or (None, None)."""
    for pattern in _PIN_PATTERNS:
        match = re.search(pattern, resolved_url)
        if match:
            return float(match.group(1)), float(match.group(2))
    return None, None


def google_confidence(precision: str) -> str:
    return "google_verified" if precision in GOOD_PRECISION else "google_approx"


def is_present(value) -> bool:
    """True for a non-empty, non-NaN cell (empty CSV cells read as '')."""
    text = "" if value is None else str(value).strip()
    return bool(text) and text.lower() != "nan"


def output_row(source, is_fixed, lat, lon, confidence, provider, label) -> dict:
    return {
        "library_id": source.get("library_id"),
        "name": source.get("name"),
        "location_type": source.get("location_type"),
        "is_fixed": is_fixed,
        "zone": source.get("zone"),
        "latitude": lat,
        "longitude": lon,
        "geocode_confidence": confidence,
        "geocode_provider": provider,
        "geocode_label": label,
        "address": source.get("address"),
    }
