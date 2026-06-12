#!/usr/bin/env python3
"""Pass-1 finance acquisition for Bengaluru (the locked scope: budget + the two work-order ledgers).

Reads the local OpenCity catalogue, downloads every resource of the named finance datasets to the
EXTERNAL volume (raw archive), and writes a provenance manifest. Processing into the ward-spend
layer is done by build_finance_layer.py (kept separate so re-processing doesn't re-download).

Raw lands under $OPENCITY_ARCHIVE/bengaluru/raw/<slug>/ (set OPENCITY_ARCHIVE to the
external archive root; defaults to the in-repo gitignored data/sources/opencity).
Provenance:    same dir / _manifest.json  (+ a copy of the credit line)

Run:  OPENCITY_ARCHIVE=<archive-root> .venv/bin/python scripts/recipes/bengaluru/acquire_finance.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[3]
CATALOGUE = ROOT / "data" / "sources" / "opencity" / "_catalogue" / "opencity_catalogue.json"
ARCHIVE = Path(os.environ.get("OPENCITY_ARCHIVE", str(ROOT / "data" / "sources" / "opencity")))
EXT = ARCHIVE / "bengaluru" / "raw"
UA = {"User-Agent": "sevent4-atlas/1.0 (74th-amendment atlas; solanki.aakash@gmail.com)"}

# Locked pass-1 finance scope (+ MLA-LAD as a small who-pays/who-decides bonus).
SLUGS = [
    "bbmp-budget",                       # CSV + PDF city budget series
    "bbmp-budget-2023-24",               # XLSX detail
    "bbmp-budget-2024-25",
    "bbmp-budget-2025-26",
    "bbmp-work-orders-by-ward-2013-2022",  # 198 CSV, one per ward — the ward-spend ledger
    "bbmp-work-orders-and-bill-payment",   # 87 CSV, by division — the bill/payment trail
    "bengaluru-mla-local-area-development-funds",  # 28 CSV
]
# only fetch machine-readable here; PDFs of the budget books are a separate (optional) pull
KEEP = {"CSV", "XLSX", "XLS", "JSON", "GEOJSON"}


def safe(name: str, fallback: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", (name or "").strip())[:90].strip("_")
    return s or fallback


def fetch(url: str, dest: Path) -> int:
    req = Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urlopen(req, timeout=120) as r:
                data = r.read()
            dest.write_bytes(data)
            return len(data)
        except Exception:
            if attempt == 2:
                raise
    return 0


def main() -> None:
    if not ARCHIVE.exists():
        sys.exit(f"archive root {ARCHIVE} not present — mount it or set OPENCITY_ARCHIVE")
    cat = json.load(open(CATALOGUE))
    by = {d["name"]: d for d in cat["datasets"]}

    jobs = []          # (slug, dest_path, url, resource_meta)
    manifest = []
    for slug in SLUGS:
        d = by.get(slug)
        if not d:
            print(f"!! dataset not in catalogue: {slug}", file=sys.stderr)
            continue
        ddir = EXT / slug
        ddir.mkdir(parents=True, exist_ok=True)
        kept = 0
        for i, r in enumerate(d["resources"]):
            if r["format"] not in KEEP:
                continue
            fname = safe(r.get("name") or "", f"res_{i}") + "." + r["format"].lower()
            dest = ddir / fname
            jobs.append((slug, dest, r["url"]))
            manifest.append({
                "slug": slug, "dataset_title": d["title"], "publisher_org": d["organization"],
                "opencity_dataset": d["url"], "resource_name": r.get("name"),
                "resource_url": r["url"], "format": r["format"], "file": str(dest.relative_to(EXT)),
                "last_modified": r.get("last_modified"),
            })
            kept += 1
        print(f"  {slug}: queued {kept} {KEEP & {r['format'] for r in d['resources']}} files")

    print(f"\n[acquire] downloading {len(jobs)} files to {EXT} ...", file=sys.stderr)
    done = 0
    errors = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(fetch, url, dest): (slug, dest) for slug, dest, url in jobs}
        for fut in as_completed(futs):
            slug, dest = futs[fut]
            try:
                fut.result()
                done += 1
                if done % 25 == 0:
                    print(f"    {done}/{len(jobs)}", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                errors.append((str(dest), str(e)))

    (EXT / "_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"[acquire] done: {done}/{len(jobs)} files; {len(errors)} errors", file=sys.stderr)
    for d, e in errors[:10]:
        print(f"    ERR {d}: {e}", file=sys.stderr)
    print(f"[acquire] provenance -> {EXT/'_manifest.json'}", file=sys.stderr)


if __name__ == "__main__":
    main()
