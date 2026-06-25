"""Geospatial + filesystem adapter for Delhi OpenCity layers: read source KML,
simplify/repair geometry, dissolve districts, write GeoJSON, and read/write the
layer-manifest JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import make_valid
from shapely.geometry import MultiPolygon, Polygon


def _polygonal(geom):
    """make_valid + keep only polygonal parts (drop stray lines from repair)."""
    v = make_valid(geom)
    if v.geom_type == "GeometryCollection":
        parts = [g for g in v.geoms if isinstance(g, (Polygon, MultiPolygon))]
        polys = [q for p in parts for q in (p.geoms if p.geom_type == "MultiPolygon" else [p])]
        v = MultiPolygon(polys) if polys else v
    return v


def _simplify(g: gpd.GeoDataFrame, tol_m: float = 25.0) -> gpd.GeoDataFrame:
    # simplify in metric CRS to shrink GeoJSON, then buffer(0) to repair any
    # self-intersections the simplifier introduces (they render as spikes in MapLibre)
    g = g.copy()
    geom = g.to_crs(32643).geometry.simplify(tol_m, preserve_topology=True).buffer(0)
    g = g.set_geometry(geom).set_crs(32643, allow_override=True).to_crs(4326)
    return g


class DelhiOpenCityLayers:
    def __init__(self, raw_dir: Path, layers_dir: Path) -> None:
        self.raw = Path(raw_dir)
        self.layers = Path(layers_dir)

    def build_villages(self) -> gpd.GeoDataFrame:
        parts = []
        for kml in sorted((self.raw / "villages-maps-of-delhi").glob("*.kml")):
            g = gpd.read_file(kml).to_crs(4326)
            g["village_name"] = g["VILLAGE"].astype(str).str.title().str.strip()
            g["tehsil"] = g["TEHSIL"].astype(str).str.title().str.strip()
            g["district"] = g["DISTRICT"].astype(str).str.title().str.strip()
            parts.append(g[["village_name", "tehsil", "district", "geometry"]])
        villages = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs="EPSG:4326")
        villages = _simplify(villages, 25.0)
        villages["Name"] = villages["village_name"]
        return villages

    def build_districts(self, villages: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        districts = villages.dissolve(by="district", as_index=False)[["district", "geometry"]]
        dgeom = districts.to_crs(32643).geometry.simplify(40.0, preserve_topology=True).buffer(0)
        districts = districts.set_geometry(dgeom).set_crs(32643, allow_override=True).to_crs(4326)
        districts["geometry"] = districts.geometry.apply(_polygonal)  # repair self-intersections
        return districts

    def build_water(self) -> gpd.GeoDataFrame:
        kml = next((self.raw / "delhi-water-bodies-census-data").glob("*.kml"))
        g = gpd.read_file(kml).to_crs(4326)
        g["Name"] = g["Name"].astype(str).str.strip()
        return g[["Name", "geometry"]]

    def write_layer(self, gdf: gpd.GeoDataFrame, filename: str) -> None:
        gdf.to_file(self.layers / filename, driver="GeoJSON")

    def read_manifest(self, filename: str = "layer_manifest.json") -> dict:
        return json.loads((self.layers / filename).read_text())

    def write_manifest(self, manifest: dict, filename: str = "layer_manifest.json") -> None:
        (self.layers / filename).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
