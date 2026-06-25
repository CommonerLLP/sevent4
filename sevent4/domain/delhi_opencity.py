"""Pure Delhi OpenCity layer logic: the atlas layer-manifest specs for the
villages / districts / water layers and the manifest merge (insert-or-replace a
layer entry by id, preserving order). No geospatial or filesystem IO.
"""
from __future__ import annotations


def layer_specs() -> list[dict]:
    """The three OpenCity layer entries, in console insertion order."""
    return [
        {"id": "districts", "label": "Districts (revenue)", "file": "districts.geojson",
         "kind": "line", "group": "Civic baseline", "default": True, "popup": ["district"],
         "paint": {"line-color": "#c9c2b3", "line-width": 1.4, "line-opacity": 0.6}},
        {"id": "villages", "label": "Revenue villages (2022)", "file": "villages.geojson",
         "kind": "fill", "group": "Civic baseline", "default": False, "outline": True,
         "popup": ["village_name", "tehsil", "district"],
         "paint": {"fill-color": "#8a6f4e", "fill-opacity": 0.12}},
        {"id": "water", "label": "Water bodies (2023 census)", "file": "water.geojson",
         "kind": "circle", "group": "Environment", "default": False, "popup": ["Name"],
         "paint": {"circle-color": "#3aa0d6", "circle-radius": 2.8,
                   "circle-stroke-color": "#0b3a52", "circle-stroke-width": 0.5,
                   "circle-opacity": 0.85}},
    ]


def merge_layers(manifest: dict, entries: list[dict]) -> dict:
    """Insert-or-replace each entry in manifest['layers'] by id, preserving order."""
    ids = {layer["id"] for layer in manifest["layers"]}
    for entry in entries:
        if entry["id"] in ids:
            manifest["layers"] = [entry if layer["id"] == entry["id"] else layer
                                  for layer in manifest["layers"]]
        else:
            manifest["layers"].append(entry)
    return manifest
