from __future__ import annotations

import sys
import time
from typing import Sequence

import numpy as np

from sevent4.application.heat import HeatGrid
from sevent4.domain.heat import celsius_from_landsat_st, qa_mask

STAC_API = "https://planetarycomputer.microsoft.com/api/stac/v1"


class PlanetaryComputerHeatSource:
    """Builds the median summer land-surface-temperature grid from the Microsoft
    Planetary Computer Landsat Collection-2 Level-2 archive."""

    def median_grid(self, bbox: Sequence[float], datetime: str, cloud_cover: float) -> HeatGrid:
        try:
            import planetary_computer
            import pystac_client
            import rioxarray  # noqa: F401
            import xarray as xr
            from rasterio.enums import Resampling
            from rasterio.warp import transform_bounds
        except ImportError as exc:  # pragma: no cover - environment guard
            raise SystemExit(
                f"Missing heat dependency: {exc.name}. Install with: python3 -m pip install -e '.[heat]'"
            )

        catalog = pystac_client.Client.open(STAC_API, modifier=planetary_computer.sign_inplace)
        # Narrow per-summer windows page quickly; a single multi-year window times out.
        start_year = int(datetime[:4])
        end_year = int(datetime.split("/")[-1][:4])
        found: dict[str, object] = {}
        for year in range(start_year, end_year + 1):
            window = f"{year}-04-01/{year}-06-30"
            for attempt in range(3):
                try:
                    search = catalog.search(
                        collections=["landsat-c2-l2"],
                        bbox=bbox,
                        datetime=window,
                        query={"eo:cloud_cover": {"lt": cloud_cover}},
                    )
                    for item in search.items():
                        if (
                            item.datetime.month in (4, 5, 6)
                            and item.properties.get("view:sun_elevation", 1) > 0
                            and item.properties.get("platform") in ("landsat-8", "landsat-9")
                        ):
                            found[item.id] = item
                    break
                except Exception as exc:  # noqa: BLE001
                    print(f"search retry {window} attempt {attempt+1}: {exc}", file=sys.stderr)
                    time.sleep(5)
            else:
                print(f"search FAILED for window {window}", file=sys.stderr)
        items = sorted(found.values(), key=lambda item: item.datetime)
        if not items:
            raise SystemExit("No summer daytime Landsat scenes found for the requested city/window.")

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

            left, bottom, right, top = transform_bounds("EPSG:4326", st.rio.crs, *bbox)
            st = st.rio.clip_box(left, bottom, right, top)
            qa = qa.rio.clip_box(left, bottom, right, top)
            if ref_grid is None:
                ref_grid = st
            else:
                qa = qa.rio.reproject_match(ref_grid, resampling=Resampling.nearest)
                st = st.rio.reproject_match(ref_grid, resampling=Resampling.bilinear)

            good = qa_mask(qa.values)
            celsius = celsius_from_landsat_st(st.values, good)
            if celsius.ndim == 3:
                celsius = celsius[0]
            layers.append(
                xr.DataArray(
                    celsius,
                    dims=ref_grid.dims[-2:],
                    coords={d: ref_grid.coords[d] for d in ref_grid.dims[-2:]},
                )
            )
            print(f"ok {item.id}: valid_px={np.isfinite(celsius).sum()}", file=sys.stderr)

        if not layers or ref_grid is None:
            raise SystemExit("No usable scenes after cloud masking.")

        stack = xr.concat(layers, dim="t")
        median = stack.median(dim="t", skipna=True)
        median = median.rio.write_crs(ref_grid.rio.crs)
        median = median.rio.write_transform(ref_grid.rio.transform())
        median = median.assign_coords({d: ref_grid.coords[d] for d in median.dims})
        median.rio.write_crs(ref_grid.rio.crs, inplace=True)
        m4326 = median.rio.reproject("EPSG:4326", resampling=Resampling.bilinear, nodata=np.nan)

        data = m4326.values
        west, south, east, north = m4326.rio.bounds()
        return HeatGrid(
            data=data,
            lon=m4326.x.values,
            lat=m4326.y.values,
            bounds=[west, south, east, north],
            scene_log=scene_log,
        )
