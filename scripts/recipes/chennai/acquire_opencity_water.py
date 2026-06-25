#!/usr/bin/env python3
"""Acquire Chennai water/flood geo resources from OpenCity."""
from __future__ import annotations

import sevent4.adapters.chennai_opencity_water_filesystem as water_store
from sevent4.application.chennai_opencity_water import acquire_water_resources
from sevent4.domain.chennai_opencity_water import KEEP, SLUGS, safe_filename as slugify


def fetch(url: str) -> bytes:
    return water_store.request_bytes(url)


def main() -> None:
    result = acquire_water_resources(water_store)
    total_bytes = sum(int(row["bytes"]) for row in result["resources"] if row["status"] == "ok")
    print(
        f"Chennai OpenCity water/flood: {result['downloaded']}/"
        f"{len(result['resources'])} resources, {total_bytes / 1e6:.1f} MB -> {water_store.RAW}"
    )


if __name__ == "__main__":
    main()
