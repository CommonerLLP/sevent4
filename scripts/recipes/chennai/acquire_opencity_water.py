#!/usr/bin/env python3
"""Acquire Chennai water/flood geo resources from OpenCity into the gitignored archive.

Pulls every machine-readable geo resource (KML/KMZ) for the six GCC/CMWSSB
water-and-flood datasets named in docsx/ready-city-geo-layer-queue.md, saving each
to data/cities/chennai/source/opencity/_raw/<dataset-slug>/ with a provenance
manifest (sha256 + bytes + OpenCity dataset URL + direct resource URL + license).

The ward-level SWD maps are distributed only as per-ward PDF (100+ files, not
machine-readable) and are intentionally skipped; the single consolidated
"Storm Water Drains - SWD - Map 2023" KML is kept.

    python3 scripts/recipes/chennai/acquire_opencity_water.py
"""
from __future__ import annotations
import hashlib, json, re
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/cities/chennai/source/opencity/_raw"  # gitignored
UA = {"User-Agent": "sevent4-atlas-catalogue/1.0 (open-data harvest)"}
API = "https://data.opencity.in/api/3/action/package_show?id="
KEEP = {"KML", "KMZ"}  # geo formats; PDF ward maps + TXT codes skipped here

SLUGS = [
    "chennai-stormwater-drain-swd-maps",
    "chennai-flooding-data",
    "chennai-sewage-pumping-network",
    "chennai-sewerage-collection-system",
    "chennai-water-distribution-stations",
    "cmwssb-administrative-boundaries",
]


def slugify(s: str, fallback: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", (s or "").strip())[:80].strip("_")
    return s or fallback


def fetch(url: str) -> bytes:
    for attempt in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=180)
            r.raise_for_status()
            return r.content
        except Exception:
            if attempt == 2:
                raise
    return b""


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    for slug in SLUGS:
        meta = requests.get(API + slug, headers=UA, timeout=60).json()
        if not meta.get("success"):
            print(f"  SKIP {slug}: package_show failed")
            continue
        res = meta["result"]
        org = (res.get("organization") or {}).get("title", "?")
        lic = res.get("license_title", "?")
        ds_url = f"https://data.opencity.in/dataset/{slug}"
        geo = [r for r in res.get("resources", []) if (r.get("format") or "").upper() in KEEP]
        n_pdf = sum(1 for r in res.get("resources", []) if (r.get("format") or "").upper() == "PDF")
        print(f"\n{slug}: {len(geo)} geo resources ({n_pdf} PDFs skipped) | {org}")
        for i, r in enumerate(geo):
            ext = (r.get("format") or "kml").lower()
            fname = slugify(r.get("name") or r.get("id"), f"r{i}") + f".{ext}"
            dest = RAW / slug / fname
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                blob = fetch(r["url"])
                dest.write_bytes(blob)
                sha, size, status = hashlib.sha256(blob).hexdigest(), len(blob), "ok"
            except Exception as e:
                sha, size, status = "", 0, f"error: {type(e).__name__}"
            manifest.append({
                "dataset_slug": slug, "dataset_url": ds_url, "organization": org,
                "license": lic, "resource_name": r.get("name"), "format": ext.upper(),
                "resource_url": r["url"], "local": str(dest.relative_to(ROOT)),
                "bytes": size, "sha256": sha, "status": status,
            })
            print(f"   [{status:>5}] {size/1024:7.1f} KB  {fname}")

    ok = [m for m in manifest if m["status"] == "ok"]
    (RAW / "_manifest.json").write_text(json.dumps({
        "retrieved": date.today().isoformat(),
        "source": "OpenCity (data.opencity.in) CKAN API",
        "downloaded": len(ok), "failed": len(manifest) - len(ok),
        "total_bytes": sum(m["bytes"] for m in ok),
        "resources": manifest,
    }, indent=2), encoding="utf-8")
    print(f"\nChennai OpenCity water/flood: {len(ok)}/{len(manifest)} resources, "
          f"{sum(m['bytes'] for m in ok)/1e6:.1f} MB -> {RAW}")


if __name__ == "__main__":
    main()
