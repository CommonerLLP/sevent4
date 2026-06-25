#!/usr/bin/env python3
"""Acquire and convert the Bengaluru representative boundary spine.

Thin CLI wrapper: source definitions live in sevent4.domain.bengaluru_opencity,
dispatch in sevent4.application.bengaluru_opencity, and network/geospatial/
filesystem IO in sevent4.adapters.bengaluru_opencity_filesystem.
"""
from __future__ import annotations

import sevent4.adapters.bengaluru_opencity_filesystem as opencity_store
from sevent4.application.bengaluru_opencity import acquire_boundary_spine
from sevent4.domain.bengaluru_opencity import BOUNDARY_SPINE  # noqa: F401


def main() -> None:
    result = acquire_boundary_spine(opencity_store)
    for row in result["provenance"]:
        print(
            f"[{row['layer']}] {row['features']} features -> {row['file']} "
            f"({int(row['bytes']) / 1024:.0f} KB KML) cols={row['columns']}"
        )
    print(f"\nwrote sources.json + CREDITS.md to {opencity_store.BOUNDARY_OUT}")


if __name__ == "__main__":
    main()
