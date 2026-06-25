#!/usr/bin/env python3
"""
build_budget_db.py — build the canonical municipal budget database (Ahmedabad first).

Reproducible: `.venv/bin/python scripts/budget_db/build_budget_db.py`
Inputs  (verified, in-repo): amc_budget_22yr.csv, amc_civic_lines.json,
    amts_income_expenditure.json under data/cities/ahmedabad/source/budget/.
Inputs  (optional): AMC budget PDFs under the AMC_PDF_DIRS search path.
Outputs (data/cities/ahmedabad/db/): amc_budget.sqlite (canonical) + duckdb,
    parquet, csv, json, xlsx exports.
No figure is invented: every row carries source_pdf, page, extraction_method,
confidence.

Thin CLI wrapper: the four loaders + dedup live in sevent4.domain.amc_budget /
sevent4.application.amc_budget; input reads, pdftotext/pdfinfo, the SQLite build,
and the exports live in the AMC budget filesystem adapter.
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.amc_budget_filesystem import AmcBudgetRepository
from sevent4.application.amc_budget import build_budget_lines

REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    repository = AmcBudgetRepository(REPO)
    civic, ie, csv_rows = repository.read_inputs()
    rows, extracted = build_budget_lines(civic, ie, csv_rows, repository.grant_texts())
    stats = repository.build_database(rows)

    print(f"✓ built {stats['sqlite_path']}")
    print(f"  budget_line rows : {stats['n_budget_lines']}")
    print(f"  source_docs      : {stats['n_source_docs']}  (pdf-on-disk: {stats['n_pdf_on_disk']})")
    print(f"  text-extracted   : {extracted} narrative grant lines")
    if not stats["xlsx_ok"]:
        print(f"  ! xlsx export skipped ({stats['xlsx_err']})")
    print(f"  exports          : sqlite, duckdb, parquet, csv, json, xlsx -> {repository.db}")


if __name__ == "__main__":
    main()
