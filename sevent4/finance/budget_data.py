from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def fy_start(year: str) -> int:
    """'2005-06' -> 2005."""
    return int(year.split("-")[0])


def load_headline(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "year": row["year"],
                    "start": fy_start(row["year"]),
                    "amts_cr": _num(row.get("amts_cr", "")),
                    "mj_library_cr": _num(row.get("mj_library_cr", "")),
                    "property_tax_cr": _num(row.get("property_tax_cr", "")),
                    "total_cr": _num(row.get("total_cr", "")),
                    "confidence": (row.get("confidence") or "").strip(),
                    "page": (row.get("amts_page") or "").strip(),
                    "notes": (row.get("notes") or "").strip(),
                }
            )
    return sorted(rows, key=lambda item: item["start"])


def load_budget_lines(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            item = dict(row)
            item["amount_cr"] = _num(row.get("amount_cr", ""))
            item["fy_start"] = int(row["fy_start"]) if row.get("fy_start") else fy_start(row["fiscal_year"])
            rows.append(item)
    return rows


def load_budget_stages(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            item = dict(row)
            item["amount_cr"] = _num(row.get("amount_cr", ""))
            item["year"] = (row.get("year") or "").strip()
            rows.append(item)
    return sorted(rows, key=lambda item: (fy_start(item["year"]), item.get("stage") or ""))


def enrich_headline_from_budget_lines(
    headline: list[dict[str, Any]],
    budget_lines: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_year = {row["year"]: dict(row) for row in headline}
    years = sorted({row["fiscal_year"] for row in budget_lines if row.get("fiscal_year")})
    for year in years:
        row = by_year.setdefault(
            year,
            {
                "year": year,
                "start": fy_start(year),
                "amts_cr": None,
                "mj_library_cr": None,
                "property_tax_cr": None,
                "total_cr": None,
                "confidence": "",
                "page": "",
                "notes": "filled from canonical budget_line.csv",
            },
        )
        selected: list[dict[str, Any]] = []
        for key, predicate in [
            ("amts_cr", lambda item: item.get("entity") == "AMTS" and item.get("head_name") == "Loan/support to AMTS (city bus)"),
            ("mj_library_cr", lambda item: item.get("entity") == "MJ_LIBRARY" and item.get("head_name") == "Grant to Sheth M.J. Library"),
            ("property_tax_cr", lambda item: item.get("head_name") == "Property tax (general tax)"),
            ("total_cr", lambda item: item.get("head_name") == "Total revenue budget"),
        ]:
            if row.get(key) is not None:
                continue
            match = _best_line(row["year"], budget_lines, predicate)
            if match is None:
                continue
            row[key] = match["amount_cr"]
            selected.append(match)
        if selected and not row.get("confidence"):
            row["confidence"] = _best_confidence(selected)
        if selected and not row.get("page"):
            page = next((str(item.get("page") or "") for item in selected if item.get("page")), "")
            row["page"] = page
    return sorted(by_year.values(), key=lambda item: item["start"])


def civic_rows_from_budget_lines(budget_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    for row in budget_lines:
        if row.get("amount_cr") is None:
            continue
        if not row.get("source_pdf"):
            continue
        line = _civic_line_key(row)
        if line is None:
            continue
        mapped.append(
            {
                "year": row["fiscal_year"],
                "line": line,
                "amount_cr": row["amount_cr"],
                "raw": row.get("amount_raw") or row.get("head_name_raw") or "",
                "page": row.get("page") or "",
                "source_pdf": row.get("source_pdf") or "",
                "account_head": row.get("head_name") or "",
                "estimate_basis": row.get("estimate_basis") or "",
                "confidence": row.get("confidence") or "",
                "exact_line": row.get("note") or "",
            }
        )
    return _dedupe_civic_rows(mapped)


def load_civic_lines(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("_meta", {}), data.get("data", [])


def _num(value: str) -> float | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _best_line(year: str, rows: list[dict[str, Any]], predicate) -> dict[str, Any] | None:
    matches = [
        row for row in rows
        if row.get("fiscal_year") == year and row.get("amount_cr") is not None and predicate(row)
    ]
    return sorted(matches, key=_line_rank, reverse=True)[0] if matches else None


def _line_rank(row: dict[str, Any]) -> tuple[int, int, int]:
    basis_rank = {"BE": 3, "RE": 2, "actual": 1}.get(str(row.get("estimate_basis") or ""), 0)
    confidence_rank = {"high": 3, "medium": 2, "low": 1}.get(str(row.get("confidence") or ""), 0)
    source_rank = 1 if row.get("source_pdf") else 0
    return basis_rank, confidence_rank, source_rank


def _best_confidence(rows: list[dict[str, Any]]) -> str:
    ranked = sorted((str(row.get("confidence") or "") for row in rows), key=lambda value: {"high": 3, "medium": 2, "low": 1}.get(value, 0), reverse=True)
    return ranked[0] if ranked else ""


def _civic_line_key(row: dict[str, Any]) -> str | None:
    entity = row.get("entity")
    head = row.get("head_name")
    if entity == "AMTS" and head == "Loan/support to AMTS (city bus)":
        return "AMTS"
    if entity == "AJL_BRTS":
        return "ajl_brts"
    if entity == "SCHOOL_BOARD":
        return "school_board"
    if entity == "VS_HOSPITAL":
        return "vs_hospital"
    if entity == "MJ_LIBRARY" and head == "Grant to Sheth M.J. Library":
        return "library_mj"
    return None


def _dedupe_civic_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["year"], row["line"])
        current = selected.get(key)
        if current is None or _line_rank(row) > _line_rank(current):
            selected[key] = row
    return sorted(selected.values(), key=lambda item: (fy_start(item["year"]), item["line"]))
