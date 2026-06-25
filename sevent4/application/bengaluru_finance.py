"""Application services for Bengaluru work-order finance layers."""
from __future__ import annotations

from pathlib import Path

from sevent4.domain.bengaluru_finance import (
    boundary_name_keys,
    build_cumulative_geojson,
    build_finance_tables,
    build_yearly_geojson,
    build_yearly_table,
    matched_ledger_count,
    patch_finance_manifest,
)


def build_yearly_table_from_store(store, raw_dir: Path, min_year: int = 2013, max_year: int = 2022) -> list[dict]:
    return build_yearly_table(store.read_workorder_file_rows(raw_dir), min_year, max_year)


def build_finance_layer(store, raw_dir: Path, out_dir: Path, boundary_path: Path) -> dict:
    file_rows = store.read_workorder_file_rows(raw_dir)
    table, yearly = build_finance_tables(file_rows)
    store.write_json(Path(out_dir) / "ward_workorders.json", table)
    store.write_json(Path(out_dir) / "ward_workorders_yearly.json", yearly)

    boundary = store.read_json(boundary_path) if store.exists(boundary_path) else {"features": []}
    return {
        "ledger_rows": len(table),
        "yearly_rows": len(yearly),
        "works": sum(row["work_count"] for row in table),
        "total_nett_cr": sum(row["total_nett_cr"] for row in table),
        "boundary_names": len(boundary_name_keys(boundary)),
        "matched": matched_ledger_count(table, boundary),
        "top_rows": table[:5],
    }


def wire_finance_layer(store, city_dir: Path, layers_dir: Path) -> dict:
    city_dir = Path(city_dir)
    layers_dir = Path(layers_dir)
    ledger_records = store.read_json(city_dir / "source" / "finance" / "ward_workorders.json")
    boundary_path = city_dir / "source" / "boundaries" / "wards_bbmp198.geojson"
    if store.exists(boundary_path):
        boundary = store.read_json(boundary_path)
    else:
        boundary = store.read_json(layers_dir / "ward_workorders.geojson")
    yearly_records = store.read_json(city_dir / "source" / "finance" / "ward_workorders_yearly.json")
    years = sorted({int(row["year"]) for row in yearly_records})

    cumulative, matched = build_cumulative_geojson(boundary, ledger_records)
    store.write_json(layers_dir / "ward_workorders.geojson", cumulative)
    yearly = build_yearly_geojson(boundary, yearly_records, years)
    store.write_json(layers_dir / "ward_workorders_yearly.geojson", yearly)

    manifest_path = layers_dir / "layer_manifest.json"
    manifest = patch_finance_manifest(store.read_json(manifest_path), years)
    store.write_json(manifest_path, manifest, indent=2)

    return {
        "matched": matched,
        "features": len(cumulative["features"]),
        "yearly_features": len(yearly["features"]),
        "years": years,
    }
