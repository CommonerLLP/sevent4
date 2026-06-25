#!/usr/bin/env python3
"""Acquire Bengaluru finance resources from the local OpenCity catalogue.

Thin CLI wrapper: acquisition planning lives in
sevent4.domain.bengaluru_opencity, dispatch in
sevent4.application.bengaluru_opencity, and network/filesystem IO in
sevent4.adapters.bengaluru_opencity_filesystem.
"""
from __future__ import annotations

import sevent4.adapters.bengaluru_opencity_filesystem as opencity_store
from sevent4.application.bengaluru_opencity import acquire_finance_resources
from sevent4.domain.bengaluru_opencity import FINANCE_KEEP, FINANCE_SLUGS, safe_filename  # noqa: F401


def main() -> None:
    try:
        result = acquire_finance_resources(opencity_store)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"[acquire] done: {result['done']}/{result['jobs']} files; {len(result['errors'])} errors")
    for path, error in result["errors"][:10]:
        print(f"    ERR {path}: {error}")
    if result["missing"]:
        print(f"    missing datasets: {result['missing']}")
    print(f"[acquire] provenance -> {opencity_store.FINANCE_RAW / '_manifest.json'}")


if __name__ == "__main__":
    main()
