#!/usr/bin/env python3
"""Build curated Bengaluru jurisdiction and waste GeoJSON layers.

Thin CLI wrapper: curated specs live in sevent4.domain.bengaluru_opencity,
dispatch in sevent4.application.bengaluru_opencity, and geospatial filesystem
IO in sevent4.adapters.bengaluru_opencity_filesystem.
"""
from __future__ import annotations

import sevent4.adapters.bengaluru_opencity_filesystem as opencity_store
from sevent4.application.bengaluru_opencity import build_jurisdiction_layers
from sevent4.domain.bengaluru_opencity import CURATED_JURISDICTION_LAYERS  # noqa: F401


def main() -> None:
    result = build_jurisdiction_layers(opencity_store)
    for row in result["layers"]:
        if row.get("status") == "ok":
            print(f"  [ok] {row['id']:<28} {row['features']:>5} feats {row['bytes'] / 1e6:5.1f}MB")
        else:
            print(f"  [{row['status']}] {row['id']:<28}")
    print(f"\nbuilt {result['ok']}/{result['total']} Bengaluru jurisdiction layers -> {opencity_store.LAYERS}")


if __name__ == "__main__":
    main()
