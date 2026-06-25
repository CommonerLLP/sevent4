from __future__ import annotations

from sevent4.domain.amc_budget import (
    BudgetLineBuilder,
    load_amts_income_expenditure,
    load_budget_22yr_csv,
    load_civic_lines,
    load_grant_text,
)


def build_budget_lines(civic: dict, ie: dict, csv_rows, grant_texts) -> tuple[list[dict], int]:
    """Run the four loaders in priority order into one deduped budget_line set.

    `grant_texts` is an iterable of (fiscal_year, pdf_name, pdftotext) from the
    clean-year English PDFs (loader 4). Returns (rows, narrative_grant_count)."""
    builder = BudgetLineBuilder()
    load_civic_lines(builder, civic)
    load_amts_income_expenditure(builder, ie)
    load_budget_22yr_csv(builder, csv_rows)
    extracted = 0
    for fy, pdf_name, txt in grant_texts:
        extracted += load_grant_text(builder, fy, txt, pdf_name)
    return builder.rows, extracted
