#!/usr/bin/env python3
"""Aggregate the 30m Landsat LST raster (heat30m.tif) to ward polygons.

For each ward in wards.geojson, computes mean and max land-surface temperature
(degrees C) over the heat raster and writes ward_heat.geojson: a copy of the
ward geometry + properties with mean_lst_c, max_lst_c, lst_px_count added.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate LST raster to wards.")
    parser.add_argument("--city", required=True)
    parser.add_argument("--layers-dir", help="Override layers dir.")
    args = parser.parse_args()

    city = args.city.lower()
    layers = Path(args.layers_dir) if args.layers_dir else REPO / "data" / "cities" / city / "layers"
    tif_path = layers / "heat30m.tif"
    wards_path = layers / "wards.geojson"
    if not tif_path.exists():
        sys.exit(f"No heat raster at {tif_path}")
    if not wards_path.exists():
        sys.exit(f"No wards at {wards_path}")

    wards = json.loads(wards_path.read_text(encoding="utf-8"))

    out_features = []
    means = []
    with rasterio.open(tif_path) as src:
        nodata = src.nodata
        for feat in wards["features"]:
            geom = feat.get("geometry")
            mean_c = None
            max_c = None
            count = 0
            if geom is not None:
                try:
                    out_img, _ = rio_mask(src, [geom], crop=True, filled=True, nodata=np.nan)
                    vals = out_img[0].astype("float32")
                    finite = vals[np.isfinite(vals)]
                    if nodata is not None and not np.isnan(nodata):
                        finite = finite[finite != nodata]
                    finite = finite[(finite > -10) & (finite < 70)]
                    if finite.size:
                        mean_c = round(float(finite.mean()), 2)
                        max_c = round(float(finite.max()), 2)
                        count = int(finite.size)
                except Exception as exc:  # noqa: BLE001
                    print(f"ward agg skip: {exc}", file=sys.stderr)

            props = dict(feat.get("properties", {}))
            props["mean_lst_c"] = mean_c
            props["max_lst_c"] = max_c
            props["lst_px_count"] = count
            if mean_c is not None:
                means.append(mean_c)
            out_features.append({"type": "Feature", "properties": props, "geometry": geom})

    out = {
        "type": "FeatureCollection",
        "name": "ward_heat",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": out_features,
    }
    (layers / "ward_heat.geojson").write_text(json.dumps(out), encoding="utf-8")

    covered = len(means)
    summary = {
        "city": city,
        "wards": len(out_features),
        "wards_with_lst": covered,
        "mean_lst_min": round(min(means), 1) if means else None,
        "mean_lst_max": round(max(means), 1) if means else None,
    }
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
