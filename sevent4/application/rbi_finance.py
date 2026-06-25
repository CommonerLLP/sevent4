from __future__ import annotations

from typing import Any

from sevent4.domain.rbi_finance import (
    APPENDIX_YEARS,
    CHAPTER_YEARS,
    OFFICIAL_URLS,
    clean_label,
    clean_value,
    lakh_to_crore,
    parse_rbi_2024_tables,
)


# ---- 2024 edition ----------------------------------------------------------
def build_rbi_2024_report(text: str, source_path: str, sha256_hex: str) -> dict[str, Any]:
    cover = text[:400].replace("\f", " ").strip()
    return {
        "source": {
            "path": source_path,
            "sha256": sha256_hex,
            "cover_text": cover,
            "parser": "scripts/research/parse_rbi_municipal_finances.py",
        },
        "tables": parse_rbi_2024_tables(text),
    }


# ---- 2022 edition (pandas HTML tables, passed in by the adapter) -----------
def row_values(df, label: str, years: list[str], start_col: int = 1) -> dict[str, float | None]:
    matches = df[df.iloc[:, 0].map(clean_label) == label]
    if matches.empty:
        raise ValueError(f"Missing row: {label}")
    row = matches.iloc[0]
    vals = [clean_value(row.iloc[idx]) for idx in range(start_col, start_col + len(years))]
    return dict(zip(years, vals))


def table_by_title(tables, title: str, max_cols: int | None = None, min_rows: int = 1):
    for df in tables:
        if df.shape[0] < min_rows:
            continue
        if max_cols is not None and df.shape[1] > max_cols:
            continue
        first_cell = clean_label(df.iloc[0, 0]) if not df.empty else ""
        if title in first_cell:
            return df
    raise ValueError(f"Missing table: {title}")


def parse_chapter2(tables) -> dict[str, Any]:
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


def parse_appendix_revenue(tables) -> dict[str, Any]:
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
        out["Delhi"][key] = {"inr_lakh": delhi_lakh, "inr_crore": lakh_to_crore(delhi_lakh)}
        out["All States/UTs"][key] = {"inr_lakh": all_lakh, "inr_crore": lakh_to_crore(all_lakh)}
    return out


def build_rbi_2022_report(chapter2_tables, appendix_tables, source_files: dict[str, Any]) -> dict[str, Any]:
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
            **parse_chapter2(chapter2_tables),
            "appendix_i_revenue_receipts_delhi_all_states_uts": parse_appendix_revenue(appendix_tables),
        },
    }
