"""Application service for the Delhi Public Library extraction recipe.

The store owns filesystem reads/writes. This layer owns the publication order
and table derivations from parsed source rows.
"""
from __future__ import annotations

from pathlib import Path

from sevent4.domain.delhi_dpl_extract import (
    ANNUAL_FIELDS,
    DPL_LOCATION_FIELDS,
    GEOCODE_CACHE_FIELDS,
    MANIFEST_FIELDS,
    METRICS_LONG_FIELDS,
    TIME_SERIES_FIELDS,
    geocode_cache_rows,
    latest_long_metrics,
    one_year,
    online_annual_time_series,
    ten_year_time_series,
)

SOURCE_MANIFEST = "selected_finance_operations_links.tsv"


def build_dpl_library(store, source_dir: Path, out_dir: Path, geocode_dir: Path) -> dict[str, object]:
    source_dir = Path(source_dir)
    out_dir = Path(out_dir)
    geocode_dir = Path(geocode_dir)

    manifest = store.read_tsv(source_dir / SOURCE_MANIFEST)
    manifest_rows = store.build_manifest_rows(source_dir, manifest)
    store.write_csv(out_dir / "dpl_fetch_manifest.csv", manifest_rows, MANIFEST_FIELDS)

    source_by_stem = source_urls_by_stem(manifest)
    location_rows = store.extract_dpl_locations(source_dir / "html", source_by_stem)
    store.write_csv(out_dir / "dpl_library_locations.csv", location_rows, DPL_LOCATION_FIELDS)

    cache_rows = geocode_cache_rows(location_rows)
    store.write_csv(geocode_dir / "geocode_cache.csv", cache_rows, GEOCODE_CACHE_FIELDS)

    annual_rows = store.extract_annual_rows(source_dir / "text", source_by_stem)
    store.write_csv(out_dir / "dpl_annual_metrics.csv", annual_rows, ANNUAL_FIELDS)

    population = store.primary_delhi_population()
    ten_year_rows = ten_year_time_series(annual_rows, population)
    online_rows = online_annual_time_series(annual_rows, population)
    store.write_csv(out_dir / "dpl_ten_year_time_series.csv", ten_year_rows, TIME_SERIES_FIELDS)
    store.write_csv(out_dir / "dpl_online_annual_time_series.csv", online_rows, TIME_SERIES_FIELDS)

    long_rows = latest_long_metrics(one_year(annual_rows, "2023-24"))
    store.write_csv(out_dir / "dpl_metrics_long.csv", long_rows, METRICS_LONG_FIELDS)

    return {
        "manifest_rows": len(manifest_rows),
        "annual_rows": len(annual_rows),
        "ten_year_rows": len(ten_year_rows),
        "online_rows": len(online_rows),
        "long_rows": len(long_rows),
        "location_rows": len(location_rows),
        "geocode_cache_rows": len(cache_rows),
        "out_dir": out_dir,
        "geocode_dir": geocode_dir,
    }


def source_urls_by_stem(manifest: list[dict[str, str]]) -> dict[str, str]:
    return {
        Path(row["local_path"]).stem: row["url"]
        for row in manifest
        if row.get("url") and row.get("local_path")
    }
