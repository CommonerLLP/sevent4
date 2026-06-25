"""Pure helpers shared by the library-network recipes: HTML-to-text, name/year
normalisation, and small row utilities. No filesystem, network, or subprocess IO
lives here (those are in sevent4.adapters.library_networks_filesystem).
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser


class PlainTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def plain_text(raw: str) -> str:
    parser = PlainTextParser()
    parser.feed(raw.replace("\\", " "))
    return html.unescape(parser.text())


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def natural_key(value: str) -> list[int | str]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def year_from_text(text: str) -> str | None:
    match = re.search(r"(20\d{2})\s*[-_]\s*(20\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)[-2:]}"
    match = re.search(r"(20\d{2})\s*[-_]\s*(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    match = re.search(r"(?<!\d)(20\d{2})(\d{2})(?!\d)", text)
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        if end == (start + 1) % 100:
            return f"{start}-{match.group(2)}"
    return None


def proactive_disclosure_year(prefix: str) -> str | None:
    years = re.findall(r"PRO\s+ACTIVE\s+DISCLOSURE\s+(20\d{2})\s*[-_]\s*(\d{2})", prefix, flags=re.I)
    if not years:
        return None
    start, end = years[-1]
    return f"{start}-{end}"


def one_year(rows: list[dict[str, str]], year: str) -> dict[str, str]:
    for row in rows:
        if row.get("year") == year:
            return row
    raise KeyError(year)


def as_float(value: str) -> float:
    return float(value)


def source_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = row["source_category"]
        counts[key] = counts.get(key, 0) + 1
    return counts


def sorted_js_object(parsed: dict) -> dict[str, dict[str, str]]:
    """Order a parsed JS content object by natural key on its keys."""
    return {str(key): value for key, value in sorted(parsed.items(), key=lambda item: natural_key(item[0]))}
