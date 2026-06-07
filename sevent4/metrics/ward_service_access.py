from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from sevent4.city_dataset import CityDataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute ward-level civic service access metrics.")
    parser.add_argument("--city", required=True, help="Path to city.yaml")
    parser.add_argument("--out", help="Output CSV path; defaults to outputs_dir/ward_service_access.csv")
    args = parser.parse_args()
    city = CityDataset.from_yaml(args.city)
    out = Path(args.out) if args.out else city.outputs_dir / "ward_service_access.csv"
    build_metrics(city, out)


def build_metrics(city: CityDataset, out: Path) -> None:
    wards = gpd.read_file(city.source_dir / "amc" / "Wards.geojson")[["Name", "geometry"]].copy()
    wards = wards.to_crs(city.crs_metric)
    wards["ward_area_km2"] = wards.geometry.area / 1e6

    sources = {
        "libraries": _amc_libraries(city),
        "schools": _points_json(city.source_dir / "services" / "schools.json"),
        "health": _points_json(city.source_dir / "services" / "health.json"),
        "toilets": _points_json(city.source_dir / "services" / "toilets.json"),
        "police": _points_json(city.source_dir / "services" / "police.json"),
        "fire": _points_json(city.source_dir / "services" / "emergency.json"),
        "universities": _service_group(city.source_dir / "services" / "civic.json", ["university", "college"]),
        "gtfs_stops": _points_json(city.source_dir / "transit" / "gtfs_stops.json"),
    }
    for column, points in sources.items():
        _count_in_wards(wards, points.to_crs(city.crs_metric), column)

    builtup_path = city.source_dir / "cities" / "Builtup" / "2000_2014_Ahmedabad_Builtup" / "2000_2014_Ahmedabad_Builtup.geojson"
    if builtup_path.exists():
        builtup = gpd.read_file(builtup_path).to_crs(city.crs_metric)
        builtup["geometry"] = builtup.geometry.buffer(0)
        centroids = builtup.copy()
        centroids["geometry"] = builtup.geometry.centroid
        centroids["area"] = builtup.geometry.area
        joined = gpd.sjoin(centroids[["area", "geometry"]], wards.reset_index()[["index", "geometry"]], predicate="within", how="inner")
        area = joined.groupby("index")["area"].sum() / 1e6
        wards["builtup_km2"] = wards.index.map(area).fillna(0.0).round(2)
    else:
        wards["builtup_km2"] = 0.0

    population_path = city.source_dir / "cities" / "Population" / "2000_2015_Ahmedabad_Population.geojson"
    if population_path.exists():
        population = gpd.read_file(population_path).to_crs(city.crs_metric)
        centroids = population.copy()
        centroids["geometry"] = population.geometry.centroid
        joined = gpd.sjoin(centroids[["geometry"]], wards.reset_index()[["index", "geometry"]], predicate="within", how="inner")
        wards["population_cells_proxy"] = wards.index.map(joined.groupby("index").size()).fillna(0).astype(int)
    else:
        wards["population_cells_proxy"] = 1

    population_proxy = wards["population_cells_proxy"].clip(lower=1)
    access_parts = []
    for service in ["libraries", "schools", "health", "gtfs_stops"]:
        per_proxy = wards[service] / population_proxy
        access_parts.append(_norm(per_proxy))
    access = sum(access_parts) / len(access_parts)
    wards["service_access"] = access.round(3)
    wards["service_gap"] = (1 - access).round(3)
    wards["service_priority"] = (wards["service_gap"] * _norm(wards["population_cells_proxy"])).round(3)

    columns = [
        "Name", "ward_area_km2", "builtup_km2", "population_cells_proxy",
        "libraries", "schools", "health", "toilets", "police", "fire", "universities", "gtfs_stops",
        "service_access", "service_gap", "service_priority",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(wards.drop(columns="geometry"))[columns].sort_values("service_priority", ascending=False).to_csv(out, index=False)
    print(f"wrote {out} ({len(wards)} wards)")


def _points_json(path: Path) -> gpd.GeoDataFrame:
    rows = json.loads(path.read_text()) if path.exists() else []
    points = []
    for row in rows:
        try:
            points.append(Point(float(row["lon"]), float(row["lat"])))
        except (KeyError, TypeError, ValueError):
            continue
    return gpd.GeoDataFrame(geometry=points, crs=4326)


def _service_group(path: Path, keys: list[str]) -> gpd.GeoDataFrame:
    data = json.loads(path.read_text()) if path.exists() else {}
    rows = []
    for key in keys:
        rows.extend(data.get(key, []))
    return _rows_to_points(rows)


def _amc_libraries(city: CityDataset) -> gpd.GeoDataFrame:
    path = city.source_dir / "amc" / "Library.geojson"
    return gpd.read_file(path).to_crs(4326)


def _rows_to_points(rows: list[dict]) -> gpd.GeoDataFrame:
    points = []
    for row in rows:
        try:
            points.append(Point(float(row["lon"]), float(row["lat"])))
        except (KeyError, TypeError, ValueError):
            continue
    return gpd.GeoDataFrame(geometry=points, crs=4326)


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


if __name__ == "__main__":
    main()
