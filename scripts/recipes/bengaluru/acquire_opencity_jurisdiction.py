#!/usr/bin/env python3
"""Acquire Bengaluru jurisdiction + utility geo resources from OpenCity.

Pulls KML/KMZ/GEOJSON for the authority-and-utility datasets named in
docsx/ready-city-geo-layer-queue.md that carry the unelected-city thesis: BDA,
GBA-2025, BWSSB, traffic police all cut Bengaluru differently than BBMP wards.
Saves to data/cities/bengaluru/source/opencity/_raw/<slug>/ with a provenance
manifest (sha256 + bytes + OpenCity URL + license).

The 92-file urban revenue maps, 17-file tree census, and cadastral KMZ bulk are
intentionally not pulled here (large; lower thesis value). Per-dataset cap guards
against runaway downloads.

    python3 scripts/recipes/bengaluru/acquire_opencity_jurisdiction.py
"""
from __future__ import annotations
import hashlib, json, re
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/cities/bengaluru/source/opencity/_raw"  # gitignored
UA = {"User-Agent": "sevent4-atlas-catalogue/1.0 (open-data harvest)"}
API = "https://data.opencity.in/api/3/action/package_show?id="
KEEP = {"KML", "KMZ", "GEOJSON"}
PER_DATASET_CAP = 40

SLUGS = [
    "bda-jurisdiction-and-boundary",
    "greater-bengaluru-authority-corporations-delimitation-2025",
    "bwssb-boundary-maps",
    "bwssb-sewerage-line-maps-for-bengaluru",
    "bengaluru-traffic-police-jurisdictions",
    "bbmp-solid-waste-management-data",
    "bengaluru-zone-wise-streetlights",
    "bus-stops-and-routes-map-by-ward",
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


def get_json(url: str) -> dict | None:
    """package_show with retry — the metadata call must not abort the whole run."""
    for attempt in range(3):
        try:
            return requests.get(url, headers=UA, timeout=90).json()
        except Exception:
            if attempt == 2:
                return None
    return None


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    for slug in SLUGS:
        meta = get_json(API + slug)
        if not meta or not meta.get("success"):
            print(f"  SKIP {slug}: package_show failed/timed out")
            continue
        res = meta["result"]
        org = (res.get("organization") or {}).get("title", "?")
        lic = res.get("license_title", "?")
        ds_url = f"https://data.opencity.in/dataset/{slug}"
        geo = [r for r in res.get("resources", []) if (r.get("format") or "").upper() in KEEP]
        geo = geo[:PER_DATASET_CAP]
        print(f"\n{slug}: {len(geo)} geo resources | {org}")
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
            print(f"   [{status:>5}] {size/1024:8.1f} KB  {fname}")

    ok = [m for m in manifest if m["status"] == "ok"]
    (RAW / "_manifest.json").write_text(json.dumps({
        "retrieved": date.today().isoformat(),
        "source": "OpenCity (data.opencity.in) CKAN API",
        "downloaded": len(ok), "failed": len(manifest) - len(ok),
        "total_bytes": sum(m["bytes"] for m in ok),
        "resources": manifest,
    }, indent=2), encoding="utf-8")
    print(f"\nBengaluru OpenCity jurisdiction: {len(ok)}/{len(manifest)} resources, "
          f"{sum(m['bytes'] for m in ok)/1e6:.1f} MB -> {RAW}")


if __name__ == "__main__":
    main()
