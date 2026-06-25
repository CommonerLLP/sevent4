"""Filesystem, network, CSV, and geospatial adapter for Chennai GCC finance."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import geopandas as gpd


ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / "data" / "sources" / "opencity" / "_catalogue" / "opencity_catalogue.json"
ARCHIVE = Path(os.environ.get("OPENCITY_ARCHIVE", str(ROOT / "data" / "sources" / "opencity")))
RAW = ARCHIVE / "chennai" / "raw" / "gcc-finances"
CITY = ROOT / "data" / "cities" / "chennai"
WARDS = CITY / "layers" / "wards.geojson"
OUT_LAYER = CITY / "layers" / "zone_finance.geojson"
OUT_FIN = CITY / "source" / "finance"
UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas)"}


def read_catalogue() -> dict:
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


def fetch_finance_resource(filename: str, url: str) -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    target = RAW / filename
    if not target.exists():
        with urlopen(Request(url, headers=UA), timeout=60) as response:
            target.write_bytes(response.read())
    return target.stat().st_size


def read_finance_tables(resources: list[dict]) -> list[tuple[str, object]]:
    tables = []
    for resource in resources:
        name = resource["resource_name"]
        path = RAW / resource["filename"]
        if "summary" in name.lower():
            tables.append((name, read_csv_rows(path)))
        else:
            tables.append((name, read_csv_dict_rows(path)))
    return tables


def read_csv_rows(path: Path) -> list[list[str]]:
    with Path(path).open(encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.reader(handle))


def read_csv_dict_rows(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def read_zone_features() -> list[dict]:
    wards = gpd.read_file(WARDS)
    zone_column = "zone_no" if "zone_no" in wards.columns else None
    if not zone_column:
        raise ValueError("wards.geojson lacks zone_no")
    if wards.crs is not None:
        wards = wards.to_crs(4326)
    dissolved = wards.dissolve(by=zone_column).reset_index()
    features = []
    for _, row in dissolved.iterrows():
        zone_no = str(row[zone_column]).strip()
        zone_rows = wards[wards[zone_column] == row[zone_column]]
        zone_name = zone_no
        if "zone_name" in wards.columns and not zone_rows.empty:
            zone_name = str(zone_rows["zone_name"].iloc[0])
        geometry = json.loads(gpd.GeoSeries([row.geometry], crs=wards.crs).to_json())["features"][0]["geometry"]
        features.append({"zone_no": zone_no, "zone_name": zone_name, "geometry": geometry})
    return features


def write_zone_finance_layer(feature_collection: dict) -> None:
    OUT_LAYER.parent.mkdir(parents=True, exist_ok=True)
    OUT_LAYER.write_text(json.dumps(feature_collection, ensure_ascii=False), encoding="utf-8")


def write_budget_summary(budget: dict) -> None:
    OUT_FIN.mkdir(parents=True, exist_ok=True)
    (OUT_FIN / "chennai_budget.json").write_text(json.dumps(budget, indent=1, ensure_ascii=False), encoding="utf-8")


def write_finance_sources(sources: dict) -> None:
    OUT_FIN.mkdir(parents=True, exist_ok=True)
    (OUT_FIN / "sources.json").write_text(json.dumps(sources, indent=1, ensure_ascii=False), encoding="utf-8")
