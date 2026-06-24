from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from sevent4.domain.heat import (
    HEAT30M_LAYER,
    WARD_HEAT_LAYER,
    heat_rgba,
    patched_manifest_layers,
    ward_lst_stats,
)


@dataclass(frozen=True)
class HeatGrid:
    """A reprojected (EPSG:4326) median Celsius grid plus the coordinate vectors,
    geographic bounds, and the scene log that produced it."""

    data: np.ndarray
    lon: np.ndarray
    lat: np.ndarray
    bounds: Sequence[float]
    scene_log: Sequence[Mapping[str, Any]]


@dataclass(frozen=True)
class HeatArtifacts:
    grid: HeatGrid
    rgba: np.ndarray
    bounds_doc: Mapping[str, Any]
    scene_log: Sequence[Mapping[str, Any]]
    summary: Mapping[str, Any]


def build_city_heat(city: str, grid: HeatGrid) -> HeatArtifacts:
    """Turn a median heat grid into the raster artifacts (RGBA + bounds + summary)
    the writer persists. Pure: no IO."""
    data = grid.data
    if data.ndim == 3:
        data = data[0]
    west, south, east, north = grid.bounds
    bounds_doc = {
        "bbox": [west, south, east, north],
        "corners": [[west, north], [east, north], [east, south], [west, south]],
        "crs": "EPSG:4326",
    }
    finite = data[np.isfinite(data)]
    summary = {
        "city": city,
        "scenes": len(grid.scene_log),
        "min_c": round(float(finite.min()), 2),
        "max_c": round(float(finite.max()), 2),
        "mean_c": round(float(finite.mean()), 2),
        "bbox": bounds_doc["bbox"],
    }
    return HeatArtifacts(
        grid=grid,
        rgba=heat_rgba(data),
        bounds_doc=bounds_doc,
        scene_log=list(grid.scene_log),
        summary=summary,
    )


def aggregate_ward_heat(
    wards: Mapping[str, Any],
    sample: Callable[[Any], "np.ndarray | None"],
    nodata: float | None,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Join the heat raster onto ward polygons via the supplied sampler callable.

    `sample(geometry)` returns the raster values under a ward (or None). Stats are
    computed in the domain layer. Returns (ward_heat GeoJSON, summary)."""
    out_features = []
    means: list[float] = []
    for feature in wards["features"]:
        geometry = feature.get("geometry")
        values = sample(geometry) if geometry is not None else None
        mean_c, max_c, count = ward_lst_stats(values, nodata)
        properties = dict(feature.get("properties", {}))
        properties["mean_lst_c"] = mean_c
        properties["max_lst_c"] = max_c
        properties["lst_px_count"] = count
        if mean_c is not None:
            means.append(mean_c)
        out_features.append({"type": "Feature", "properties": properties, "geometry": geometry})

    document = {
        "type": "FeatureCollection",
        "name": "ward_heat",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": out_features,
    }
    summary = {
        "wards": len(out_features),
        "wards_with_lst": len(means),
        "mean_lst_min": round(min(means), 1) if means else None,
        "mean_lst_max": round(max(means), 1) if means else None,
    }
    return document, summary


def patch_heat_manifest(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    """Idempotently add the ward_heat + heat30m Climate layers to a manifest."""
    patched = dict(manifest)
    patched["layers"] = patched_manifest_layers(
        manifest.get("layers", []), (WARD_HEAT_LAYER, HEAT30M_LAYER)
    )
    return patched
