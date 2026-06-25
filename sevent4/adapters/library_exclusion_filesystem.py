from __future__ import annotations

import csv
import json
from pathlib import Path

from sevent4.domain.library_exclusion import INDEX_FIELDS, SUMMARY_FIELDS, nearest_point_distance_m

WGS84 = "EPSG:4326"
METRIC = "EPSG:32643"


class LibraryExclusionRepository:
    """Ahmedabad ward/library inputs + exclusion outputs. The nearest-library
    distance is a metric-CRS spatial join (geopandas); everything else is JSON/CSV."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)
        city = self.repo_root / "data" / "cities" / "ahmedabad"
        self.layers = city / "layers"
        self.wards_path = self.layers / "wards.geojson"
        self.excl_path = self.layers / "ward_library_exclusion.geojson"
        self.lib_csv = city / "source" / "libraries" / "ahmedabad_library_locations.csv"
        self.out_dir = city / "derived" / "library_access"

    def nearest_library_km(self) -> dict[str, float]:
        import geopandas as gpd
        import pandas as pd

        wards = gpd.read_file(self.wards_path).to_crs(METRIC)
        raw = pd.read_csv(self.lib_csv)
        libraries = gpd.GeoDataFrame(
            raw,
            geometry=gpd.points_from_xy(raw["longitude"], raw["latitude"]),
            crs=WGS84,
        ).to_crs(METRIC)
        points = [(geom.x, geom.y) for geom in libraries.geometry]
        out: dict[str, float] = {}
        for _, ward in wards.iterrows():
            centroid = ward.geometry.centroid
            out[ward["Name"]] = nearest_point_distance_m(centroid.x, centroid.y, points) / 1000.0
        return out

    def load_wards(self) -> dict:
        return json.loads(self.wards_path.read_text())

    def write_wards(self, document: dict) -> None:
        self.wards_path.write_text(json.dumps(document, ensure_ascii=False))

    def write_exclusion_layer(self, document: dict) -> None:
        self.excl_path.write_text(json.dumps(document, ensure_ascii=False))

    def write_index_csv(self, rows: list[dict]) -> None:
        self._write_csv(self.out_dir / "library_exclusion_index.csv", rows, INDEX_FIELDS)

    def write_summary_csv(self, summary: dict) -> None:
        self._write_csv(self.out_dir / "library_exclusion_summary.csv", [summary], SUMMARY_FIELDS)

    def _write_csv(self, path: Path, rows: list[dict], fieldnames: list[str]) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    @property
    def index_csv_path(self) -> Path:
        return self.out_dir / "library_exclusion_index.csv"

    @property
    def exclusion_layer_relpath(self) -> Path:
        return self.excl_path.relative_to(self.repo_root)
