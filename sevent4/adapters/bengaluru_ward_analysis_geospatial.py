"""Geospatial/filesystem adapter for Bengaluru four-axis ward analysis."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd

from sevent4.domain.bengaluru_ward_analysis import nk

ROOT = Path(__file__).resolve().parents[2]
CITY = ROOT / "data" / "cities" / "bengaluru"
LAYERS = CITY / "layers"
METRIC = 32643


def ward_analysis_rows() -> list[dict]:
    canonical = gpd.read_file(CITY / "source" / "boundaries" / "wards_bbmp198.geojson").to_crs(METRIC)
    heat = gpd.read_file(LAYERS / "ward_heat.geojson").to_crs(METRIC)[["mean_lst_c", "max_lst_c", "geometry"]]

    canonical["_cid"] = range(len(canonical))
    intersections = gpd.overlay(canonical[["_cid", "geometry"]], heat, how="intersection")
    intersections["_a"] = intersections.geometry.area
    heat_by_canonical = {}
    for cid, group in intersections.groupby("_cid"):
        area = group["_a"].sum()
        if area > 0:
            heat_by_canonical[cid] = (
                float((group["mean_lst_c"] * group["_a"]).sum() / area),
                float(group["max_lst_c"].max()),
            )
    canonical["mean_lst_c"] = canonical["_cid"].map(
        lambda cid: round(heat_by_canonical.get(cid, (None, None))[0], 2) if heat_by_canonical.get(cid) else None
    )
    canonical["max_lst_c"] = canonical["_cid"].map(
        lambda cid: round(heat_by_canonical.get(cid, (None, None))[1], 2) if heat_by_canonical.get(cid) else None
    )

    ledger = {
        nk(row["ward_name"].split(" ", 1)[-1]): row
        for row in read_json(CITY / "source" / "finance" / "ward_workorders.json")
    }
    canonical_wgs84 = canonical.to_crs(4326)
    rows = []
    for index, (_, record) in enumerate(canonical.iterrows()):
        ward = record.get("name_en") or record.get("proposed_ward_name_en") or record.get("Name") or ""
        geometry = json.loads(gpd.GeoSeries([canonical_wgs84.iloc[index].geometry]).to_json())["features"][0]["geometry"]
        rows.append(
            {
                "ward": ward,
                "population": record.get("population") or 0,
                "sc_population": record.get("sc_population") or 0,
                "st_population": record.get("st_population") or 0,
                "assembly": record.get("assembly_constituency_name_en") or "",
                "parliament": record.get("parliamentary_constituency_name_en") or "",
                "ledger": ledger.get(nk(ward)),
                "mean_lst_c": canonical.iloc[index]["mean_lst_c"],
                "max_lst_c": canonical.iloc[index]["max_lst_c"],
                "geometry": geometry,
            }
        )
    return rows


def write_ward_analysis(feature_collection: dict) -> None:
    (LAYERS / "ward_analysis.geojson").write_text(json.dumps(feature_collection, ensure_ascii=False), encoding="utf-8")


def read_layer_manifest() -> dict:
    return read_json(LAYERS / "layer_manifest.json")


def write_layer_manifest(manifest: dict) -> None:
    (LAYERS / "layer_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
