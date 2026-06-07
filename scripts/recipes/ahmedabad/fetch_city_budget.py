#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen


REPO = Path(__file__).resolve().parents[3]

# Ahmedabad is the first implemented finance-book fetch adapter. Other cities
# publish budgets and accounts differently, so add city adapters over time.
DEFAULT_CITY = "ahmedabad"

CITY_FINANCE_PAGES = {
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


class FinanceBookParser(HTMLParser):
    def __init__(self, page_url: str, keywords: tuple[str, ...]) -> None:
        super().__init__()
        self.page_url = page_url
        self.keywords = keywords
        self._href: str | None = None
        self._text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._href:
            return
        label = " ".join("".join(self._text).split())
        href = self._href
        haystack = f"{label} {href}".lower()
        if any(keyword in haystack for keyword in self.keywords) and (".pdf" in haystack or "viewfile" in haystack):
            self.links.append((label, urljoin(self.page_url, href)))
        self._href = None
        self._text = []


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch city finance-book PDFs from public municipal sources.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Ahmedabad is implemented first.")
    parser.add_argument("--kind", default="budget", choices=["budget", "balance-sheet", "all"], help="Finance-book kind.")
    parser.add_argument("--page-url", help="Override source page URL. Only valid with one --kind.")
    parser.add_argument("--out-dir", help="PDF output directory. Only recommended with one --kind.")
    parser.add_argument("--manifest", help="JSON manifest output path. Only recommended with one --kind.")
    parser.add_argument("--dry-run", action="store_true", help="List discovered PDFs without downloading.")
    args = parser.parse_args()

    city = args.city.lower()
    configs = CITY_FINANCE_PAGES.get(city)
    if not configs:
        sys.exit(
            f"No finance-book fetch adapter for city={city!r}. "
            "Put PDFs under data/cities/<city>/source/budget/pdfs/ or add an adapter."
        )

    if args.kind == "all":
        if args.page_url:
            sys.exit("--page-url is only valid when --kind is budget or balance-sheet")
        kinds = list(configs)
    else:
        kinds = [args.kind]

    all_rows = []
    for kind in kinds:
        config = configs.get(kind)
        if not config:
            sys.exit(f"No {kind} fetch adapter for city={city!r}")

        page_url = args.page_url or str(config["url"])
        source_dir = str(config["dir"])
        out_dir = (
            Path(args.out_dir)
            if args.out_dir and len(kinds) == 1
            else REPO / "data" / "cities" / city / "source" / source_dir / "pdfs"
        )
        manifest = (
            Path(args.manifest)
            if args.manifest and len(kinds) == 1
            else REPO / "data" / "cities" / city / "source" / source_dir / f"{source_dir}_sources.json"
        )

        links = discover_finance_links(kind, page_url, tuple(config["keywords"]))
        if not links:
            sys.exit(f"No {kind} links discovered at {page_url}")

        if not args.dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
            manifest.parent.mkdir(parents=True, exist_ok=True)

        rows = []
        seen_names: set[str] = set()
        for link in links:
            filename = _filename(city, link, seen_names)
            out_path = out_dir / filename
            row = {
                "city": city,
                "kind": kind,
                "year": link.year,
                "label": link.label,
                "url": link.url,
                "path": str(out_path.relative_to(REPO)),
            }
            if args.dry_run:
                print(f"{kind}\t{link.year}\t{link.label}\t{link.url}")
            else:
                download(link.url, out_path)
                print(f"wrote {out_path}")
            rows.append(row)
            all_rows.append(row)

        if not args.dry_run:
            manifest.write_text(json.dumps({"city": city, "kind": kind, "source_page": page_url, "items": rows}, indent=2), encoding="utf-8")
            print(f"wrote {manifest}")

    if len(kinds) > 1:
        print(f"discovered {len(all_rows)} finance-book links across {len(kinds)} source pages")


def discover_finance_links(kind: str, page_url: str, keywords: tuple[str, ...]) -> list[FinanceBookLink]:
    html = _fetch_text(page_url)
    parser = FinanceBookParser(page_url, keywords)
    parser.feed(html)
    links: list[FinanceBookLink] = []
    seen: set[tuple[str, str]] = set()
    for label, url in parser.links:
        year = _year(label, url)
        if not year:
            continue
        key = (year, url)
        if key in seen:
            continue
        seen.add(key)
        links.append(FinanceBookLink(kind=kind, year=year, label=label or f"{kind} {year}", url=url))
    return sorted(links, key=lambda item: item.year, reverse=True)


def download(url: str, out_path: Path) -> None:
    out_path.write_bytes(_fetch_bytes(url))


def _fetch_text(url: str) -> str:
    return _fetch_bytes(url).decode("utf-8", errors="ignore")


def _fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "SevenT4 city finance-book fetcher"})
    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except Exception as exc:
        curl = shutil.which("curl")
        if not curl:
            raise
        result = subprocess.run(
            [curl, "-L", "--fail", "--silent", "--show-error", url],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            return result.stdout
        raise RuntimeError(result.stderr.decode("utf-8", errors="ignore").strip() or str(exc)) from exc


def _year(*parts: str) -> str | None:
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


def _filename(city: str, link: FinanceBookLink, seen: set[str]) -> str:
    kind = re.sub(r"[^a-z0-9]+", "-", link.kind.lower()).strip("-")
    slug = re.sub(r"[^a-z0-9]+", "-", link.label.lower()).strip("-") or kind
    name = f"{city}_{kind}_{link.year}_{slug}.pdf"
    base = name
    i = 2
    while name in seen:
        name = base.replace(".pdf", f"_{i}.pdf")
        i += 1
    seen.add(name)
    return name


if __name__ == "__main__":
    main()
