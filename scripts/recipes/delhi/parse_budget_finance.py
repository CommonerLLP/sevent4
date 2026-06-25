#!/usr/bin/env python3
"""Parse Delhi's three civic budgets (GNCTD / MCD / NDMC) into one comparable
finance series, to make the municipal-finance fragmentation legible (most spend
sits with the GNCTD, not the elected MCD; NDMC is a nominated-council enclave).

Outputs: data/cities/delhi/derived/finance/delhi_finance.{json,csv}

Thin CLI wrapper: number parsing, fiscal-year inference, plausibility floors, and
the per-body row builders live in sevent4.domain.delhi_finance /
sevent4.application.delhi_finance; pdftotext + OCR-sidecar reads and JSON/CSV
writes in the delhi-finance adapter.

    .venv/bin/python scripts/recipes/delhi/parse_budget_finance.py
"""
from __future__ import annotations

from pathlib import Path

from sevent4.adapters.delhi_finance_filesystem import DelhiFinanceSource, write_finance_csv, write_json
from sevent4.application.delhi_finance import parse_delhi_finance

# Re-exported so the existing test (loads this module by path) keeps a stable surface.
from sevent4.domain.delhi_finance import (  # noqa: F401
    FIELDS,
    fy_from_name,
    last_total,
    nums,
    plausible,
)

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/cities/delhi/derived/finance"


def main() -> None:
    source = DelhiFinanceSource(ROOT)
    rows, meta = parse_delhi_finance(source)

    write_json(meta, OUT / "delhi_finance.json")
    write_finance_csv(rows, OUT / "delhi_finance.csv", FIELDS)

    print(f"wrote delhi_finance.json + .csv — {len(rows)} rows "
          f"(GNCTD {sum(r['body'] == 'GNCTD' for r in rows)}, MCD {sum(r['body'] == 'MCD' for r in rows)}, "
          f"NDMC {sum(r['body'] == 'NDMC' for r in rows)})")
    for r in rows:
        head = r.get("total_expenditure_cr") or r.get("total_receipts_cr") or r.get("total_income_cr")
        print(f"  {r['body']:<6} {r['fy']:<8} ~₹{head} cr  [{r.get('scope', '')}]")


if __name__ == "__main__":
    main()
