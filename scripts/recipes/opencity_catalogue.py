#!/usr/bin/env python3
"""Catalogue the full data.opencity.in CKAN portal — no downloads.

Enumerates every dataset via the CKAN Action API and writes
opencity_catalogue.json (machine-readable) + opencity_catalogue.md (human index).

Thin CLI wrapper: catalogue shaping + markdown live in
sevent4.domain.opencity_catalogue / sevent4.application.comparators; the CKAN API
+ JSON/MD writes in the comparators adapter. (The previous version of this script
was corrupted with missing-parens method calls; repaired in the refactor.)

  .venv/bin/python scripts/recipes/opencity_catalogue.py --out data/sources/opencity/_catalogue
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.comparators_filesystem import fetch_all_packages, write_json, write_text
from sevent4.application.comparators import build_opencity_catalogue
from sevent4.domain.opencity_catalogue import human_bytes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output directory for catalogue files")
    ap.add_argument("--page-size", type=int, default=200)
    args = ap.parse_args()

    pkgs = fetch_all_packages(page_size=args.page_size)
    cat, md = build_opencity_catalogue(pkgs)

    out = Path(args.out)
    json_path = out / "opencity_catalogue.json"
    md_path = out / "opencity_catalogue.md"
    write_json(cat, json_path, indent=2)
    write_text(md, md_path)

    print(f"[catalogue] wrote {json_path}", file=sys.stderr)
    print(f"[catalogue] wrote {md_path}", file=sys.stderr)
    print(f"[catalogue] {cat['dataset_count']} datasets, {cat['resource_count']} resources, "
          f"{human_bytes(cat['known_bytes'])} known size", file=sys.stderr)


if __name__ == "__main__":
    main()
