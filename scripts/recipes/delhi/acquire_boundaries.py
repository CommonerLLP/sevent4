#!/usr/bin/env python3
"""Acquire Delhi's boundary spine into data/cities/delhi/source/boundaries/.

Delhi's geometry is NOT on OpenCity (which carries Delhi finance, elections,
births/deaths, vehicles, air quality, schools — but no admin boundaries). The
spine is sourced from DataMeet's open mirrors:

  - ACs (70)  : datameet/maps  India_AC.shp        (ECI delimitation, EPSG:4326)
  - PCs ( 7)  : datameet/maps  india_pc_2019        (ECI 2019, simplified GeoJSON)
  - wards     : datameet/Municipal_Spatial_Data/Delhi/Delhi_Wards.geojson

PROVENANCE CAVEAT — wards: the only openly-available Delhi ward geometry is the
PRE-2022 set (~290 features incl. NDMC + Delhi Cantonment "charges"), scraped
from an ArcGIS Online map. The 2022 *unified MCD 250-ward delimitation* was
published by the State Election Commission as PDFs only; its geometry is not
openly available. This layer is therefore shipped as an honestly-labelled
INTERIM ward layer. ACs/PCs are current.

    python3 scripts/recipes/delhi/acquire_boundaries.py
"""
from __future__ import annotations
import json
from pathlib import Path

import geopandas as gpd
import requests

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "cities" / "delhi" / "source" / "boundaries"
UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas)"}

DM = "https://raw.githubusercontent.com/datameet"
AC_BASE = f"{DM}/maps/master/assembly-constituencies/India_AC"
PC_URL = f"{DM}/maps/master/parliamentary-constituencies/india_pc_2019_simplified.geojson"
WARDS_URL = f"{DM}/Municipal_Spatial_Data/master/Delhi/Delhi_Wards.geojson"

SOURCES = {
    "acs": {
        "url": f"{AC_BASE}.shp",
        "label": "Delhi Assembly Constituencies (70)",
        "publisher": "Election Commission of India delimitation, via DataMeet datameet/maps",
        "vintage": "current (2008 delimitation order, in force)",
        "license": "DataMeet community data",
    },
    "pcs": {
        "url": PC_URL,
        "label": "Delhi Parliamentary Constituencies (7)",
        "publisher": "Election Commission of India 2019, via DataMeet datameet/maps",
        "vintage": "current",
        "license": "DataMeet community data",
    },
    "wards": {
        "url": WARDS_URL,
        "label": "Delhi municipal wards (INTERIM, pre-2022)",
        "publisher": "DataMeet datameet/Municipal_Spatial_Data (scraped from ArcGIS Online)",
        "vintage": "PRE-2022 (~290 features incl. NDMC + Cantonment charges); "
                   "predates the 2022 unified-MCD 250-ward delimitation",
        "license": "CC BY-SA 2.5 IN",
    },
}


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, headers=UA, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def acquire_acs(tmp: Path) -> gpd.GeoDataFrame:
    for ext in ("shp", "dbf", "shx", "prj"):
        _download(f"{AC_BASE}.{ext}", tmp / f"India_AC.{ext}")
    g = gpd.read_file(tmp / "India_AC.shp")
    g = g[g["ST_NAME"].astype(str).str.strip().str.upper().eq("DELHI")].copy()
    g = g.to_crs(4326)
    g["ac_name"] = g["AC_NAME"].astype(str).str.strip()
    g["ac_no"] = g["AC_NO"]
    g["dist_name"] = g["DIST_NAME"].astype(str).str.strip()
    g["pc_name"] = g["PC_NAME"].astype(str).str.strip()
    g["office"] = "MLA"
    return g[["ac_name", "ac_no", "dist_name", "pc_name", "office", "geometry"]]


def acquire_pcs(tmp: Path) -> gpd.GeoDataFrame:
    _download(PC_URL, tmp / "india_pc.geojson")
    g = gpd.read_file(tmp / "india_pc.geojson")
    g = g[g["st_name"].astype(str).str.strip().str.upper().eq("DELHI")].copy()
    g = g.to_crs(4326)
    g["pc_name"] = g["pc_name"].astype(str).str.strip()
    g["office"] = "MP"
    return g[["pc_name", "pc_no", "office", "geometry"]]


def acquire_wards(tmp: Path) -> gpd.GeoDataFrame:
    _download(WARDS_URL, tmp / "Delhi_Wards.geojson")
    g = gpd.read_file(tmp / "Delhi_Wards.geojson").to_crs(4326)
    g["ward_name"] = g["Ward_Name"].astype(str).str.title().str.strip()
    g["ward_no"] = g["Ward_No"].astype(str).str.strip()
    g["Name"] = g["ward_name"]
    g["ward_vintage"] = "pre-2022 (interim; not the 2022 unified-MCD 250-ward set)"
    return g[["Name", "ward_name", "ward_no", "ward_vintage", "geometry"]]


def acquire_districts(acs: gpd.GeoDataFrame) -> gpd.GeoDataFrame | None:
    # The DataMeet AC shapefile carries no DIST_NAME for Delhi, so districts
    # can't be dissolved from it. Skip rather than ship an empty layer.
    valid = acs["dist_name"].notna() & acs["dist_name"].astype(str).str.strip().ne("")
    if not valid.any():
        return None
    d = acs[valid].dissolve(by="dist_name", as_index=False)[["dist_name", "geometry"]]
    d["district"] = d["dist_name"]
    return d[["district", "geometry"]]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_raw"
    tmp.mkdir(exist_ok=True)

    acs = acquire_acs(tmp)
    pcs = acquire_pcs(tmp)
    wards = acquire_wards(tmp)
    districts = acquire_districts(acs)

    acs.to_file(OUT / "acs.geojson", driver="GeoJSON")
    pcs.to_file(OUT / "pcs.geojson", driver="GeoJSON")
    wards.to_file(OUT / "wards.geojson", driver="GeoJSON")
    if districts is not None:
        districts.to_file(OUT / "districts.geojson", driver="GeoJSON")
    else:
        (OUT / "districts.geojson").unlink(missing_ok=True)
    n_districts = 0 if districts is None else len(districts)

    (OUT / "sources.json").write_text(json.dumps(SOURCES, indent=2), encoding="utf-8")
    (OUT / "CREDITS.md").write_text(
        "# Delhi boundary spine — provenance\n\n"
        "| Layer | Features | Source | Vintage |\n|---|---|---|---|\n"
        f"| ACs | {len(acs)} | {SOURCES['acs']['publisher']} | {SOURCES['acs']['vintage']} |\n"
        f"| PCs | {len(pcs)} | {SOURCES['pcs']['publisher']} | {SOURCES['pcs']['vintage']} |\n"
        f"| Districts | {n_districts} | dissolved from ACs (DIST_NAME) | derived (none: DIST_NAME blank) |\n"
        f"| Wards | {len(wards)} | {SOURCES['wards']['publisher']} | {SOURCES['wards']['vintage']} |\n\n"
        "**Ward caveat:** the 2022 unified-MCD 250-ward delimitation geometry is not "
        "openly available (SEC-Delhi published PDFs only). The ward layer here is the "
        "pre-2022 set, shipped as labelled interim. ACs and PCs are current.\n",
        encoding="utf-8",
    )
    print(f"delhi boundaries: {len(wards)} wards (INTERIM pre-2022), "
          f"{len(acs)} ACs, {len(pcs)} PCs, {n_districts} districts -> {OUT}")


if __name__ == "__main__":
    main()
