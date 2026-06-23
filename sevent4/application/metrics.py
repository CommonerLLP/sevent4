from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import pandas as pd

from sevent4.ports.metrics import WardServiceAccessInput, WardServiceAccessWriter


SERVICE_COLUMNS = (
    "libraries",
    "schools",
    "health",
    "toilets",
    "police",
    "fire",
    "universities",
    "gtfs_stops",
)

OUTPUT_COLUMNS = [
    "Name",
    "ward_area_km2",
    "builtup_km2",
    "population_cells_proxy",
    *SERVICE_COLUMNS,
    "service_access",
    "service_gap",
    "service_priority",
]


@dataclass(frozen=True)
class WardServiceAccessResult:
    rows: list[dict]


def build_ward_service_access(
    inputs: WardServiceAccessInput,
    writer: WardServiceAccessWriter,
) -> WardServiceAccessResult:
    wards = inputs.wards[["Name", "geometry"]].copy().to_crs(inputs.crs_metric)
    wards["ward_area_km2"] = wards.geometry.area / 1e6

    for column in SERVICE_COLUMNS:
        points = inputs.service_points.get(column, _empty_points())
        _count_in_wards(wards, points.to_crs(inputs.crs_metric), column)

    _add_builtup_area(wards, inputs.builtup, inputs.crs_metric)
    _add_population_proxy(wards, inputs.population, inputs.crs_metric)

    population_proxy = wards["population_cells_proxy"].clip(lower=1)
    access_parts = []
    for service in ["libraries", "schools", "health", "gtfs_stops"]:
        access_parts.append(_norm(wards[service] / population_proxy))
    access = sum(access_parts) / len(access_parts)
    wards["service_access"] = access.round(3)
    wards["service_gap"] = (1 - access).round(3)
    wards["service_priority"] = (wards["service_gap"] * _norm(wards["population_cells_proxy"])).round(3)

    rows = (
        pd.DataFrame(wards.drop(columns="geometry"))[OUTPUT_COLUMNS]
        .sort_values("service_priority", ascending=False)
        .to_dict(orient="records")
    )
    writer.write_rows(rows)
    return WardServiceAccessResult(rows=rows)


def _add_builtup_area(wards: gpd.GeoDataFrame, builtup: gpd.GeoDataFrame | None, crs_metric: str) -> None:
    if builtup is None:
        wards["builtup_km2"] = 0.0
        return
    builtup = builtup.to_crs(crs_metric)
    builtup["geometry"] = builtup.geometry.buffer(0)
    centroids = builtup.copy()
    centroids["geometry"] = builtup.geometry.centroid
    centroids["area"] = builtup.geometry.area
    joined = gpd.sjoin(
        centroids[["area", "geometry"]],
        wards.reset_index()[["index", "geometry"]],
        predicate="within",
        how="inner",
    )
    area = joined.groupby("index")["area"].sum() / 1e6
    wards["builtup_km2"] = wards.index.map(area).fillna(0.0).round(2)


def _add_population_proxy(wards: gpd.GeoDataFrame, population: gpd.GeoDataFrame | None, crs_metric: str) -> None:
    if population is None:
        wards["population_cells_proxy"] = 1
        return
    population = population.to_crs(crs_metric)
    centroids = population.copy()
    centroids["geometry"] = population.geometry.centroid
    joined = gpd.sjoin(
        centroids[["geometry"]],
        wards.reset_index()[["index", "geometry"]],
        predicate="within",
        how="inner",
    )
    wards["population_cells_proxy"] = wards.index.map(joined.groupby("index").size()).fillna(0).astype(int)


def _count_in_wards(wards: gpd.GeoDataFrame, points: gpd.GeoDataFrame, column: str) -> None:
    if len(points) == 0:
        wards[column] = 0
        return
    joined = gpd.sjoin(points, wards.reset_index()[["index", "geometry"]], predicate="within", how="inner")
    counts = joined.groupby("index").size()
    wards[column] = wards.index.map(counts).fillna(0).astype(int)


def _norm(series: pd.Series) -> pd.Series:
    series = series.astype(float).fillna(0)
    span = series.max() - series.min()
    return (series - series.min()) / span if span > 0 else series * 0.0


def _empty_points() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(geometry=[], crs=4326)
