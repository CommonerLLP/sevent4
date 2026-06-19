#!/usr/bin/env python3
"""Build curated Bengaluru jurisdiction + waste GeoJSON layers from the OpenCity _raw archive.

The thesis layers: GBA (5 corporations, 2025), GBA zones, BDA, BWSSB, and traffic
police each cut Bengaluru differently than BBMP wards. Plus BBMP solid-waste sites.
Heavy operational layers (113k-point streetlights per zone, 87k sewerage lines,
BMTC division maps with broken geometries) stay in _raw and are not promoted here.

    python3 scripts/recipes/bengaluru/build_opencity_jurisdiction_layers.py
"""
from __future__ import annotations
import json, warnings
from datetime import date
from pathlib import Path

import geopandas as gpd
import shapely
from pyogrio.raw import read as praw

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/cities/bengaluru/source/opencity/_raw"
LAYERS = ROOT / "data/cities/bengaluru/layers"
SRCDIR = ROOT / "data/cities/bengaluru/source/opencity"

KML_CRUFT = {"id", "Name", "description", "timestamp", "begin", "end", "altitudeMode",
             "tessellate", "extrude", "visibility", "drawOrder", "icon", "snippet",
             "fid", "layer"}

BDA = "Bangalore Development Authority (BDA)"
GBA = "Greater Bengaluru Authority (GBA)"
BWSSB = "Bangalore Water Supply and Sewerage Board (BWSSB)"
TP = "Bengaluru Traffic Police"
BBMP = "Bruhat Bengaluru Mahanagara Palike (BBMP)"

CURATED = [
    dict(id="gba_corporations", slug="greater-bengaluru-authority-corporations-delimitation-2025",
         file="Greater_Bengaluru_Authority_Five_Corporations_Map_-_September_2025.kml",
         pub=GBA, simplify=0.0002),
    dict(id="gba_zones", slug="greater-bengaluru-authority-corporations-delimitation-2025",
         file="GBA_Zones_2025.kml", pub=GBA, simplify=0.0002),
    dict(id="bda_zones", slug="bda-jurisdiction-and-boundary",
         file="BDA_Zones_and_Subdivisions.geojson", pub=BDA, simplify=0.0002),
    dict(id="bwssb_divisions", slug="bwssb-boundary-maps",
         file="BWSSB_Division_Boundary_Maps.kml", pub=BWSSB, simplify=0.0002),
    dict(id="traffic_police_jurisdiction", slug="bengaluru-traffic-police-jurisdictions",
         file="Bengaluru_Traffic_Police_Jurisdictions_Map_2022.kml", pub=TP, simplify=0.0002),
    dict(id="bbmp_dry_waste_centres", slug="bbmp-solid-waste-management-data",
         file="BBMP_Dry_Waste_Collection_Centres_Map.kml", pub=BBMP, simplify=0.0),
    dict(id="bbmp_landfills", slug="bbmp-solid-waste-management-data",
         file="BBMP_Landfill_Locations_Map.kml", pub=BBMP, simplify=0.0),
]


def read_any(path: Path) -> gpd.GeoDataFrame:
    try:
        return gpd.read_file(path)
    except Exception:
        meta, _fids, geom_wkb, field_data = praw(path)
        fields = meta["fields"]
        geoms, ok = [], []
        for i, wkb in enumerate(geom_wkb):
            if wkb is None:
                continue
            try:
                geoms.append(shapely.from_wkb(wkb)); ok.append(i)
            except Exception:
                continue
        data = {n: field_data[j][ok] for j, n in enumerate(fields)}
        skipped = len(geom_wkb) - len(ok)
        if skipped:
            print(f"     (salvaged: skipped {skipped} malformed geometries)")
        return gpd.GeoDataFrame(data, geometry=geoms, crs=meta["crs"])


def clean(g: gpd.GeoDataFrame, spec: dict) -> gpd.GeoDataFrame:
    g = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
    g = g.set_crs(4326, allow_override=True) if g.crs is None else g.to_crs(4326)
    if spec.get("simplify"):
        g["geometry"] = g.geometry.simplify(spec["simplify"], preserve_topology=True)
        g = g[g.geometry.notna() & ~g.geometry.is_empty]
    # keep all meaningful (non-cruft, non-empty) attributes
    keep = [c for c in g.columns if c != "geometry" and c not in KML_CRUFT and g[c].notna().any()]
    g = g[keep + ["geometry"]].copy()
    g["source"] = "OpenCity (data.opencity.in)"
    g["publisher"] = spec["pub"]
    return g


def main() -> None:
    built = []
    for spec in CURATED:
        src = RAW / spec["slug"] / spec["file"]
        rec = {"id": spec["id"], "file": f"{spec['id']}.geojson",
               "source_file": spec["file"], "publisher": spec["pub"], "dataset_slug": spec["slug"]}
        if not src.exists():
            rec["status"] = "missing_raw"; built.append(rec)
            print(f"  MISSING raw: {spec['file']}"); continue
        try:
            g = clean(read_any(src), spec)
            out = LAYERS / f"{spec['id']}.geojson"
            g.to_file(out, driver="GeoJSON", COORDINATE_PRECISION=6)
            attrs = [c for c in g.columns if c not in ("geometry", "source", "publisher")]
            rec.update(status="ok", features=len(g),
                       geom_types=g.geom_type.value_counts().to_dict(),
                       attrs=attrs, bytes=out.stat().st_size)
            print(f"  [ok] {spec['id']:<28} {len(g):>5} feats {out.stat().st_size/1e6:5.1f}MB  attrs={attrs[:6]}")
        except Exception as e:
            rec["status"] = f"error: {type(e).__name__}: {e}"
            print(f"  [ERR] {spec['id']:<28} {type(e).__name__}: {str(e)[:70]}")
        built.append(rec)

    (SRCDIR / "_build_report.json").write_text(json.dumps(
        {"built": date.today().isoformat(), "layers": built}, indent=2), encoding="utf-8")
    ok = [b for b in built if b.get("status") == "ok"]
    print(f"\nbuilt {len(ok)}/{len(built)} Bengaluru jurisdiction layers -> {LAYERS}")


if __name__ == "__main__":
    main()
