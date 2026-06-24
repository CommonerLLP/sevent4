#!/usr/bin/env python3
"""Add the ward_heat + heat30m Climate layers to a city's layer_manifest.json.

Idempotent: an existing layer id is replaced in place rather than duplicated.
Only runs when the city actually has the heat outputs on disk. Thin CLI wrapper:
the patch logic lives in the heat application/domain layers, JSON IO in the
manifest store adapter.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.heat_filesystem import FileHeatManifestStore
from sevent4.application.heat import patch_heat_manifest

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True)
    args = parser.parse_args()
    city = args.city.lower()

    store = FileHeatManifestStore(REPO, city)
    if not store.manifest_exists():
        sys.exit(f"No manifest at {store.manifest_path}")
    if not store.has_heat_outputs():
        sys.exit(f"{city}: heat outputs missing, not patching manifest")

    store.write_manifest(patch_heat_manifest(store.load_manifest()))
    print(f"{city}: manifest patched with ward_heat + heat30m")


if __name__ == "__main__":
    main()
