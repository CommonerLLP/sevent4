from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from sevent4.city_dataset import CityDataset
from sevent4.application.metrics import OUTPUT_COLUMNS
from sevent4.ports.metrics import WardServiceAccessInput


class FileWardServiceAccessInputRepository:
    def __init__(self, city_config: str | Path | CityDataset) -> None:
        self.city_config = city_config

    def load(self) -> WardServiceAccessInput:
        city = self.city_config if isinstance(self.city_config, CityDataset) else CityDataset.from_yaml(self.city_config)
        return WardServiceAccessInput(
            wards=gpd.read_file(city.source_dir / "amc" / "Wards.geojson"),
            crs_metric=city.crs_metric,
            service_points={
                "libraries": _amc_libraries(city),
                "schools": _points_json(city.source_dir / "services" / "schools.json"),
                "health": _points_json(city.source_dir / "services" / "health.json"),
                "toilets": _points_json(city.source_dir / "services" / "toilets.json"),
                "police": _points_json(city.source_dir / "services" / "police.json"),
                "fire": _points_json(city.source_dir / "services" / "emergency.json"),
                "universities": _service_group(city.source_dir / "services" / "civic.json", ["university", "college"]),
                "gtfs_stops": _points_json(city.source_dir / "transit" / "gtfs_stops.json"),
            },
            builtup=_read_optional(
                city.source_dir
                / "cities"
                / "Builtup"
                / "2000_2014_Ahmedabad_Builtup"
                / "2000_2014_Ahmedabad_Builtup.geojson"
            ),
            population=_read_optional(
                city.source_dir / "cities" / "Population" / "2000_2015_Ahmedabad_Population.geojson"
            ),
        )


class CsvWardServiceAccessWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_rows(self, rows: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows)[OUTPUT_COLUMNS].to_csv(self.path, index=False)


def _points_json(path: Path) -> gpd.GeoDataFrame:
    rows = json.loads(path.read_text()) if path.exists() else []
    return _rows_to_points(rows)


def _service_group(path: Path, keys: list[str]) -> gpd.GeoDataFrame:
    data = json.loads(path.read_text()) if path.exists() else {}
    rows = []
    for key in keys:
        rows.extend(data.get(key, []))
    return _rows_to_points(rows)


def _amc_libraries(city: CityDataset) -> gpd.GeoDataFrame:
    return gpd.read_file(city.source_dir / "amc" / "Library.geojson").to_crs(4326)


def _rows_to_points(rows: list[dict]) -> gpd.GeoDataFrame:
    points = []
    for row in rows:
        try:
            points.append(Point(float(row["lon"]), float(row["lat"])))
        except (KeyError, TypeError, ValueError):
            continue
    return gpd.GeoDataFrame(geometry=points, crs=4326)


def _read_optional(path: Path) -> gpd.GeoDataFrame | None:
    return gpd.read_file(path) if path.exists() else None
