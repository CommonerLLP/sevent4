#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[3]

# Ahmedabad is the first implemented heat recipe. Other cities can reuse this
# script by passing bbox/date arguments and adding city-specific defaults later.
DEFAULT_CITY = "ahmedabad"
DEFAULT_BBOX = [72.45, 22.90, 72.74, 23.18]
DEFAULT_DATETIME = "2023-04-01/2025-06-30"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a 30m Landsat surface-heat layer for a city.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Defaults to Ahmedabad.")
    parser.add_argument("--bbox", nargs=4, type=float, default=DEFAULT_BBOX, metavar=("W", "S", "E", "N"))
    parser.add_argument("--datetime", default=DEFAULT_DATETIME, help="STAC datetime window.")
    parser.add_argument("--out-dir", help="Layer output directory.")
    parser.add_argument("--cloud-cover", type=float, default=20.0)
    args = parser.parse_args()

    try:
        import planetary_computer
        import pystac_client
        import rioxarray  # noqa: F401
        import xarray as xr
        from PIL import Image
        from rasterio.enums import Resampling
        from rasterio.warp import transform_bounds
    except ImportError as exc:
        sys.exit(f"Missing heat dependency: {exc.name}. Install with: python3 -m pip install -e '.[heat]'")

    city = args.city.lower()
    out_dir = Path(args.out_dir) if args.out_dir else REPO / "data" / "cities" / city / "layers"
    out_dir.mkdir(parents=True, exist_ok=True)

    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    search = catalog.search(
        collections=["landsat-c2-l2"],
        bbox=args.bbox,
        datetime=args.datetime,
        query={"eo:cloud_cover": {"lt": args.cloud_cover}, "platform": {"in": ["landsat-8", "landsat-9"]}},
    )
    items = [
        item for item in search.items()
        if item.datetime.month in (4, 5, 6) and item.properties.get("view:sun_elevation", 1) > 0
    ]
    items.sort(key=lambda item: item.datetime)
    if not items:
        sys.exit("No summer daytime Landsat scenes found for the requested city/window.")

    scene_log = []
    layers = []
    ref_grid = None
    for item in items:
        scene_log.append({
            "id": item.id,
            "date": str(item.datetime)[:10],
            "cloud_cover": round(item.properties.get("eo:cloud_cover", -1), 2),
            "platform": item.properties.get("platform"),
            "sun_elev": round(item.properties.get("view:sun_elevation", -1), 1),
        })
        href_st = item.assets["lwir11"].href if "lwir11" in item.assets else item.assets["ST_B10"].href
        href_qa = item.assets["qa_pixel"].href
        try:
            st = rioxarray.open_rasterio(href_st, masked=False).squeeze()
            qa = rioxarray.open_rasterio(href_qa, masked=False).squeeze()
        except Exception as exc:  # noqa: BLE001
            print(f"skip {item.id}: {exc}", file=sys.stderr)
            continue

        left, bottom, right, top = transform_bounds("EPSG:4326", st.rio.crs, *args.bbox)
        st = st.rio.clip_box(left, bottom, right, top)
        qa = qa.rio.clip_box(left, bottom, right, top)
        if ref_grid is None:
            ref_grid = st
        else:
            qa = qa.rio.reproject_match(ref_grid, resampling=Resampling.nearest)
            st = st.rio.reproject_match(ref_grid, resampling=Resampling.bilinear)

        good = qa_mask(qa.values)
        celsius = st.values.astype("float32")
        celsius[celsius == 0] = np.nan
        celsius = celsius * 0.00341802 + 149.0 - 273.15
        celsius[~good] = np.nan
        celsius[(celsius < -10) | (celsius > 70)] = np.nan
        if celsius.ndim == 3:
            celsius = celsius[0]
        layers.append(xr.DataArray(celsius, dims=ref_grid.dims[-2:], coords={d: ref_grid.coords[d] for d in ref_grid.dims[-2:]}))
        print(f"ok {item.id}: valid_px={np.isfinite(celsius).sum()}", file=sys.stderr)

    if not layers or ref_grid is None:
        sys.exit("No usable scenes after cloud masking.")

    stack = xr.concat(layers, dim="t")
    median = stack.median(dim="t", skipna=True)
    median = median.rio.write_crs(ref_grid.rio.crs)
    median = median.rio.write_transform(ref_grid.rio.transform())
    median = median.assign_coords({d: ref_grid.coords[d] for d in median.dims})
    median.rio.write_crs(ref_grid.rio.crs, inplace=True)
    m4326 = median.rio.reproject("EPSG:4326", resampling=Resampling.bilinear, nodata=np.nan)

    tif_path = out_dir / "heat30m.tif"
    m4326.rio.to_raster(tif_path, dtype="float32", nodata=float("nan"), compress="deflate")

    west, south, east, north = m4326.rio.bounds()
    bounds = {"bbox": [west, south, east, north], "corners": [[west, north], [east, north], [east, south], [west, south]], "crs": "EPSG:4326"}
    (out_dir / "heat30m_bounds.json").write_text(json.dumps(bounds, indent=2), encoding="utf-8")

    data = m4326.values
    if data.ndim == 3:
        data = data[0]
    image = heat_png(data, Image)
    image.save(out_dir / "heat30m.png")
    np.savez_compressed(out_dir / "_heat30m_grid.npz", data=data, lon=m4326.x.values, lat=m4326.y.values)
    (out_dir / "_heat30m_scenes.json").write_text(json.dumps(scene_log, indent=2), encoding="utf-8")

    finite = data[np.isfinite(data)]
    print(json.dumps({"city": city, "scenes": len(items), "min_c": round(float(finite.min()), 2), "max_c": round(float(finite.max()), 2), "mean_c": round(float(finite.mean()), 2), "bbox": bounds["bbox"]}, indent=2))


def qa_mask(qa: np.ndarray) -> np.ndarray:
    bad = np.zeros(qa.shape, dtype=bool)
    for bit in (1, 2, 3, 4):
        bad |= ((qa.astype(np.uint16) >> bit) & 1).astype(bool)
    return ~(bad | (qa == 0))


def heat_png(data: np.ndarray, image_module):
    stops = [
        (30, (0, 80, 30)),
        (33, (120, 180, 40)),
        (36, (240, 230, 40)),
        (39, (245, 150, 30)),
        (42, (225, 50, 30)),
        (45, (150, 15, 20)),
        (48, (90, 0, 25)),
    ]
    xs = np.array([stop[0] for stop in stops], dtype="float32")
    rs = np.array([stop[1][0] for stop in stops], dtype="float32")
    gs = np.array([stop[1][1] for stop in stops], dtype="float32")
    bs = np.array([stop[1][2] for stop in stops], dtype="float32")
    valid = np.isfinite(data)
    values = np.where(valid, data, 30.0)
    rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
    rgba[..., 0] = np.interp(values, xs, rs).astype(np.uint8)
    rgba[..., 1] = np.interp(values, xs, gs).astype(np.uint8)
    rgba[..., 2] = np.interp(values, xs, bs).astype(np.uint8)
    rgba[..., 3] = np.where(valid, 220, 0).astype(np.uint8)
    return image_module.fromarray(rgba, "RGBA")


if __name__ == "__main__":
    main()
