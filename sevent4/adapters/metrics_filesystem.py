from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from sevent4.application.metrics import OUTPUT_COLUMNS
from sevent4.city_dataset import CityDataset
from sevent4.ports.metrics import ServiceAccessCompositeInput, WardServiceAccessInput, WardTransitFrequencyInput


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


class FileWardTransitFrequencyInputRepository:
    def __init__(
        self,
        wards_path: str | Path,
        gtfs_dir: str | Path,
        *,
        buffer_m: float = 2500.0,
    ) -> None:
        self.wards_path = Path(wards_path)
        self.gtfs_dir = Path(gtfs_dir)
        self.buffer_m = buffer_m

    def load(self) -> WardTransitFrequencyInput:
        return WardTransitFrequencyInput(
            wards=_read_json(self.wards_path),
            gtfs_routes=list(_read_csv(self.gtfs_dir / "routes.txt")),
            gtfs_trips=list(_read_csv(self.gtfs_dir / "trips.txt")),
            gtfs_stops=list(_read_csv(self.gtfs_dir / "stops.txt")),
            gtfs_stop_times=list(_read_csv(self.gtfs_dir / "stop_times.txt")),
            buffer_m=self.buffer_m,
        )


class GeoJsonWardTransitFrequencyWriter:
    def __init__(self, wards_path: str | Path) -> None:
        self.wards_path = Path(wards_path)

    def write_wards(self, document: dict) -> None:
        self.wards_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


class FileServiceAccessCompositeInputRepository:
    def __init__(self, wards_path: str | Path, acs_path: str | Path, crosswalk_path: str | Path) -> None:
        self.wards_path = Path(wards_path)
        self.acs_path = Path(acs_path)
        self.crosswalk_path = Path(crosswalk_path)

    def load(self) -> ServiceAccessCompositeInput:
        return ServiceAccessCompositeInput(
            wards=_read_json(self.wards_path),
            acs=_read_json(self.acs_path),
            crosswalk_records=_read_json(self.crosswalk_path).get("records", []),
        )


class GeoJsonServiceAccessCompositeWriter:
    def __init__(self, wards_path: str | Path, acs_path: str | Path) -> None:
        self.wards_path = Path(wards_path)
        self.acs_path = Path(acs_path)

    def write_documents(self, wards: dict, acs: dict) -> None:
        self.wards_path.write_text(json.dumps(wards, ensure_ascii=False), encoding="utf-8")
        self.acs_path.write_text(json.dumps(acs, ensure_ascii=False), encoding="utf-8")


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


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)
