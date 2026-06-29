#!/usr/bin/env python3
"""Driver: build the Landsat heat layer for all atlas cities, in-process.

Runs the source -> build -> aggregate -> manifest-patch pipeline per city using
the heat ports; per-city config and the run summary are read/written through the
heat adapters.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from sevent4.adapters.heat_filesystem import (
    FileHeatArtifactWriter,
    FileHeatManifestStore,
    FileWardHeatRepository,
    load_city_bbox,
    summary_json,
    write_heat_run_summary,
)
from sevent4.adapters.heat_planetary import PlanetaryComputerHeatSource
from sevent4.application.heat import aggregate_ward_heat, build_city_heat, patch_heat_manifest

REPO = Path(__file__).resolve().parents[3]

# Rolling refresh knobs (env-driven so a scheduled job can advance the window):
#   HEAT_WINDOW       STAC date window for the Landsat median (default below)
#   HEAT_LAYERS_ROOT  source/output tree — "data" (local, gitignored) or "public"
#                     (committed wards, so the layer refresh runs on a CI checkout)
HEAT_WINDOW = os.environ.get("HEAT_WINDOW", "2023-04-01/2025-06-30")
HEAT_LAYERS_ROOT = os.environ.get("HEAT_LAYERS_ROOT", "data")

DEFAULT_CITIES = [
    "chennai", "mumbai", "bengaluru", "hyderabad", "kolkata",
    "visakhapatnam", "bhubaneswar", "kochi", "pune", "kanpur", "jaipur",
]


def _layers_dir(city: str) -> Path:
    return REPO / HEAT_LAYERS_ROOT / "cities" / city / "layers"


def run_city(city: str) -> dict:
    layers_dir = _layers_dir(city)
    bbox = load_city_bbox(REPO, city, layers_dir=layers_dir)
    print(f"\n===== {city}  bbox={bbox}  window={HEAT_WINDOW}  tree={HEAT_LAYERS_ROOT} =====", flush=True)

    try:
        grid = PlanetaryComputerHeatSource().median_grid(bbox, HEAT_WINDOW, 30.0)
        raster = build_city_heat(city, grid)
        FileHeatArtifactWriter(REPO, city, layers_dir=layers_dir).write_raster_artifacts(raster)
    except (SystemExit, Exception) as exc:  # noqa: B014 - isolate any per-city build failure
        # The previous subprocess driver turned any non-zero build into this
        # city's MISSING result and carried on; keep that per-city isolation.
        print(f"{city}: HEAT MISSING -> {exc}", flush=True)
        return {"status": "MISSING", "reason": str(exc)}

    repository = FileWardHeatRepository(REPO, city, layers_dir=layers_dir)
    try:
        wards = repository.load_wards()
        with repository.open_sampler() as (sample, nodata):
            document, agg = aggregate_ward_heat(wards, sample, nodata)
        FileHeatArtifactWriter(REPO, city, layers_dir=layers_dir).write_ward_heat(document)
    except Exception as exc:  # noqa: BLE001
        print(f"{city}: ward agg failed -> {exc}", flush=True)
        return {"status": "RASTER_ONLY", "reason": str(exc)[-200:], "scene_stats": raster.summary}

    store = FileHeatManifestStore(REPO, city)
    manifest_note = ""
    if store.manifest_exists() and store.has_heat_outputs():
        store.write_manifest(patch_heat_manifest(store.load_manifest()))
        manifest_note = f"{city}: manifest patched with ward_heat + heat30m"

    print(
        f"{city}: OK  {agg.get('mean_lst_min')}-{agg.get('mean_lst_max')}C  "
        f"{agg.get('wards_with_lst')}/{agg.get('wards')} wards",
        flush=True,
    )
    return {
        "status": "OK",
        "scenes": raster.summary.get("scenes"),
        "scene_min_c": raster.summary.get("min_c"),
        "scene_max_c": raster.summary.get("max_c"),
        "ward_mean_lst_min": agg.get("mean_lst_min"),
        "ward_mean_lst_max": agg.get("mean_lst_max"),
        "wards_with_lst": agg.get("wards_with_lst"),
        "wards": agg.get("wards"),
        "manifest": manifest_note,
    }


def main() -> None:
    cities = sys.argv[1:] or DEFAULT_CITIES
    results = {city: run_city(city) for city in cities}
    write_heat_run_summary(REPO, results)
    print("\n===== SUMMARY =====")
    print(summary_json(results))


if __name__ == "__main__":
    main()
