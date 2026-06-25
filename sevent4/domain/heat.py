"""Pure surface-heat domain logic: Landsat QA masking, brightness-to-Celsius
conversion, the heat colour ramp, per-ward LST statistics, and the Climate
layer-manifest entries. No filesystem, network, or raster-library IO lives here;
callers pass plain numpy arrays and GeoJSON-shaped dicts in and out.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

import numpy as np

# Landsat Collection-2 Level-2 surface-temperature scaling (ST_B10 / lwir11).
ST_SCALE = 0.00341802
ST_OFFSET = 149.0
KELVIN = 273.15
VALID_C_MIN = -10.0
VALID_C_MAX = 70.0

HEAT_RAMP = (
    (30, (0, 80, 30)),
    (33, (120, 180, 40)),
    (36, (240, 230, 40)),
    (39, (245, 150, 30)),
    (42, (225, 50, 30)),
    (45, (150, 15, 20)),
    (48, (90, 0, 25)),
)

WARD_HEAT_LAYER: Mapping[str, Any] = {
    "id": "ward_heat",
    "label": "Ward heat",
    "file": "ward_heat.geojson",
    "kind": "fill",
    "group": "Climate",
    "default": False,
    "outline": True,
    "popup": ["Name", "mean_lst_c", "max_lst_c"],
    "paint": {
        "fill-color": [
            "interpolate", ["linear"], ["to-number", ["get", "mean_lst_c"], 35],
            32, "#2c7a55", 36, "#d7b33f", 39, "#d36b32", 42, "#9f2d2d",
        ],
        "fill-opacity": 0.58,
    },
}

HEAT30M_LAYER: Mapping[str, Any] = {
    "id": "heat30m",
    "label": "Surface heat - 30m",
    "file": "heat30m.png",
    "bounds_file": "heat30m_bounds.json",
    "kind": "image",
    "group": "Climate",
    "default": False,
    "popup": [],
    "paint": {"raster-opacity": 0.78, "raster-resampling": "nearest"},
}


def qa_mask(qa: np.ndarray) -> np.ndarray:
    """Return a boolean array that is True for usable pixels.

    Bits 1-4 of the Landsat QA_PIXEL band flag dilated-cloud/cirrus/cloud/shadow;
    a fill value of 0 is also rejected.
    """
    bad = np.zeros(qa.shape, dtype=bool)
    for bit in (1, 2, 3, 4):
        bad |= ((qa.astype(np.uint16) >> bit) & 1).astype(bool)
    return ~(bad | (qa == 0))


def celsius_from_landsat_st(st: np.ndarray, good: np.ndarray) -> np.ndarray:
    """Convert raw ST brightness values to Celsius, masking fill/bad/out-of-range
    pixels to NaN."""
    celsius = st.astype("float32")
    celsius[celsius == 0] = np.nan
    celsius = celsius * ST_SCALE + ST_OFFSET - KELVIN
    celsius[~good] = np.nan
    celsius[(celsius < VALID_C_MIN) | (celsius > VALID_C_MAX)] = np.nan
    return celsius


def heat_rgba(data: np.ndarray) -> np.ndarray:
    """Map a 2D Celsius grid to an RGBA uint8 array using the heat colour ramp.
    NaN pixels become fully transparent."""
    xs = np.array([stop[0] for stop in HEAT_RAMP], dtype="float32")
    rs = np.array([stop[1][0] for stop in HEAT_RAMP], dtype="float32")
    gs = np.array([stop[1][1] for stop in HEAT_RAMP], dtype="float32")
    bs = np.array([stop[1][2] for stop in HEAT_RAMP], dtype="float32")
    valid = np.isfinite(data)
    values = np.where(valid, data, 30.0)
    rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
    rgba[..., 0] = np.interp(values, xs, rs).astype(np.uint8)
    rgba[..., 1] = np.interp(values, xs, gs).astype(np.uint8)
    rgba[..., 2] = np.interp(values, xs, bs).astype(np.uint8)
    rgba[..., 3] = np.where(valid, 220, 0).astype(np.uint8)
    return rgba


def ward_lst_stats(values: np.ndarray | None, nodata: float | None) -> tuple[float | None, float | None, int]:
    """Mean/max/count of valid land-surface-temperature pixels under one ward.

    Returns (mean_c, max_c, count) with mean/max rounded to 2 dp, or
    (None, None, 0) when no usable pixel falls inside the ward.
    """
    if values is None:
        return None, None, 0
    finite = values[np.isfinite(values)]
    if nodata is not None and not np.isnan(nodata):
        finite = finite[finite != nodata]
    finite = finite[(finite > VALID_C_MIN) & (finite < VALID_C_MAX)]
    if not finite.size:
        return None, None, 0
    return round(float(finite.mean()), 2), round(float(finite.max()), 2), int(finite.size)


def patched_manifest_layers(
    existing: Sequence[Mapping[str, Any]],
    entries: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Idempotently add the Climate layer entries: replace any layer with the
    same id in place, otherwise append. Returns a new list."""
    layers = [deepcopy(layer) for layer in existing]
    by_id = {layer.get("id"): index for index, layer in enumerate(layers)}
    for entry in entries:
        if entry["id"] in by_id:
            layers[by_id[entry["id"]]] = deepcopy(entry)
        else:
            layers.append(deepcopy(entry))
    return layers
