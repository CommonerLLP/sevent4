from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

import numpy as np

from sevent4.application.heat import HeatArtifacts


class FileWardHeatRepository:
    """Reads a city's ward polygons and exposes a rasterio-backed per-ward
    sampler over heat30m.tif."""

    def __init__(self, root: str | Path, city: str, layers_dir: str | Path | None = None) -> None:
        self.layers_dir = Path(layers_dir) if layers_dir else Path(root) / "data" / "cities" / city / "layers"

    def load_wards(self) -> Mapping[str, Any]:
        return json.loads((self.layers_dir / "wards.geojson").read_text(encoding="utf-8"))

    @contextmanager
    def open_sampler(self) -> Iterator[tuple[Any, float | None]]:
        import rasterio
        from rasterio.mask import mask as rio_mask

        path = self.layers_dir / "heat30m.tif"
        with rasterio.open(path) as src:
            nodata = src.nodata

            def sample(geometry):
                try:
                    out_image, _ = rio_mask(src, [geometry], crop=True, filled=True, nodata=np.nan)
                    return out_image[0].astype("float32")
                except Exception:
                    return None

            yield sample, nodata

    def heat_tif_exists(self) -> bool:
        return (self.layers_dir / "heat30m.tif").exists()

    def wards_exist(self) -> bool:
        return (self.layers_dir / "wards.geojson").exists()


class FileHeatArtifactWriter:
    """Persists the raster heat artifacts (GeoTIFF, PNG, npz grid, bounds + scene
    logs) and the ward_heat GeoJSON for a city."""

    def __init__(self, root: str | Path, city: str, layers_dir: str | Path | None = None) -> None:
        self.layers_dir = Path(layers_dir) if layers_dir else Path(root) / "data" / "cities" / city / "layers"

    def write_raster_artifacts(self, artifacts: HeatArtifacts) -> None:
        import rasterio
        from PIL import Image
        from rasterio.transform import from_bounds

        self.layers_dir.mkdir(parents=True, exist_ok=True)
        grid = artifacts.grid
        data = grid.data[0] if grid.data.ndim == 3 else grid.data
        west, south, east, north = grid.bounds
        height, width = data.shape
        transform = from_bounds(west, south, east, north, width, height)
        with rasterio.open(
            self.layers_dir / "heat30m.tif",
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=transform,
            nodata=float("nan"),
            compress="deflate",
        ) as dst:
            dst.write(data.astype("float32"), 1)

        Image.fromarray(artifacts.rgba, "RGBA").save(self.layers_dir / "heat30m.png")
        np.savez_compressed(self.layers_dir / "_heat30m_grid.npz", data=data, lon=grid.lon, lat=grid.lat)
        (self.layers_dir / "heat30m_bounds.json").write_text(
            json.dumps(artifacts.bounds_doc, indent=2), encoding="utf-8"
        )
        (self.layers_dir / "_heat30m_scenes.json").write_text(
            json.dumps(list(artifacts.scene_log), indent=2), encoding="utf-8"
        )

    def write_ward_heat(self, document: Mapping[str, Any]) -> None:
        self.layers_dir.mkdir(parents=True, exist_ok=True)
        (self.layers_dir / "ward_heat.geojson").write_text(
            json.dumps(document), encoding="utf-8"
        )


class FileHeatManifestStore:
    def __init__(self, root: str | Path, city: str) -> None:
        self.layers_dir = Path(root) / "data" / "cities" / city / "layers"
        self.manifest_path = self.layers_dir / "layer_manifest.json"

    def manifest_exists(self) -> bool:
        return self.manifest_path.exists()

    def has_heat_outputs(self) -> bool:
        return (self.layers_dir / "heat30m.png").exists() and (
            self.layers_dir / "ward_heat.geojson"
        ).exists()

    def load_manifest(self) -> Mapping[str, Any]:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def write_manifest(self, manifest: Mapping[str, Any]) -> None:
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def summary_json(summary: Mapping[str, Any], indent: int | None = 2) -> str:
    return json.dumps(summary, indent=indent)


def load_city_bbox(root: str | Path, city: str, layers_dir: str | Path | None = None) -> list[float]:
    # Prefer the committed heat bounds, so a refresh can source the bbox from a
    # public-only checkout (no gitignored city.yaml); fall back to city.yaml.
    if layers_dir is not None:
        bounds = Path(layers_dir) / "heat30m_bounds.json"
        if bounds.exists():
            return list(json.loads(bounds.read_text(encoding="utf-8"))["bbox"])
    import yaml

    config = yaml.safe_load(
        (Path(root) / "data" / "cities" / city / "city.yaml").read_text(encoding="utf-8")
    )
    return list(config["bbox"])


def write_heat_run_summary(root: str | Path, results: Mapping[str, Any]) -> None:
    path = Path(root) / "scripts" / "recipes" / "ahmedabad" / "_heat_run_summary.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
