"""Application services for Bengaluru OpenCity acquisition recipes."""
from __future__ import annotations

from sevent4.domain.bengaluru_opencity import (
    BOUNDARY_SPINE,
    CURATED_JURISDICTION_LAYERS,
    JURISDICTION_SLUGS,
    boundary_provenance_record,
    finance_dataset_from_package,
    finance_download_jobs,
    jurisdiction_resource_jobs,
)


def acquire_finance_resources(store, slugs: list[str] | None = None) -> dict[str, object]:
    if not store.archive_exists():
        raise FileNotFoundError("OpenCity archive root is not present")
    catalogue = store.read_catalogue()
    jobs, missing = finance_download_jobs(catalogue, slugs)
    if missing and hasattr(store, "package_show"):
        datasets = list(catalogue.get("datasets", []))
        for slug in missing:
            dataset = finance_dataset_from_package(store.package_show(slug), slug)
            if dataset:
                datasets.append(dataset)
        jobs, missing = finance_download_jobs({**catalogue, "datasets": datasets}, slugs)
    manifest: list[dict] = []
    done = 0
    errors: list[tuple[str, str]] = []
    for job in jobs:
        record = dict(job["record"])
        try:
            size = store.fetch_finance_resource(job["slug"], job["filename"], job["url"])
            record["bytes"] = size
            record["status"] = "ok"
            done += 1
        except Exception as exc:  # noqa: BLE001
            record["bytes"] = 0
            record["status"] = f"error: {type(exc).__name__}"
            errors.append((record["file"], str(exc)))
        manifest.append(record)
    store.write_finance_manifest(manifest)
    return {"jobs": len(jobs), "done": done, "errors": errors, "missing": missing}


def acquire_boundary_spine(store, spine: dict[str, dict] | None = None) -> dict[str, object]:
    selected = spine or BOUNDARY_SPINE
    provenance: list[dict[str, object]] = []
    total_features = 0
    for layer_id, spec in selected.items():
        size = store.fetch_boundary_resource(layer_id, spec["resource"])
        converted = store.convert_boundary_resource(layer_id, spec["target"])
        total_features += int(converted["features"])
        provenance.append(boundary_provenance_record(layer_id, spec, size, converted))
    store.write_boundary_sources(provenance)
    store.write_boundary_credits(provenance)
    return {"layers": len(provenance), "features": total_features, "provenance": provenance}


def acquire_jurisdiction_resources(store, slugs: list[str] | None = None) -> dict[str, object]:
    selected = slugs or JURISDICTION_SLUGS
    manifest: list[dict] = []
    skipped: list[str] = []
    for slug in selected:
        package = store.package_show(slug)
        if not package or not package.get("success"):
            skipped.append(slug)
            continue
        for job in jurisdiction_resource_jobs(package, slug):
            record = dict(job["record"])
            result = store.fetch_jurisdiction_resource(job["slug"], job["filename"], job["url"])
            record.update(result)
            manifest.append(record)
    ok = [row for row in manifest if row["status"] == "ok"]
    summary = {
        "source": "OpenCity (data.opencity.in) CKAN API",
        "downloaded": len(ok),
        "failed": len(manifest) - len(ok),
        "total_bytes": sum(int(row["bytes"]) for row in ok),
        "resources": manifest,
    }
    store.write_jurisdiction_manifest(summary)
    return {"downloaded": len(ok), "failed": summary["failed"], "skipped": skipped, "resources": manifest}


def build_jurisdiction_layers(store, curated: list[dict] | None = None) -> dict[str, object]:
    selected = curated or CURATED_JURISDICTION_LAYERS
    rows: list[dict] = []
    for spec in selected:
        record = {
            "id": spec["id"],
            "file": f"{spec['id']}.geojson",
            "source_file": spec["file"],
            "publisher": spec["pub"],
            "dataset_slug": spec["slug"],
        }
        if not store.source_exists(spec):
            record["status"] = "missing_raw"
            rows.append(record)
            continue
        try:
            record.update(store.build_curated_layer(spec))
        except Exception as exc:  # noqa: BLE001
            record["status"] = f"error: {type(exc).__name__}: {exc}"
        rows.append(record)
    store.write_jurisdiction_build_report(rows)
    return {"ok": sum(1 for row in rows if row.get("status") == "ok"), "total": len(rows), "layers": rows}
