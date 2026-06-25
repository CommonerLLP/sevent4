"""Filesystem, network, and geospatial adapter for Bengaluru OpenCity recipes."""
from __future__ import annotations

import json
import os
import hashlib
import warnings
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

import geopandas as gpd
import requests
import shapely
from pyogrio.raw import read as pyogrio_read

from sevent4.domain.bengaluru_opencity import KML_CRUFT

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / "data" / "sources" / "opencity" / "_catalogue" / "opencity_catalogue.json"
ARCHIVE = Path(os.environ.get("OPENCITY_ARCHIVE", str(ROOT / "data" / "sources" / "opencity")))
FINANCE_RAW = ARCHIVE / "bengaluru" / "raw"
BOUNDARY_OUT = ROOT / "data" / "cities" / "bengaluru" / "source" / "boundaries"
BOUNDARY_RAW = BOUNDARY_OUT / "_raw"
OPENCITY_RAW = ROOT / "data" / "cities" / "bengaluru" / "source" / "opencity" / "_raw"
OPENCITY_SOURCE = ROOT / "data" / "cities" / "bengaluru" / "source" / "opencity"
LAYERS = ROOT / "data" / "cities" / "bengaluru" / "layers"
API = "https://data.opencity.in/api/3/action/package_show?id="
UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas)"}


def archive_exists() -> bool:
    return ARCHIVE.exists()


def read_catalogue() -> dict:
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


def fetch_finance_resource(slug: str, filename: str, url: str) -> int:
    target_dir = FINANCE_RAW / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    data = fetch_bytes(url)
    (target_dir / filename).write_bytes(data)
    return len(data)


def write_finance_manifest(manifest: list[dict]) -> None:
    FINANCE_RAW.mkdir(parents=True, exist_ok=True)
    (FINANCE_RAW / "_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_boundary_resource(layer_id: str, url: str) -> int:
    BOUNDARY_RAW.mkdir(parents=True, exist_ok=True)
    data = fetch_bytes(url)
    (BOUNDARY_RAW / f"{layer_id}.kml").write_bytes(data)
    return len(data)


def convert_boundary_resource(layer_id: str, target: str) -> dict:
    BOUNDARY_OUT.mkdir(parents=True, exist_ok=True)
    kml = BOUNDARY_RAW / f"{layer_id}.kml"
    gdf = gpd.read_file(kml)
    if gdf.crs is None:
        gdf.set_crs(4326, inplace=True)
    gdf = gdf.to_crs(4326)
    if layer_id == "acs":
        if "ac_name" not in gdf.columns:
            gdf["ac_name"] = gdf.get("Name", "")
        gdf["office"] = "MLA"
    elif layer_id == "pcs":
        if "pc_name" not in gdf.columns:
            gdf["pc_name"] = gdf.get("Name", "")
        gdf["office"] = "MP"
    gdf.to_file(BOUNDARY_OUT / target, driver="GeoJSON")
    return {"features": len(gdf), "columns": [column for column in gdf.columns if column != "geometry"]}


def write_boundary_sources(provenance: list[dict[str, object]]) -> None:
    BOUNDARY_OUT.mkdir(parents=True, exist_ok=True)
    (BOUNDARY_OUT / "sources.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False), encoding="utf-8")


def write_boundary_credits(provenance: list[dict[str, object]]) -> None:
    lines = [
        "# Bengaluru boundary spine — sources & credit\n",
        "_Acquired from data.opencity.in. Cite: **publisher → OpenCity → sevent4 (processed)**._\n",
    ]
    for row in provenance:
        lines.append(
            f"- **{row['layer']}** (`{row['file']}`, {row['features']} features) — "
            f"{row['publisher_org']} · published on OpenCity · {row['opencity_dataset']}"
        )
    (BOUNDARY_OUT / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers=UA)
    with urlopen(request, timeout=120) as response:
        return response.read()


def package_show(slug: str) -> dict | None:
    for attempt in range(3):
        try:
            return requests.get(API + slug, headers=UA, timeout=90).json()
        except Exception:
            if attempt == 2:
                return None
    return None


def fetch_jurisdiction_resource(slug: str, filename: str, url: str) -> dict:
    target = OPENCITY_RAW / slug / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        blob = request_bytes(url)
        target.write_bytes(blob)
        return {"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(), "status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"bytes": 0, "sha256": "", "status": f"error: {type(exc).__name__}"}


def write_jurisdiction_manifest(summary: dict) -> None:
    OPENCITY_RAW.mkdir(parents=True, exist_ok=True)
    payload = {"retrieved": date.today().isoformat(), **summary}
    (OPENCITY_RAW / "_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def source_exists(spec: dict) -> bool:
    return (OPENCITY_RAW / spec["slug"] / spec["file"]).exists()


def build_curated_layer(spec: dict) -> dict:
    warnings.filterwarnings("ignore")
    LAYERS.mkdir(parents=True, exist_ok=True)
    source = OPENCITY_RAW / spec["slug"] / spec["file"]
    gdf = clean_geodataframe(read_any(source), spec)
    out = LAYERS / f"{spec['id']}.geojson"
    gdf.to_file(out, driver="GeoJSON", COORDINATE_PRECISION=6)
    attrs = [column for column in gdf.columns if column not in ("geometry", "source", "publisher")]
    return {
        "status": "ok",
        "features": len(gdf),
        "geom_types": gdf.geom_type.value_counts().to_dict(),
        "attrs": attrs,
        "bytes": out.stat().st_size,
    }


def write_jurisdiction_build_report(rows: list[dict]) -> None:
    OPENCITY_SOURCE.mkdir(parents=True, exist_ok=True)
    (OPENCITY_SOURCE / "_build_report.json").write_text(
        json.dumps({"built": date.today().isoformat(), "layers": rows}, indent=2),
        encoding="utf-8",
    )


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


def clean_geodataframe(gdf: gpd.GeoDataFrame, spec: dict) -> gpd.GeoDataFrame:
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    gdf = gdf.set_crs(4326, allow_override=True) if gdf.crs is None else gdf.to_crs(4326)
    if spec.get("simplify"):
        gdf["geometry"] = gdf.geometry.simplify(spec["simplify"], preserve_topology=True)
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
    keep = [
        column for column in gdf.columns
        if column != "geometry" and column not in KML_CRUFT and gdf[column].notna().any()
    ]
    gdf = gdf[keep + ["geometry"]].copy()
    gdf["source"] = "OpenCity (data.opencity.in)"
    gdf["publisher"] = spec["pub"]
    return gdf
