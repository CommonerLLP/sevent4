"""Filesystem, network, and geospatial adapter for Chennai OpenCity water layers."""
from __future__ import annotations

import hashlib
import json
import warnings
from datetime import date
from pathlib import Path

import geopandas as gpd
import requests
import shapely
from pyogrio.raw import read as pyogrio_read


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "cities" / "chennai" / "source" / "opencity" / "_raw"
LAYERS = ROOT / "data" / "cities" / "chennai" / "layers"
SRCDIR = ROOT / "data" / "cities" / "chennai" / "source" / "opencity"
API = "https://data.opencity.in/api/3/action/package_show?id="
UA = {"User-Agent": "sevent4-atlas-catalogue/1.0 (open-data harvest)"}


def package_show(slug: str) -> dict | None:
    try:
        return requests.get(API + slug, headers=UA, timeout=60).json()
    except Exception:
        return None


def request_bytes(url: str) -> bytes:
    for attempt in range(3):
        try:
            response = requests.get(url, headers=UA, timeout=180)
            response.raise_for_status()
            return response.content
        except Exception:
            if attempt == 2:
                raise
    return b""


def fetch_water_resource(slug: str, filename: str, url: str) -> dict:
    target = RAW / slug / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        blob = request_bytes(url)
        target.write_bytes(blob)
        return {"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(), "status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"bytes": 0, "sha256": "", "status": f"error: {type(exc).__name__}"}


def write_water_manifest(summary: dict) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    payload = {"retrieved": date.today().isoformat(), **summary}
    (RAW / "_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def source_exists(spec: dict) -> bool:
    return (RAW / spec["slug"] / spec["file"]).exists()


def build_curated_layer(spec: dict) -> dict:
    warnings.filterwarnings("ignore")
    LAYERS.mkdir(parents=True, exist_ok=True)
    source = RAW / spec["slug"] / spec["file"]
    geodata = clean_geodataframe(read_any(source), spec)
    out = LAYERS / f"{spec['id']}.geojson"
    geodata.to_file(out, driver="GeoJSON", COORDINATE_PRECISION=6)
    attrs = [column for column in geodata.columns if column not in ("geometry", "source", "publisher")]
    return {
        "status": "ok",
        "features": len(geodata),
        "geom_types": geodata.geom_type.value_counts().to_dict(),
        "attrs": attrs,
        "bytes": out.stat().st_size,
    }


def write_water_build_report(rows: list[dict]) -> None:
    SRCDIR.mkdir(parents=True, exist_ok=True)
    (SRCDIR / "_build_report.json").write_text(
        json.dumps({"built": date.today().isoformat(), "layers": rows}, indent=2),
        encoding="utf-8",
    )


def read_any(path: Path) -> gpd.GeoDataFrame:
    try:
        return gpd.read_file(path)
    except Exception:
        meta, _fids, geom_wkb, field_data = pyogrio_read(path)
        fields = meta["fields"]
        geometries, ok = [], []
        for index, wkb in enumerate(geom_wkb):
            if wkb is None:
                continue
            try:
                geometries.append(shapely.from_wkb(wkb))
                ok.append(index)
            except Exception:
                continue
        data = {name: field_data[column][ok] for column, name in enumerate(fields)}
        return gpd.GeoDataFrame(data, geometry=geometries, crs=meta["crs"])


def clean_geodataframe(geodata: gpd.GeoDataFrame, spec: dict) -> gpd.GeoDataFrame:
    geodata = geodata[geodata.geometry.notna() & ~geodata.geometry.is_empty].copy()
    geodata = geodata.set_crs(4326, allow_override=True) if geodata.crs is None else geodata.to_crs(4326)
    if spec.get("simplify"):
        geodata["geometry"] = geodata.geometry.simplify(spec["simplify"], preserve_topology=True)
        geodata = geodata[geodata.geometry.notna() & ~geodata.geometry.is_empty]
    if spec.get("centroid"):
        geodata["geometry"] = geodata.geometry.representative_point()
    keep = [column for column in spec.get("keep", []) if column in geodata.columns]
    geodata = geodata[keep + ["geometry"]].copy()
    geodata["source"] = "OpenCity (data.opencity.in)"
    geodata["publisher"] = spec["pub"]
    return geodata
