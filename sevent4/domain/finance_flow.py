from __future__ import annotations

from collections import defaultdict


CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def gba_links_from_summaries(summaries: list[dict]) -> list[dict]:
    links: list[dict] = []
    payment_heads = defaultdict(float)
    for summary in summaries:
        corp = summary["corporation"]
        receipts = float(summary.get("total_receipts_cr") or 0)
        payments = float(summary.get("total_payments_cr") or 0)
        if receipts > 0:
            links.append({"source": corp, "target": "Receipts", "amount_cr": round(receipts, 2), "group": "receipts"})
        if payments > 0:
            links.append({"source": corp, "target": "Payments", "amount_cr": round(payments, 2), "group": "payments"})
        for row in summary.get("top_payment_heads", [])[:5]:
            amount = float(row.get("amount_cr") or 0)
            if amount > 0:
                payment_heads[str(row["label"])] += amount
    for label, amount in sorted(payment_heads.items(), key=lambda item: item[1], reverse=True)[:8]:
        links.append(
            {
                "source": "Payments",
                "target": label,
                "amount_cr": round(amount, 2),
                "group": "payment_head",
            }
        )
    return links


def gba_flow_notes(summaries: list[dict]) -> list[str]:
    files = ", ".join(summary["source_file"] for summary in summaries)
    return [
        "Amounts are Budget Estimate 2026-27 values, converted from lakhs to crore.",
        "Receipts and payments are shown as separate budget views; do not add them together as one total.",
        f"Source workbooks: {files}.",
    ]


def amc_flow_year(budget_lines: list[dict]) -> str:
    eligible = [flow["year"] for flow in amc_year_flows(budget_lines) if flow["status"] == "complete"]
    return max(eligible, key=lambda year: int(year.split("-")[0])) if eligible else ""


def amc_year_flows(budget_lines: list[dict]) -> list[dict]:
    years = sorted({row["fiscal_year"] for row in budget_lines if _is_amc_flow_row(row)}, key=lambda year: int(year.split("-")[0]))
    flows = []
    for year in years:
        links = amc_links_from_budget_lines(budget_lines, year)
        if not links:
            continue
        rows = _dedupe_amc_heads([row for row in budget_lines if row.get("fiscal_year") == year and _is_amc_flow_row(row)])
        flows.append(
            {
                "year": year,
                "status": "complete" if len(rows) >= 4 else "partial",
                "links": links,
                "notes": amc_flow_notes(budget_lines, year),
                "rows": [_flow_row(row) for row in sorted(rows, key=lambda item: (_section_label(item), str(item.get("head_name") or "")))],
            }
        )
    return flows


def amc_links_from_budget_lines(budget_lines: list[dict], fiscal_year: str | None = None) -> list[dict]:
    year = fiscal_year or amc_flow_year(budget_lines)
    if not year:
        return []
    rows = [row for row in budget_lines if row.get("fiscal_year") == year and _is_amc_flow_row(row)]
    rows = _dedupe_amc_heads(rows)
    section_totals: dict[str, float] = defaultdict(float)
    for row in rows:
        section_totals[_section_label(row)] += float(row["amount_cr"])
    links = [
        {
            "source": "Ahmedabad Municipal Corporation",
            "target": section,
            "amount_cr": round(amount, 2),
            "group": "payments",
        }
        for section, amount in sorted(section_totals.items(), key=lambda item: item[1], reverse=True)
        if amount > 0
    ]
    for row in sorted(rows, key=lambda item: float(item["amount_cr"]), reverse=True)[:8]:
        links.append(
            {
                "source": _section_label(row),
                "target": str(row["head_name"]),
                "amount_cr": round(float(row["amount_cr"]), 2),
                "group": "payment_head",
            }
        )
    return links


def amc_flow_notes(budget_lines: list[dict], fiscal_year: str | None = None) -> list[str]:
    year = fiscal_year or amc_flow_year(budget_lines)
    rows = [row for row in budget_lines if row.get("fiscal_year") == year and _is_amc_flow_row(row)]
    sources = sorted({str(row.get("source_pdf") or "budget_line.csv") for row in rows})
    return [
        f"Flow uses {year} Budget Estimate expenditure rows from data/cities/ahmedabad/db/budget_line.csv.",
        "This is a selected, source-backed civic-line view, not the full municipal budget total.",
        "Amounts are normalised to rupees crore; low-confidence and blank extractions are excluded.",
        "Source PDFs: " + ", ".join(sources) + ".",
    ]


def _is_amc_flow_row(row: dict) -> bool:
    if row.get("city") != "ahmedabad":
        return False
    if row.get("estimate_basis") != "BE" or row.get("flow") != "expenditure":
        return False
    if not row.get("source_pdf"):
        return False
    if row.get("amount_cr") is None or float(row.get("amount_cr") or 0) <= 0:
        return False
    return CONFIDENCE_RANK.get(str(row.get("confidence") or ""), 0) >= 2


def _section_label(row: dict) -> str:
    section = str(row.get("section") or "").strip().lower()
    if section == "capital":
        return "Capital expenditure"
    if section == "revenue":
        return "Revenue expenditure"
    return "Expenditure"


def _dedupe_amc_heads(rows: list[dict]) -> list[dict]:
    selected: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (_section_label(row), str(row.get("head_name") or ""))
        current = selected.get(key)
        if current is None or _row_rank(row) > _row_rank(current):
            selected[key] = row
    return list(selected.values())


def _flow_row(row: dict) -> dict:
    return {
        "year": row.get("fiscal_year"),
        "section": _section_label(row),
        "head": row.get("head_name") or "",
        "amount_cr": round(float(row.get("amount_cr") or 0), 2),
        "source_pdf": row.get("source_pdf") or "",
        "page": str(row.get("page") or ""),
        "confidence": row.get("confidence") or "",
    }


def _row_rank(row: dict) -> tuple[int, int]:
    return (
        CONFIDENCE_RANK.get(str(row.get("confidence") or ""), 0),
        1 if row.get("source_pdf") else 0,
    )
