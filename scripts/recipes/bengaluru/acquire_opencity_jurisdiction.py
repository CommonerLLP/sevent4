#!/usr/bin/env python3
"""Acquire Bengaluru jurisdiction and utility geo resources from OpenCity.

Thin CLI wrapper: resource selection lives in
sevent4.domain.bengaluru_opencity, dispatch in
sevent4.application.bengaluru_opencity, and network/filesystem/hash IO in
sevent4.adapters.bengaluru_opencity_filesystem.
"""
from __future__ import annotations

import sevent4.adapters.bengaluru_opencity_filesystem as opencity_store
from sevent4.application.bengaluru_opencity import acquire_jurisdiction_resources
from sevent4.domain.bengaluru_opencity import JURISDICTION_KEEP, JURISDICTION_SLUGS  # noqa: F401


def main() -> None:
    result = acquire_jurisdiction_resources(opencity_store)
    print(
        f"Bengaluru OpenCity jurisdiction: {result['downloaded']}/{len(result['resources'])} resources "
        f"-> {opencity_store.OPENCITY_RAW}"
    )
    if result["skipped"]:
        print(f"skipped packages: {result['skipped']}")


if __name__ == "__main__":
    main()
