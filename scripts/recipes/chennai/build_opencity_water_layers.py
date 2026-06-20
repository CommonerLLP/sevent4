#!/usr/bin/env python3
"""Build curated Chennai water/flood GeoJSON layers from the OpenCity _raw archive.

Reads the gitignored KML/KMZ archive produced by acquire_opencity_water.py and
writes a curated, story-driven subset to data/cities/chennai/layers/ as WGS84
GeoJSON. Keeps the meaningful ExtendedData attributes (DEPTH, F_REMARKS, ZONE,
WARD, ...) and drops empty KML-standard cruft columns. Operational asset
inventories (DG sets, motors, valves, flow meters, ...) are intentionally left
in _raw and not promoted.

    python3 scripts/recipes/chennai/build_opencity_water_layers.py
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
RAW = ROOT / "data/cities/chennai/source/opencity/_raw"
LAYERS = ROOT / "data/cities/chennai/layers"
SRCDIR = ROOT / "data/cities/chennai/source/opencity"

# empty KML-standard columns to drop
KML_CRUFT = {"id", "Name", "description", "timestamp", "begin", "end",
             "altitudeMode", "tessellate", "extrude", "visibility",
             "drawOrder", "icon", "snippet"}

GCC = "Greater Chennai Corporation (GCC)"
CMWSSB = "Chennai Metropolitan Water Supply and Sewerage Board (CMWSSB)"

# meaningful drain attributes to keep (the raw KML carries 42 columns; the rest are
# survey/engineering cruft — invert levels, eastings, manhole shapes, road ids)
DRAIN_KEEP = ["DRAIN_TYPE", "DRAIN_SIZE", "DRAIN_DEP", "DRAIN_WID", "DRAIN_LEN",
              "MAT_TYP", "SWD_MAT", "STATUS", "COVER", "FUND", "CONTRACTOR",
              "CONST_DATE", "RECONST", "WARD", "ZONE", "ST_NAME", "LOCATION",
              "WATER_FLOW", "RD_CLASS"]

# id, slug, filename, publisher, centroid, simplify-tolerance (deg), keep-attrs
CURATED = [
    dict(id="flood_hazard", slug="chennai-flooding-data",
         file="Chennai_Flood_Hazard_Zones_Map.kml", pub=GCC, centroid=False,
         simplify=0.0001, keep=["CATEGORY"]),
    dict(id="flood_inundation", slug="chennai-flooding-data",
         file="Chennai_Inundation_Points_with_Depth_of_Inundation.kml", pub=GCC,
         centroid=False, simplify=0.0, keep=["DEPTH", "F_REMARKS", "WARD", "ZONE"]),
    dict(id="flood_2015", slug="chennai-flooding-data",
         file="Chennai_Flooding_Points_in_2015.kml", pub=GCC, centroid=False,
         simplify=0.0, keep=["ZONE", "DIVISION"]),
    dict(id="stormwater_drains", slug="chennai-stormwater-drain-swd-maps",
         file="Chennai_Storm_Water_Drains_-_SWD_-_Map_2023.kml", pub=GCC,
         centroid=False, simplify=0.00003, keep=DRAIN_KEEP),
    dict(id="cmwssb_depots", slug="cmwssb-administrative-boundaries",
         file="Depot_Boundaries_Map.kml", pub=CMWSSB, centroid=False,
         simplify=0.0001, keep=["depot", "dae_range", "se_territory", "area_in_sqkm"]),
    dict(id="sewer_command_area", slug="chennai-sewerage-collection-system",
         file="Sewerage_Command_Area.kml", pub=CMWSSB, centroid=False, simplify=0.0001,
         keep=["name_of_the_sps", "area_no_of_the_sps", "length_of_sewer_m",
               "no_of_mh", "se_territory_of_the_sps", "status"]),
    dict(id="water_overhead_tanks", slug="chennai-water-distribution-stations",
         file="Water_Supply_Overhead_Tanks.kml", pub=CMWSSB, centroid=True,
         simplify=0.0, keep=["location", "depot", "capacity_of_oht_ml",
                             "name_of_the_wds", "commissioned_on", "status"]),
]


def read_kml(path: Path) -> gpd.GeoDataFrame:
    try:
        return gpd.read_file(path)
    except Exception:
        # A malformed geometry breaks the bulk WKB->shapely conversion (seen in the
        # 10k-feature SWD map). Drop to the low-level reader and convert per feature,
        # skipping only the individual bad geometries.
        meta, _fids, geom_wkb, field_data = praw(path)
        fields = meta["fields"]
        geoms, ok_idx = [], []
        for i, wkb in enumerate(geom_wkb):
            if wkb is None:
                continue
            try:
                geoms.append(shapely.from_wkb(wkb))
                ok_idx.append(i)
            except Exception:
                continue
        data = {name: field_data[j][ok_idx] for j, name in enumerate(fields)}
        skipped = len(geom_wkb) - len(ok_idx)
        if skipped:
            print(f"     (salvaged: skipped {skipped} malformed geometries)")
        return gpd.GeoDataFrame(data, geometry=geoms, crs=meta["crs"])


def clean(g: gpd.GeoDataFrame, spec: dict) -> gpd.GeoDataFrame:
    g = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
    if g.crs is None:
        g.set_crs(4326, inplace=True)
    else:
        g = g.to_crs(4326)
    if spec.get("simplify"):
        g["geometry"] = g.geometry.simplify(spec["simplify"], preserve_topology=True)
        g = g[g.geometry.notna() & ~g.geometry.is_empty]
    if spec.get("centroid"):
        g["geometry"] = g.geometry.representative_point()
    keep = [c for c in spec.get("keep", []) if c in g.columns]
    g = g[keep + ["geometry"]].copy()
    g["source"] = "OpenCity (data.opencity.in)"
    g["publisher"] = spec["pub"]
    return g


def main() -> None:
    LAYERS.mkdir(parents=True, exist_ok=True)  # ensure the target exists on a fresh checkout
    built = []
    for spec in CURATED:
        out_id, slug, fname = spec["id"], spec["slug"], spec["file"]
        src = RAW / slug / fname
        rec = {"id": out_id, "file": f"{out_id}.geojson", "source_file": fname,
               "publisher": spec["pub"], "dataset_slug": slug}
        if not src.exists():
            rec["status"] = "missing_raw"
            built.append(rec); print(f"  MISSING raw: {fname}"); continue
        try:
            g = clean(read_kml(src), spec)
            out = LAYERS / f"{out_id}.geojson"
            g.to_file(out, driver="GeoJSON", COORDINATE_PRECISION=6)
            gt = g.geom_type.value_counts().to_dict()
            attrs = [c for c in g.columns if c not in ("geometry", "source", "publisher")]
            rec.update(status="ok", features=len(g), geom_types=gt, attrs=attrs,
                       bytes=out.stat().st_size)
            print(f"  [ok] {out_id:<22} {len(g):>5} feats {out.stat().st_size/1e6:5.1f}MB  {gt}  attrs={attrs}")
        except Exception as e:
            rec["status"] = f"error: {type(e).__name__}: {e}"
            print(f"  [ERR] {out_id:<22} {type(e).__name__}: {str(e)[:80]}")
        built.append(rec)

    (SRCDIR / "_build_report.json").write_text(json.dumps({
        "built": date.today().isoformat(), "layers": built,
    }, indent=2), encoding="utf-8")
    ok = [b for b in built if b.get("status") == "ok"]
    print(f"\nbuilt {len(ok)}/{len(built)} Chennai water/flood layers -> {LAYERS}")


if __name__ == "__main__":
    main()
