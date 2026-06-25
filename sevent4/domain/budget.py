"""Pure municipal-budget domain logic: Gujarati-digit number parsing, OCR
summary-label matching, finance-book link identity (year + filename), dense-page
selection, and the per-city source/label registries. No filesystem, network, or
subprocess IO lives here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Sequence

GUJARATI_DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")

# Ahmedabad is the first city studied. Other cities add their local table labels
# and public finance pages here as their formats are read.
LABELS_BY_CITY: Mapping[str, Mapping[str, str]] = {
    "ahmedabad": {
        "revenue_exp": r"રેવન્યુ\s*ખર્ચ.*કુલ|મહેસૂલી\s*ખર્ચ.*કુલ",
        "capital_transfer": r"કેપીટલ\s*એકાઉન્ટ.*ટ્રાન્સફર|કેપીટલ\s*એકા.*ટ્રાન",
        "capital_exp": r"કેપીટલ\s*ખર્ચ.*કુલ|મૂડી\s*ખર્ચ.*કુલ",
        "loan_charges": r"લોન\s*ચાર્જ",
        "grand_total": r"એકંદરે?\s*કુલ",
    }
}

CITY_FINANCE_PAGES: Mapping[str, Mapping[str, Mapping[str, object]]] = {
    "ahmedabad": {
        "budget": {
            "url": "https://ahmedabadcity.gov.in/SP/Budget",
            "keywords": ("budget",),
            "dir": "budget",
        },
        "balance-sheet": {
            "url": "https://ahmedabadcity.gov.in/SP/BalanceSheet",
            "keywords": ("balance sheet", "audit report", "account"),
            "dir": "balance_sheet",
        },
    },
}


@dataclass(frozen=True)
class FinanceBookLink:
    kind: str
    year: str
    label: str
    url: str


def numbers(line: str) -> list[float]:
    """Extract non-zero numeric tokens from an OCR line, translating Gujarati
    digits to ASCII and stripping thousands separators."""
    line = line.translate(GUJARATI_DIGITS)
    values: list[float] = []
    for token in re.findall(r"-?\d[\d,]*\.?\d*", line):
        try:
            value = float(token.replace(",", ""))
        except ValueError:
            continue
        if value != 0:
            values.append(value)
    return values


def parse_ocr_lines(lines: Sequence[str], labels: Mapping[str, str]) -> dict[str, dict[str, object]]:
    """For each labelled budget summary line, return the first matching line's
    numbers + raw text."""
    record: dict[str, dict[str, object]] = {}
    for key, pattern in labels.items():
        for line in lines:
            if re.search(pattern, line):
                values = numbers(line)
                if values:
                    record[key] = {"numbers": values, "raw": line.strip()[:180]}
                    break
    return record


def budget_columns(labels: Mapping[str, str]) -> list[str]:
    columns = ["year"]
    columns.extend(f"{key}_candidates" for key in labels)
    columns.extend(f"{key}_raw" for key in labels)
    return columns


def budget_row(year: str, record: Mapping[str, dict], labels: Mapping[str, str]) -> dict[str, str]:
    row = {"year": year}
    for key in labels:
        value = record.get(key)
        row[f"{key}_candidates"] = "|".join(str(num) for num in value["numbers"]) if value else ""
        row[f"{key}_raw"] = value["raw"] if value else ""
    return row


def parse_year_from_filename(filename: str) -> str | None:
    """Budget year from a PDF filename (e.g. '...2021-22...' or '...21-22...')."""
    match = re.search(r"(20\d{2})[-_ ](\d{2})", filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    match = re.search(r"\b(\d{2})[-_](\d{2})\b", filename)
    if match:
        return f"20{match.group(1)}-{match.group(2)}"
    return None


def finance_link_year(*parts: str) -> str | None:
    """Fiscal year from a finance-book link label/url, handling year ranges and
    31-03-YYYY balance-sheet dates."""
    text = " ".join(parts)
    match = re.search(r"(20\d{2})\s*[-_]\s*(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    match = re.search(r"\b31\s*[-_]\s*03\s*[-_]\s*(20\d{2}|\d{2})\b", text)
    if match:
        end_year = int(match.group(1)) if len(match.group(1)) == 4 else int(f"20{match.group(1)}")
        return f"{end_year - 1}-{str(end_year)[-2:]}"
    match = re.search(r"\b(0[5-9]|1\d|2\d)\s*[-_]\s*(0[6-9]|1\d|2\d|3\d)\b", text)
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        if end == start + 1:
            return f"20{match.group(1)}-{match.group(2)}"
    return None


def finance_book_filename(city: str, link: FinanceBookLink, seen: set[str]) -> str:
    kind = re.sub(r"[^a-z0-9]+", "-", link.kind.lower()).strip("-")
    slug = re.sub(r"[^a-z0-9]+", "-", link.label.lower()).strip("-") or kind
    name = f"{city}_{kind}_{link.year}_{slug}.pdf"
    base = name
    index = 2
    while name in seen:
        name = base.replace(".pdf", f"_{index}.pdf")
        index += 1
    seen.add(name)
    return name


def count_numeric_tokens(text: str, min_digits: int = 3) -> int:
    """Count numeric tokens (ASCII or Gujarati) of at least `min_digits`."""
    return len(re.findall(rf"[0-9૦-૯]{{{min_digits},}}", text))


def count_ascii_numbers(text: str, min_digits: int = 3) -> int:
    return len(re.findall(rf"\d{{{min_digits},}}", text))


def select_dense_pages(scored: Sequence[tuple[int, int]], top_pages: int, min_numbers: int) -> list[int]:
    """From (page, numeric-token-count) pairs, keep the densest `top_pages` pages
    that clear `min_numbers`, returned in page order."""
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    return sorted(page for page, count in ranked[:top_pages] if count >= min_numbers)
