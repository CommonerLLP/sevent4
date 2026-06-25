#!/usr/bin/env python3
"""Pull Delhi's structured OpenCity data into the gitignored source archive.

Reads the Delhi shortlist and downloads every machine-readable resource
(CSV/GEOJSON/KML/XLSX/JSON) to data/cities/delhi/source/opencity/_raw/<dataset>/,
writing a provenance manifest with sha256 + sizes.

Thin CLI wrapper: row filtering, slug/manifest shaping live in
sevent4.domain.delhi_acquire / sevent4.application.delhi_acquire; HTTP + CSV/JSON
IO in the delhi-acquire adapter.

    .venv/bin/python scripts/recipes/delhi/acquire_opencity.py            # all structured
    .venv/bin/python scripts/recipes/delhi/acquire_opencity.py --limit 20 # smoke test
"""
from __future__ import annotations

import argparse
from pathlib import Path

from sevent4.adapters.delhi_acquire_filesystem import fetch_with_sha, read_csv_rows, write_json
from sevent4.application.delhi_acquire import acquire_opencity
from sevent4.domain.delhi_acquire import OPENCITY_KEEP

ROOT = Path(__file__).resolve().parents[3]
SHORTLIST = ROOT / "data/cities/delhi/source/opencity/delhi_opencity_atlas_shortlist.csv"
RAW = ROOT / "data/cities/delhi/source/opencity/_raw"  # _raw/ is gitignored


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="cap resources (0 = all)")
    args = ap.parse_args()

    rows = read_csv_rows(SHORTLIST)
    RAW.mkdir(parents=True, exist_ok=True)

    def dest_fn(ds_slug: str, filename: str):
        dest = RAW / ds_slug / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        return dest, str(dest.relative_to(ROOT))

    manifest, skipped = acquire_opencity(rows, fetch_with_sha, dest_fn, limit=args.limit)
    write_json(manifest, RAW / "_manifest.json", indent=2)

    ok, total = manifest["downloaded"], manifest["downloaded"] + manifest["failed"]
    mb = manifest["total_bytes"] / 1e6
    print(f"delhi OpenCity: {ok}/{total} resources, {mb:.1f} MB -> {RAW}")
    print(f"  formats kept: {sorted(OPENCITY_KEEP)}; NOT auto-pulled (need parsing): {skipped}")
    if manifest["failed"]:
        for m in manifest["resources"]:
            if m["status"] != "ok":
                print(f"  FAILED: {m['dataset'][:40]} [{m['format']}] {m['status']}")


if __name__ == "__main__":
    main()
