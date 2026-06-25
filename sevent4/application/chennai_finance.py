"""Application service for the Chennai GCC finance layer."""
from __future__ import annotations

from sevent4.domain.chennai_finance import (
    build_budget_summary,
    build_zone_capex,
    build_zone_finance_feature_collection,
    finance_resource_jobs,
    finance_sources_record,
)


def acquire_finance_resources(store) -> list[dict]:
    resources: list[dict] = []
    for job in finance_resource_jobs(store.read_catalogue()):
        record = dict(job["record"])
        try:
            record["bytes"] = store.fetch_finance_resource(job["filename"], job["url"])
            record["status"] = "ok"
        except Exception as exc:  # noqa: BLE001
            record["bytes"] = 0
            record["status"] = f"error: {type(exc).__name__}"
        resources.append(record)
    return resources


def build_finance_layer(store) -> dict[str, object]:
    resources = acquire_finance_resources(store)
    ok_resources = [resource for resource in resources if resource["status"] == "ok"]
    resource_tables = store.read_finance_tables(ok_resources)
    zones = build_zone_capex(resource_tables)
    feature_collection = build_zone_finance_feature_collection(store.read_zone_features(), zones)
    store.write_zone_finance_layer(feature_collection)

    budget = build_budget_summary(resource_tables)
    if budget:
        store.write_budget_summary(budget)

    sources = finance_sources_record()
    store.write_finance_sources(sources)
    features = feature_collection["features"]
    total_capex = sum(feature["properties"]["capex_lakh"] for feature in features)
    state_grant = sum(feature["properties"]["state_grant_lakh"] for feature in features)
    return {
        "resources": len(ok_resources),
        "zones": len(features),
        "capex_lakh": total_capex,
        "state_grant_pct": round(state_grant / total_capex * 100) if total_capex else None,
        "budget_written": bool(budget),
    }
