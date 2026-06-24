#!/usr/bin/env python3
"""Parse OCR-derived city budget summary candidates into a CSV. Thin CLI wrapper:
label matching + number parsing live in the budget application/domain layers,
text/CSV IO in the budget filesystem adapter.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.budget_filesystem import (
    FileBudgetCsvWriter,
    FileBudgetOcrRepository,
    default_budget_csv,
    default_ocr_dir,
)
from sevent4.application.budget import parse_budget_ocr
from sevent4.domain.budget import LABELS_BY_CITY

REPO = Path(__file__).resolve().parents[3]
DEFAULT_CITY = "ahmedabad"


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse OCR-derived city budget summary candidates.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Ahmedabad parser labels are implemented first.")
    parser.add_argument("--ocr-dir", help="Directory containing OCR text files.")
    parser.add_argument("--out", help="Output CSV path.")
    args = parser.parse_args()

    city = args.city.lower()
    labels = LABELS_BY_CITY.get(city)
    if not labels:
        sys.exit(f"No budget parser labels for city={city!r}. Add LABELS_BY_CITY rules first.")

    ocr_dir = Path(args.ocr_dir) if args.ocr_dir else default_ocr_dir(REPO, city)
    out = Path(args.out) if args.out else default_budget_csv(REPO, city)
    repository = FileBudgetOcrRepository(ocr_dir)
    if not repository.exists():
        sys.exit(f"No OCR directory found: {ocr_dir}")

    columns, rows, found = parse_budget_ocr(repository.load_ocr_texts(), labels)
    for year, keys in found:
        print(f"{year}: found {len(keys)}/{len(labels)} labels -> {', '.join(keys)}")
    FileBudgetCsvWriter(out).write_rows(columns, rows)
    print(f"wrote {out} ({len(rows)} years). OCR-derived; verify before using as final finance data.")


if __name__ == "__main__":
    main()
