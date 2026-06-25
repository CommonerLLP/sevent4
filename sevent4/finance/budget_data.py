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
