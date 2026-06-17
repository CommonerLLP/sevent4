#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.recipes.libraries.source_archive import (
    STAFFING_FIELDS,
    archive_source_pdf,
    parse_dpl_staffing_text,
    read_csv,
    write_csv,
)


DEFAULT_EXTERNAL_ROOT = REPO / "data" / "sources" / "library_archives"
DPL_SOURCE = REPO / "data" / "cities" / "delhi" / "source" / "libraries" / "dpl_annual_metrics.csv"
MJ_SOURCE = REPO / "data" / "cities" / "ahmedabad" / "source" / "libraries" / "mj_library_pdf_index.csv"
DPL_ARCHIVE_DIR = DEFAULT_EXTERNAL_ROOT / "delhi" / "libraries" / "dpl" / "annual_reports"
MJ_ARCHIVE_DIR = DEFAULT_EXTERNAL_ROOT / "ahmedabad" / "libraries" / "mj_library" / "source_pdfs"
DPL_MANIFEST = REPO / "data" / "cities" / "delhi" / "source" / "libraries" / "dpl_annual_report_archive_manifest.csv"
DPL_STAFFING = REPO / "data" / "cities" / "delhi" / "source" / "libraries" / "dpl_staffing_time_series.csv"
MJ_MANIFEST = REPO / "data" / "cities" / "ahmedabad" / "source" / "libraries" / "mj_library_source_archive_manifest.csv"

ARCHIVE_FIELDS = [
    "year",
    "source_url",
    "archive_dir",
    "pdf_filename",
    "pdf_size_bytes",
    "pdf_sha256",
    "txt_filename",
    "txt_size_bytes",
    "txt_sha256",
    "pages",
    "text_chars",
    "text_lines",
    "extraction_method",
    "extraction_note",
]

MJ_ARCHIVE_FIELDS = ["category", "content_key", "language", "label"] + ARCHIVE_FIELDS


def main() -> None:
    parser = argparse.ArgumentParser(description="Archive original library source PDFs to external storage.")
    parser.add_argument("--city", choices=["delhi", "ahmedabad", "all"], default="all")
    parser.add_argument("--external-root", type=Path, default=DEFAULT_EXTERNAL_ROOT)
    parser.add_argument("--no-download", action="store_true", help="Only process PDFs already present in the archive.")
    args = parser.parse_args()

    if args.city in {"delhi", "all"}:
        archive_dpl(args.external_root, no_download=args.no_download)
    if args.city in {"ahmedabad", "all"}:
        archive_mj(args.external_root, no_download=args.no_download)


def archive_dpl(external_root: Path, *, no_download: bool = False) -> None:
    archive_dir = external_root / "delhi" / "libraries" / "dpl" / "annual_reports"
    rows = []
    staffing_rows = []
    seen_years: set[str] = set()
    for source in read_csv(DPL_SOURCE):
        year = source["year"]
        if year in seen_years:
            continue
        seen_years.add(year)
        url = source["source_url"]
        pdf_name = f"dpl_{year.replace('-', '_')}.pdf"
        pdf_path = archive_dir / pdf_name
        if no_download and not pdf_path.exists():
            continue
        try:
            row = archive_source_pdf(
                year=year,
                source_url=url,
                archive_dir=archive_dir,
                pdf_filename=pdf_name,
                min_text_chars=2000,
                language="eng+hin",
            )
        except RuntimeError as exc:
            rows.append(failed_archive_row(year, url, archive_dir, pdf_name, str(exc)))
            continue
        rows.append(row)
        text_path = archive_dir / row["txt_filename"]
        staffing = parse_dpl_staffing_text(year, text_path.read_text(encoding="utf-8", errors="ignore"))
        staffing["source_url"] = url
        staffing["archive_pdf_path"] = str(archive_dir / row["pdf_filename"])
        if staffing["extraction_status"] != "not_found":
            staffing_rows.append(staffing)
        elif year >= "2017-18":
            staffing_rows.append(staffing)

    write_csv(DPL_MANIFEST, rows, ARCHIVE_FIELDS)
    write_csv(DPL_STAFFING, staffing_rows, STAFFING_FIELDS)
    print(f"wrote {DPL_MANIFEST.relative_to(REPO)} ({len(rows)} rows)")
    print(f"wrote {DPL_STAFFING.relative_to(REPO)} ({len(staffing_rows)} rows)")


def archive_mj(external_root: Path, *, no_download: bool = False) -> None:
    archive_dir = external_root / "ahmedabad" / "libraries" / "mj_library" / "source_pdfs"
    rows = []
    seen_urls: set[str] = set()
    for source in read_csv(MJ_SOURCE):
        url = source["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        category = source["category"]
        year = source["year"] or category
        pdf_name = f"{category}_{year}_{Path(url).name}".replace("/", "_").replace(" ", "_")
        pdf_path = archive_dir / pdf_name
        if no_download and not pdf_path.exists():
            continue
        try:
            archive_row = archive_source_pdf(
                year=year,
                source_url=url,
                archive_dir=archive_dir,
                pdf_filename=pdf_name,
                min_text_chars=2000,
                language="eng+guj",
            )
        except RuntimeError as exc:
            archive_row = failed_archive_row(year, url, archive_dir, pdf_name, str(exc))
        rows.append(
            {
                "category": category,
                "content_key": source["content_key"],
                "language": source["language"],
                "label": source["label"],
                **archive_row,
            }
        )

    write_csv(MJ_MANIFEST, rows, MJ_ARCHIVE_FIELDS)
    print(f"wrote {MJ_MANIFEST.relative_to(REPO)} ({len(rows)} rows)")


def failed_archive_row(year: str, source_url: str, archive_dir: Path, pdf_name: str, error: str) -> dict[str, str]:
    return {
        "year": year,
        "source_url": source_url,
        "archive_dir": str(archive_dir),
        "pdf_filename": pdf_name,
        "pdf_size_bytes": "",
        "pdf_sha256": "",
        "txt_filename": "",
        "txt_size_bytes": "",
        "txt_sha256": "",
        "pages": "",
        "text_chars": "",
        "text_lines": "",
        "extraction_method": "download_failed",
        "extraction_note": error.splitlines()[-1][:500],
    }


if __name__ == "__main__":
    main()
