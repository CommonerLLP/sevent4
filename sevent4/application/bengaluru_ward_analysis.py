"""Application service for Bengaluru four-axis ward analysis."""
from __future__ import annotations

from sevent4.domain.bengaluru_ward_analysis import (
    build_ward_analysis_feature_collection,
    correlation_rows,
    patch_ward_analysis_manifest,
)


def reconcile_ward_analysis(store) -> dict:
    rows = store.ward_analysis_rows()
    feature_collection, metrics = build_ward_analysis_feature_collection(rows)
    store.write_ward_analysis(feature_collection)
    store.write_layer_manifest(patch_ward_analysis_manifest(store.read_layer_manifest()))
    correlations = correlation_rows(metrics)
    return {
        "wards": len(feature_collection["features"]),
        "spend_joined": sum(1 for row in metrics if row[2] is not None),
        "heat_transferred": sum(1 for row in metrics if row[4] is not None),
        "correlations": correlations,
    }
