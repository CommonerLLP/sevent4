#!/usr/bin/env python3
"""Parse selected RBI Report on Municipal Finances tables from pdftotext output.

The parser is deliberately narrow: it extracts only the table rows that the
The Unelected City research note relies on. It uses fixed table titles and row labels from
the RBI PDF, so failed layout changes surface as missing rows instead of silent
guesses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


YEARS_5 = [
    "2019-20_accounts",
    "2020-21_accounts",
    "2021-22_accounts",
    "2022-23_re",
    "2023-24_be",
]

STATE_TABLE_II_2_YEARS = [
    "2021-22_accounts",
    "2022-23_re",
    "2023-24_be",
]

STATE_NAMES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Mizoram",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "All India",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pdftotext(pdf: Path) -> str:
    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        check=True,
        text=True,
        capture_output=True,
    )
    return proc.stdout


def value(token: str) -> int | float | None:
    if token in {"NA", "-"}:
        return None
    clean = token.replace(",", "")
    if "." in clean:
        return float(clean)
    return int(clean)


def num_tokens(text: str) -> list[int | float | None]:
    return [value(tok) for tok in re.findall(r"NA|-?\d[\d,]*(?:\.\d+)?|-", text)]


def normalized_line(line: str) -> str:
    return line.strip().replace("\u2019", "'")


def section(text: str, start: str, end: str) -> str:
    start_idx = text.index(start)
    end_idx = text.index(end, start_idx)
    return text[start_idx:end_idx]


def state_rows(block: str, expected_values: int) -> dict[str, list[int | float | None]]:
    rows: dict[str, list[int | float | None]] = {}
    for raw_line in block.splitlines():
        line = normalized_line(raw_line)
        for state in STATE_NAMES:
            if line.startswith(state + " "):
                vals = num_tokens(line[len(state) :])
                if len(vals) == expected_values:
                    rows[state] = vals
                break
    missing = [state for state in STATE_NAMES if state not in rows]
    if missing:
        raise ValueError(f"Missing state rows: {missing}")
    return rows


def grouped(values: list[Any], years: list[str], fields: list[str]) -> dict[str, dict[str, Any]]:
    if len(values) != len(years) * len(fields):
        raise ValueError(f"Expected {len(years) * len(fields)} values, found {len(values)}")
    out: dict[str, dict[str, Any]] = {}
    offset = 0
    for year in years:
        out[year] = {}
        for field in fields:
            out[year][field] = values[offset]
            offset += 1
    return out


def parse_table_ii_2(text: str) -> dict[str, Any]:
    block = section(text, "Table II.2: State-wise Municipal Corporations", "Table II.3:")
    rows = state_rows(block, 9)
    fields = ["revenue_receipts_inr_crore", "revenue_expenditure_inr_crore", "surplus_deficit_inr_crore"]
    return {state: grouped(vals, STATE_TABLE_II_2_YEARS, fields) for state, vals in rows.items()}


def parse_table_ii_3(text: str) -> dict[str, Any]:
    block = section(text, "Table II.3: Ratio of Municipal Corporations", "Table II.4:")
    rows = state_rows(block, 5)
    return {state: dict(zip(YEARS_5, vals)) for state, vals in rows.items()}


def parse_table_ii_4(text: str) -> dict[str, Any]:
    block = section(text, "Table II.4: Revenue Receipts", "Table II.5:")
    labels = {
        "Revenue Receipts": "revenue_receipts_inr_crore",
        "I. Own Tax Revenue": "own_tax_revenue_inr_crore",
        "Of which: Property Tax": "property_tax_inr_crore",
        "Of which: Water Tax": "water_tax_inr_crore",
        "II. Own Non-Tax Revenue": "own_non_tax_revenue_inr_crore",
        "Of which: Fees and User Charges": "fees_user_charges_inr_crore",
        "Of which: Income from Investment": "income_from_investment_inr_crore",
        "III. Transfers": "transfers_inr_crore",
    }
    out: dict[str, dict[str, int | float | None]] = {}
    all_mcs = block.split("b. Top 10 Municipal Corporations", 1)[0]
    for line in all_mcs.splitlines():
        stripped = normalized_line(line)
        for label, key in labels.items():
            if stripped.startswith(label):
                vals = num_tokens(stripped[len(label) :])
                if len(vals) == 5:
                    out[key] = dict(zip(YEARS_5, vals))
                break
    missing = [key for key in labels.values() if key not in out]
    if missing:
        raise ValueError(f"Missing Table II.4 rows: {missing}")
    return out


def parse_table_ii_5(text: str) -> dict[str, Any]:
    block = section(text, "Table II.5: Ratio of Municipal Corporations", "Table II.6:")
    rows = state_rows(block, 10)
    out: dict[str, Any] = {}
    for state, vals in rows.items():
        out[state] = {
            "tax_revenue_ratio_to_state_tax_revenue_percent": dict(zip(YEARS_5, vals[:5])),
            "non_tax_revenue_ratio_to_state_non_tax_revenue_percent": dict(zip(YEARS_5, vals[5:])),
        }
    return out


def parse_table_ii_7(text: str) -> dict[str, Any]:
    block = section(text, "Table II.7: Grants to Urban Local Bodies", "Table II.8:")
    labels = {
        "Total Grants from the Central Government to the MCs@": "central_grants_to_mcs_inr_crore",
        "Finance Commission Grants as Reported by the Municipal Corporations": "fc_grants_reported_by_mcs_inr_crore",
        "Grants from Central Government other than Finance Commission Grants": "central_grants_other_than_fc_inr_crore",
        "Total Grants from the State Governments to the MCs@": "state_grants_to_mcs_inr_crore",
        "State Finance Commission Grants as Reported by the Municipal Corporations": "sfc_grants_reported_by_mcs_inr_crore",
        "Finance Commission Grants to ULBs as reported in the Union Budget": "fc_grants_to_ulbs_union_budget_inr_crore",
    }
    years = YEARS_5[:4]
    out: dict[str, dict[str, int | float | None]] = {}
    for line in block.splitlines():
        stripped = normalized_line(line)
        for label, key in labels.items():
            if stripped.startswith(label):
                vals = num_tokens(stripped[len(label) :])
                if len(vals) == 4:
                    out[key] = dict(zip(years, vals))
                break
    state_other_match = re.search(
        r"Grants from the State Governments other than State Finance Commission\s+"
        r"([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+Grants",
        block,
    )
    if state_other_match:
        out["state_grants_other_than_sfc_inr_crore"] = dict(
            zip(years, [value(v) for v in state_other_match.groups()])
        )
    missing = [key for key in list(labels.values()) + ["state_grants_other_than_sfc_inr_crore"] if key not in out]
    if missing:
        raise ValueError(f"Missing Table II.7 rows: {missing}")
    return out


def parse_table_ii_8(text: str) -> dict[str, Any]:
    block = section(text, "Table II.8: Municipal Corporations", "Table II.9:")
    labels = {
        "Own Revenue / Total Revenue Receipts": "own_revenue_to_total_revenue_percent",
        "Tax Revenue / Total Revenue Receipts": "tax_revenue_to_total_revenue_percent",
        "Property Tax Collection / Total Revenue Receipts": "property_tax_to_total_revenue_percent",
        "States' Transfer / Total Revenue Receipts": "state_transfer_to_total_revenue_percent",
        "Central Government's Transfer / Total Revenue Receipts": "central_transfer_to_total_revenue_percent",
        "Combined (Centre plus States) Transfer / Total Revenue Receipts": "combined_transfer_to_total_revenue_percent",
    }
    out: dict[str, dict[str, int | float | None]] = {}
    for line in block.splitlines():
        stripped = normalized_line(line)
        for label, key in labels.items():
            if stripped.startswith(label):
                vals = num_tokens(stripped[len(label) :])
                if len(vals) == 5:
                    out[key] = dict(zip(YEARS_5, vals))
                break
    expected = set(labels.values())
    missing = [key for key in expected if key not in out]
    if missing:
        raise ValueError(f"Missing Table II.8 rows: {missing}")
    return out


def build(pdf: Path) -> dict[str, Any]:
    text = pdftotext(pdf)
    cover = text[:400].replace("\f", " ").strip()
    return {
        "source": {
            "path": str(pdf),
            "sha256": sha256(pdf),
            "cover_text": cover,
            "parser": "scripts/research/parse_rbi_municipal_finances.py",
        },
        "tables": {
            "ii_2_state_revenue_receipts_expenditure": parse_table_ii_2(text),
            "ii_3_mc_revenue_to_state_revenue_ratio": parse_table_ii_3(text),
            "ii_4_all_mc_revenue_receipts": parse_table_ii_4(text),
            "ii_5_mc_tax_non_tax_to_state_ratios": parse_table_ii_5(text),
            "ii_7_grants_to_ulbs": parse_table_ii_7(text),
            "ii_8_key_ratios": parse_table_ii_8(text),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = build(args.pdf)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
