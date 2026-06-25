#!/usr/bin/env python3
"""Build curated Chennai water/flood GeoJSON layers from the OpenCity archive."""
from __future__ import annotations

import sevent4.adapters.chennai_opencity_water_filesystem as water_store
from sevent4.application.chennai_opencity_water import build_water_layers
from sevent4.domain.chennai_opencity_water import CURATED_WATER_LAYERS as CURATED, DRAIN_KEEP, KML_CRUFT

read_kml = water_store.read_any
clean = water_store.clean_geodataframe


def main() -> None:
    result = build_water_layers(water_store)
    print(f"built {result['ok']}/{result['total']} Chennai water/flood layers -> {water_store.LAYERS}")


if __name__ == "__main__":
    main()
