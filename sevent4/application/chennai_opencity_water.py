"""Application services for Chennai OpenCity water/flood recipes."""
from __future__ import annotations

from sevent4.domain.chennai_opencity_water import CURATED_WATER_LAYERS, SLUGS, water_resource_jobs


def acquire_water_resources(store, slugs: list[str] | None = None) -> dict[str, object]:
    selected = slugs or SLUGS
    manifest: list[dict] = []
    skipped: list[str] = []
    for slug in selected:
        package = store.package_show(slug)
        if not package or not package.get("success"):
            skipped.append(slug)
            continue
        for job in water_resource_jobs(package, slug):
            record = dict(job["record"])
            result = store.fetch_water_resource(job["slug"], job["filename"], job["url"])
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
    store.write_water_manifest(summary)
    return {"downloaded": len(ok), "failed": summary["failed"], "skipped": skipped, "resources": manifest}


def build_water_layers(store, curated: list[dict] | None = None) -> dict[str, object]:
    selected = curated or CURATED_WATER_LAYERS
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
    store.write_water_build_report(rows)
    return {"ok": sum(1 for row in rows if row.get("status") == "ok"), "total": len(rows), "layers": rows}
