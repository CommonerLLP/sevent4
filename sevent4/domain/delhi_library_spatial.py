"""Pure Delhi library-spatial logic: the 'libraries' atlas layer spec, the
mean-centre compass label, the geocoding confidence note, and the final spatial
stats shaping. No geospatial, matplotlib, or filesystem IO.
"""
from __future__ import annotations

from sevent4.domain.delhi_opencity import merge_layers  # re-used insert-or-replace by id

__all__ = ["libraries_layer_spec", "merge_layers", "compass_label",
           "confidence_note", "assemble_stats"]

_COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def libraries_layer_spec() -> dict:
    """The authoritative DPL fixed network IS Delhi's 'libraries' layer — present
    it like every other city: standard yellow circle, default on."""
    return {"id": "libraries", "label": "Libraries", "file": "dpl_libraries.geojson",
            "kind": "circle", "group": "Public services", "default": True,
            "popup": ["Name", "location_type", "zone", "geocode_confidence"],
            "paint": {"circle-color": "#e0b84d", "circle-radius": 3.2,
                      "circle-stroke-color": "#101318", "circle-stroke-width": 0.6,
                      "circle-opacity": 0.85}}


def compass_label(bearing: float) -> str:
    return _COMPASS[round(bearing / 45) % 8]


def confidence_note(hi: int, pins: int, approx: int) -> str:
    return (f"Coordinates: {hi} verified/rooftop ({pins} from DPL's own map links), "
            f"{approx} approximate. Mobile service points excluded.")


def assemble_stats(m: dict) -> dict:
    """Shape the final spatial-stats document from the computed scalar metrics."""
    return {
        "located_fixed_dpl": m["located"], "high_confidence": m["hi"], "approximate": m["approx"],
        "source_verified": m["source_verified"],
        "wards_total": m["n_wards"], "wards_within_1200m": m["within_1200"],
        "wards_within_1200m_pct": round(100 * m["within_1200"] / m["n_wards"], 1),
        "median_ward_km_to_dpl": m["median_ward_km"],
        "reach_by_radius": m["reach"], "city_area_pct_within_1200m": m["area_cov_1200"],
        "centroid_offset_from_city_km": m["centroid_offset_km"], "centroid_bearing_deg": m["bearing"],
        "network_std_distance_km": m["std_dist_km"],
        "dpl_within_800m_metro": m["within800"], "dpl_within_400m_metro": m["within400"],
        "dpl_within_400m_any_transit": m["any_transit_400"], **m["bus_stats"],
        "per_district": m["per_district"],
    }
