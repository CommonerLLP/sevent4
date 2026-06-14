#!/usr/bin/env python3
"""Turn Delhi's mappable OpenCity downloads into committed atlas layers.

From data/cities/delhi/source/opencity/_raw/ (pulled by acquire_opencity.py):
  - villages-maps-of-delhi/*.kml  -> layers/villages.geojson (2022, district-tagged)
  - dissolve villages by district -> layers/districts.geojson (11 districts)
  - delhi-water-bodies-census-data/*.kml -> layers/water.geojson (893 points, 2023)

Microwatersheds (2,324 polys / 7 MB) is left in _raw — too heavy/niche for the
default console. Then registers the three layers in layer_manifest.json.

    python3 scripts/recipes/delhi/build_opencity_layers.py
"""
from __future__ import annotations
import json, re
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/cities/delhi/source/opencity/_raw"
LAYERS = ROOT / "data/cities/delhi/layers"


def _simplify(g: gpd.GeoDataFrame, tol_m: float = 25.0) -> gpd.GeoDataFrame:
    # simplify in metric CRS to shrink GeoJSON for a Pages-committed layer
    g = g.copy()
    g["geometry"] = g.to_crs(32643).geometry.simplify(tol_m, preserve_topology=True)
    return g.set_geometry(g["geometry"]).set_crs(32643, allow_override=True).to_crs(4326)


def build_villages() -> gpd.GeoDataFrame:
    parts = []
    for kml in sorted((RAW / "villages-maps-of-delhi").glob("*.kml")):
        g = gpd.read_file(kml).to_crs(4326)
        g["village_name"] = g["VILLAGE"].astype(str).str.title().str.strip()
        g["tehsil"] = g["TEHSIL"].astype(str).str.title().str.strip()
        g["district"] = g["DISTRICT"].astype(str).str.title().str.strip()
        parts.append(g[["village_name", "tehsil", "district", "geometry"]])
    villages = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs="EPSG:4326")
    villages = _simplify(villages, 25.0)
    villages["Name"] = villages["village_name"]
    return villages


def build_water() -> gpd.GeoDataFrame:
    kml = next((RAW / "delhi-water-bodies-census-data").glob("*.kml"))
    g = gpd.read_file(kml).to_crs(4326)
    g["Name"] = g["Name"].astype(str).str.strip()
    return g[["Name", "geometry"]]


def register(manifest_path: Path, entries: list[dict]) -> None:
    m = json.loads(manifest_path.read_text())
    ids = {l["id"] for l in m["layers"]}
    # insert districts right after wards; append villages + water
    for e in entries:
        if e["id"] in ids:
            m["layers"] = [e if l["id"] == e["id"] else l for l in m["layers"]]
        else:
            m["layers"].append(e)
    manifest_path.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    villages = build_villages()
    districts = villages.dissolve(by="district", as_index=False)[["district", "geometry"]]
    districts["geometry"] = districts.to_crs(32643).geometry.simplify(40.0, preserve_topology=True).to_crs(4326)
    water = build_water()

    villages.to_file(LAYERS / "villages.geojson", driver="GeoJSON")
    districts.to_file(LAYERS / "districts.geojson", driver="GeoJSON")
    water.to_file(LAYERS / "water.geojson", driver="GeoJSON")

    register(LAYERS / "layer_manifest.json", [
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
    ])
    print(f"delhi OpenCity layers: villages {len(villages)}, districts {len(districts)}, "
          f"water {len(water)} -> {LAYERS}")


if __name__ == "__main__":
    main()
