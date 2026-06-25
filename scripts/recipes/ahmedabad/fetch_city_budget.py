#!/usr/bin/env python3
"""Fetch city finance-book PDFs from public municipal sources. Thin CLI wrapper:
link discovery + manifest shaping live in the budget application/domain layers,
HTTP + file IO in the budget adapters.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.budget_filesystem import FinanceBookArchive, finance_paths
from sevent4.adapters.budget_http import UrllibFinanceBookSource
from sevent4.application.budget import (
    budget_book_filename,
    discover_finance_links,
    finance_manifest,
    finance_row,
)
from sevent4.domain.budget import CITY_FINANCE_PAGES

REPO = Path(__file__).resolve().parents[3]
DEFAULT_CITY = "ahmedabad"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch city finance-book PDFs from public municipal sources.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Ahmedabad is implemented first.")
    parser.add_argument("--kind", default="budget", choices=["budget", "balance-sheet", "all"], help="Finance-book kind.")
    parser.add_argument("--page-url", help="Override source page URL. Only valid with one --kind.")
    parser.add_argument("--out-dir", help="PDF output directory. Only recommended with one --kind.")
    parser.add_argument("--manifest", help="JSON manifest output path. Only recommended with one --kind.")
    parser.add_argument("--dry-run", action="store_true", help="List discovered PDFs without downloading.")
    args = parser.parse_args()

    city = args.city.lower()
    configs = CITY_FINANCE_PAGES.get(city)
    if not configs:
        sys.exit(
            f"No finance-book fetch adapter for city={city!r}. "
            "Put PDFs under data/cities/<city>/source/budget/pdfs/ or add an adapter."
        )

    if args.kind == "all":
        if args.page_url:
            sys.exit("--page-url is only valid when --kind is budget or balance-sheet")
        kinds = list(configs)
    else:
        kinds = [args.kind]

    source = UrllibFinanceBookSource()
    all_rows = []
    for kind in kinds:
        config = configs.get(kind)
        if not config:
            sys.exit(f"No {kind} fetch adapter for city={city!r}")

        page_url = args.page_url or str(config["url"])
        source_dir = str(config["dir"])
        default_pdf_dir, default_manifest = finance_paths(REPO, city, source_dir)
        pdf_dir = Path(args.out_dir) if args.out_dir and len(kinds) == 1 else default_pdf_dir
        manifest_path = Path(args.manifest) if args.manifest and len(kinds) == 1 else default_manifest
        archive = FinanceBookArchive(REPO, pdf_dir, manifest_path)

        html = source.fetch_text(page_url)
        links = discover_finance_links(html, kind, page_url, tuple(config["keywords"]))
        if not links:
            sys.exit(f"No {kind} links discovered at {page_url}")

        if not args.dry_run:
            archive.ensure_dirs()

        rows = []
        seen_names: set[str] = set()
        for link in links:
            filename = budget_book_filename(city, link, seen_names)
            out_path = archive.pdf_path(filename)
            row = finance_row(city, kind, link, archive.relpath(out_path))
            if args.dry_run:
                print(f"{kind}\t{link.year}\t{link.label}\t{link.url}")
            else:
                archive.write_pdf(out_path, source.fetch_bytes(link.url))
                print(f"wrote {out_path}")
            rows.append(row)
            all_rows.append(row)

        if not args.dry_run:
            archive.write_manifest(finance_manifest(city, kind, page_url, rows))
            print(f"wrote {manifest_path}")

    if len(kinds) > 1:
        print(f"discovered {len(all_rows)} finance-book links across {len(kinds)} source pages")


if __name__ == "__main__":
    main()
