#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import shutil
import subprocess
from pathlib import Path

from sevent4.application.acquisition import (
    STAFFING_FIELDS,
    google_drive_download_url,
    parse_dpl_staffing_text,
    text_needs_ocr,
    vacancy_rate,
)
from scripts.recipes.library_networks import pdf_pages, run_pdftotext, sha256


def drive_download_url(url: str) -> str:
    return google_drive_download_url(url)


def fetch_with_curl(url: str, output_path: Path, *, timeout_seconds: int = 90) -> None:
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl is required for source archiving")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            curl,
            "-L",
            "--fail",
            "--max-time",
            str(timeout_seconds),
            "-o",
            str(output_path),
            drive_download_url(url),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"curl failed for {url}")


def extract_text_with_ocr(
    pdf_path: Path,
    text_path: Path,
    *,
    min_chars: int = 2000,
    language: str = "eng",
) -> str:
    text_path.parent.mkdir(parents=True, exist_ok=True)
    run_pdftotext(pdf_path, text_path)
    text = text_path.read_text(encoding="utf-8", errors="ignore")
    if not text_needs_ocr(text, min_chars=min_chars):
        return "pdftotext -layout"

    ocrmypdf = shutil.which("ocrmypdf")
    if not ocrmypdf:
        return "pdftotext -layout; ocr_needed"
    ocr_pdf = pdf_path.with_suffix(".ocr.pdf")
    result = subprocess.run(
        [
            ocrmypdf,
            "--skip-text",
            "--sidecar",
            str(text_path),
            "-l",
            language,
            str(pdf_path),
            str(ocr_pdf),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "pdftotext -layout; ocr_failed"
    return "ocrmypdf --sidecar"


def archive_source_pdf(
    *,
    year: str,
    source_url: str,
    archive_dir: Path,
    pdf_filename: str | None = None,
    existing_pdf: Path | None = None,
    min_text_chars: int = 2000,
    language: str = "eng",
) -> dict[str, str]:
    archive_dir.mkdir(parents=True, exist_ok=True)
    pdf_name = pdf_filename or f"{safe_slug(year)}.pdf"
    pdf_path = archive_dir / pdf_name
    if existing_pdf:
        shutil.copy2(existing_pdf, pdf_path)
    elif not pdf_path.exists():
        fetch_with_curl(source_url, pdf_path)
    text_path = pdf_path.with_suffix(".txt")
    extraction_method = extract_text_with_ocr(pdf_path, text_path, min_chars=min_text_chars, language=language)
    text = text_path.read_text(encoding="utf-8", errors="ignore")
    return {
        "year": year,
        "source_url": source_url,
        "archive_dir": str(archive_dir),
        "pdf_filename": pdf_path.name,
        "pdf_size_bytes": str(pdf_path.stat().st_size),
        "pdf_sha256": sha256(pdf_path),
        "txt_filename": text_path.name,
        "txt_size_bytes": str(text_path.stat().st_size),
        "txt_sha256": sha256(text_path),
        "pages": str(pdf_pages(pdf_path)),
        "text_chars": str(len(text)),
        "text_lines": str(len(text.splitlines())),
        "extraction_method": extraction_method,
        "extraction_note": extraction_note(extraction_method),
    }


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()


def extraction_note(method: str) -> str:
    if method == "ocrmypdf --sidecar":
        return "OCR sidecar text retained because initial pdftotext output was too sparse."
    if "ocr_needed" in method:
        return "Initial pdftotext output was too sparse; OCR tool unavailable."
    if "ocr_failed" in method:
        return "Initial pdftotext output was too sparse; OCR attempt failed."
    return "pdftotext layout extraction retained."


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
