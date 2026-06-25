#!/usr/bin/env python3
"""Acquire Delhi's boundary spine into data/cities/delhi/source/boundaries/.

Delhi's geometry is NOT on OpenCity; the spine is sourced from DataMeet's open
mirrors (ACs 70 / PCs 7 / pre-2022 interim wards). The 2022 unified-MCD 250-ward
delimitation geometry is not openly available, so the ward layer is shipped as an
honestly-labelled INTERIM layer; ACs/PCs are current.

Thin CLI wrapper: provenance/credits shaping lives in sevent4.domain.delhi_acquire /
sevent4.application.delhi_acquire; HTTP + geopandas IO in the delhi-acquire adapter.

    .venv/bin/python scripts/recipes/delhi/acquire_boundaries.py
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.delhi_acquire_filesystem import (
    DelhiBoundarySource,
    write_geodataframe,
    write_json,
    write_text,
)
from sevent4.application.delhi_acquire import acquire_boundaries, boundary_sources
from sevent4.domain.delhi_acquire import boundary_credits_md

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "cities" / "delhi" / "source" / "boundaries"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_raw"
    tmp.mkdir(exist_ok=True)

    counts, districts = acquire_boundaries(
        DelhiBoundarySource(tmp),
        lambda gdf, name: write_geodataframe(gdf, OUT / f"{name}.geojson"),
    )
    if districts is None:
        (OUT / "districts.geojson").unlink(missing_ok=True)

    sources = boundary_sources()
    write_json(sources, OUT / "sources.json", indent=2)
    write_text(boundary_credits_md(sources, counts), OUT / "CREDITS.md")
    print(f"delhi boundaries: {counts['wards']} wards (INTERIM pre-2022), "
          f"{counts['acs']} ACs, {counts['pcs']} PCs, {counts['districts']} districts -> {OUT}")


if __name__ == "__main__":
    main()
