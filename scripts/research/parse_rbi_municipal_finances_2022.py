#!/usr/bin/env python3
"""Parse selected RBI 2022 municipal-finance HTML tables.

The full RBI 2022 PDF URL is published on the official RBI page, but direct
asset downloads can return anti-automation HTML in this environment. The RBI
PublicationsView HTML pages contain the same chapter and appendix tables. This
parser uses those HTML tables structurally through pandas.read_html and fails if
expected rows are absent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


CHAPTER_YEARS = ["2017-18_accounts", "2018-19_re", "2019-20_be"]
APPENDIX_YEARS = ["2017-18_accounts", "2018-19_be", "2018-19_re", "2019-20_be"]

OFFICIAL_URLS = {
    "press_release": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=54673",
    "publication_page": "https://www.rbi.org.in/scripts/AnnualPublications.aspx?fromdate=11%2F09%2F2022&head=Report+on+Municipal+Finances&todate=11%2F11%2F2022",
    "full_pdf": "https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/RMF101120223A34C4F7023A4A9E99CB7F7FEF6881D0.PDF",
    "chapter_ii_html": "https://www.rbi.org.in/scripts/PublicationsView.aspx?id=21361",
    "appendix_i_delhi_html": "https://www.rbi.org.in/scripts/PublicationsView.aspx?id=21380",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_label(value: Any) -> str:
    text = str(value)
    text = text.replace("\u2019", "'").replace("\u2013", "-")
    return " ".join(text.split())


def clean_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, int | float):
        return float(value)
    text = clean_label(value)
    if text in {"", "-", "\u2013", "nan"}:
        return None
    return float(text.replace(",", ""))


def row_values(df: pd.DataFrame, label: str, years: list[str], start_col: int = 1) -> dict[str, float | None]:
    matches = df[df.iloc[:, 0].map(clean_label) == label]
    if matches.empty:
        raise ValueError(f"Missing row: {label}")
    row = matches.iloc[0]
    vals = [clean_value(row.iloc[idx]) for idx in range(start_col, start_col + len(years))]
    return dict(zip(years, vals))


def table_by_title(
    tables: list[pd.DataFrame],
    title: str,
    max_cols: int | None = None,
    min_rows: int = 1,
) -> pd.DataFrame:
    for df in tables:
        if df.shape[0] < min_rows:
            continue
        if max_cols is not None and df.shape[1] > max_cols:
            continue
        first_cell = clean_label(df.iloc[0, 0]) if not df.empty else ""
        if title in first_cell:
            return df
    raise ValueError(f"Missing table: {title}")


def parse_chapter2(chapter2_html: Path) -> dict[str, Any]:
    tables = pd.read_html(chapter2_html)
    revenue = table_by_title(tables, "Table II.1: Revenue Receipts", max_cols=4, min_rows=5)
    non_tax = table_by_title(tables, "Table II.2: MCs' Non-Tax Revenue", max_cols=4, min_rows=5)
    ratios = table_by_title(tables, "Table II.3: Municipal Corporations' Finances", max_cols=4, min_rows=5)

    return {
        "ii_1_revenue_receipts_percent_gdp": {
            "revenue_receipts": row_values(revenue, "Revenue Receipts", CHAPTER_YEARS),
            "own_tax_revenue": row_values(revenue, "Own Tax Revenue", CHAPTER_YEARS),
            "property_tax": row_values(revenue, "Of which: Property Tax", CHAPTER_YEARS),
            "own_non_tax_revenue": row_values(revenue, "Own Non-Tax Revenue", CHAPTER_YEARS),
            "transfers": row_values(revenue, "Transfer", CHAPTER_YEARS),
        },
        "ii_2_non_tax_revenue_percent_gdp": {
            "own_non_tax_revenue": row_values(non_tax, "Own Non-Tax Revenue", CHAPTER_YEARS),
            "rental_income_from_municipal_properties": row_values(
                non_tax, "1. Rental Income from Municipal Properties", CHAPTER_YEARS
            ),
            "fees_user_charges": row_values(non_tax, "2. Fees and User Charges", CHAPTER_YEARS),
            "sale_hire_charges": row_values(non_tax, "3. Sale and Hire Charges", CHAPTER_YEARS),
            "income_from_investment": row_values(non_tax, "4. Income from Investment", CHAPTER_YEARS),
            "other_income": row_values(non_tax, "5. Other Income", CHAPTER_YEARS),
        },
        "ii_3_key_ratios_percent": {
            "own_revenue_to_total_revenue": row_values(
                ratios, "Ratio of Own Revenue to Total Revenue Receipts", CHAPTER_YEARS
            ),
            "own_tax_revenue_to_total_revenue": row_values(
                ratios, "Ratio of Own Tax Revenue to Total Revenue Receipts", CHAPTER_YEARS
            ),
            "property_tax_to_total_revenue": row_values(
                ratios, "Ratio of Property Tax Collection to Total Revenue Receipts", CHAPTER_YEARS
            ),
            "state_transfer_to_total_revenue": row_values(
                ratios, "Ratio of States' Transfer to Total Revenue Receipts", CHAPTER_YEARS
            ),
            "central_transfer_to_total_revenue": row_values(
                ratios, "Ratio of Central Government's Transfer to Total Revenue Receipts", CHAPTER_YEARS
            ),
            "combined_transfer_to_total_revenue": row_values(
                ratios, "Ratio of Combined (Centre plus States) Transfer to Total Revenue Receipts", CHAPTER_YEARS
            ),
        },
    }


def lakh_to_crore(row: dict[str, float | None]) -> dict[str, float | None]:
    return {year: None if value is None else round(value / 100, 3) for year, value in row.items()}


def parse_appendix_revenue(appendix_html: Path) -> dict[str, Any]:
    tables = pd.read_html(appendix_html)
    target = None
    for df in tables:
        cells = [clean_label(v) for v in df.astype(str).values.flatten()[:30]]
        if "DELHI" in cells and "ALL STATES/UTs" in cells:
            target = df
            break
    if target is None:
        raise ValueError("Missing Delhi/All States appendix table")

    rows = {
        "revenue_receipts": "Revenue Receipts (I+II+III)",
        "own_revenue": "I. Own Revenue (A+B+C)",
        "own_tax_revenue": "A. Own Tax Revenue (1 - 16)",
        "property_tax": "1 Property Tax",
        "own_non_tax_revenue": "B. Own Non-Tax Revenue (1 - 7)",
        "fees_user_charges": "2 Fees and User Charges (i-v)",
        "transfers": "II. Transfers (A+B+C)",
        "central_transfers": "A. Central Transfers (1+2+3)",
        "fc_transfers": "1 FC Transfers",
        "state_transfers": "B. State Transfers (1+2+3+4+5)",
        "assigned_revenues_compensation": "1 Assigned Revenues, compensation",
        "sfc_grants": "2 SFC Grants",
        "state_grant_in_aid_transfers": "3 State grant in aid transfers",
    }

    out: dict[str, Any] = {
        "source_unit": "INR lakh",
        "derived_unit": "INR crore",
        "Delhi": {},
        "All States/UTs": {},
    }
    for key, label in rows.items():
        delhi_lakh = row_values(target, label, APPENDIX_YEARS, start_col=1)
        all_lakh = row_values(target, label, APPENDIX_YEARS, start_col=5)
        out["Delhi"][key] = {
            "inr_lakh": delhi_lakh,
            "inr_crore": lakh_to_crore(delhi_lakh),
        }
        out["All States/UTs"][key] = {
            "inr_lakh": all_lakh,
            "inr_crore": lakh_to_crore(all_lakh),
        }
    return out


def build(chapter2_html: Path, appendix_revenue_html: Path, publication_page_html: Path | None) -> dict[str, Any]:
    source_files = {
        "chapter2_html": {
            "path": str(chapter2_html),
            "sha256": sha256(chapter2_html),
        },
        "appendix_revenue_delhi_html": {
            "path": str(appendix_revenue_html),
            "sha256": sha256(appendix_revenue_html),
        },
    }
    if publication_page_html is not None:
        source_files["publication_page_html"] = {
            "path": str(publication_page_html),
            "sha256": sha256(publication_page_html),
        }

    return {
        "source": {
            "report": "RBI Report on Municipal Finances",
            "release_date": "2022-11-10",
            "coverage_municipal_corporations": 201,
            "theme": "Alternative Sources of Financing for Municipal Corporations",
            "official_urls": OFFICIAL_URLS,
            "source_files": source_files,
            "parser": "scripts/research/parse_rbi_municipal_finances_2022.py",
            "asset_note": (
                "The official full PDF URL is recorded, but the deterministic extraction here uses "
                "official RBI PublicationsView HTML pages because direct rbidocs asset requests "
                "returned anti-automation HTML in this environment."
            ),
        },
        "tables": {
            **parse_chapter2(chapter2_html),
            "appendix_i_revenue_receipts_delhi_all_states_uts": parse_appendix_revenue(appendix_revenue_html),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter2-html", type=Path, required=True)
    parser.add_argument("--appendix-revenue-html", type=Path, required=True)
    parser.add_argument("--publication-page-html", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = build(args.chapter2_html, args.appendix_revenue_html, args.publication_page_html)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
