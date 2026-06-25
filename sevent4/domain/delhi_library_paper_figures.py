"""Pure stats for Delhi Public Library paper figures."""
from __future__ import annotations


def _number(value) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number != number else number


def decline_stats(rows: list[dict]) -> dict:
    issues = [_number(row.get("total_issues")) or 0.0 for row in rows]
    members = [_number(row.get("total_members")) or 0.0 for row in rows]
    peak_index = max(range(len(issues)), key=lambda index: issues[index])
    member_peak_index = max(range(len(members)), key=lambda index: members[index])
    latest_issues = issues[-1]
    peak_issues = issues[peak_index]
    return {
        "peak_index": peak_index,
        "peak_year": rows[peak_index]["year"],
        "peak_issues": peak_issues,
        "latest_year": rows[-1]["year"],
        "latest_issues": latest_issues,
        "drop_pct_vs_peak": (latest_issues - peak_issues) / peak_issues * 100 if peak_issues else 0.0,
        "member_peak_index": member_peak_index,
        "member_peak_year": rows[member_peak_index]["year"],
        "member_peak": members[member_peak_index],
    }


def finance_stats(rows: list[dict]) -> dict:
    finance_rows = [row for row in rows if _number(row.get("grant_received_rs")) is not None]
    returned = sum(_number(row.get("returned_to_ministry_rs")) or 0.0 for row in finance_rows)
    return {
        "finance_years": [row["year"] for row in finance_rows],
        "finance_year_count": len(finance_rows),
        "returned_to_ministry_cr": round(returned / 1e7, 2),
    }
