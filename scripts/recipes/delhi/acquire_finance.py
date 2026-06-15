#!/usr/bin/env python3
"""Acquire Delhi GNCTD and MCD budget document manifests.

This is a source-first acquisition helper. It discovers official document URLs,
writes provenance-rich manifests, and optionally downloads PDFs. Network access
is sequential and can be routed through a local SOCKS proxy, for example:

    PYTHONPATH=. python3 scripts/recipes/delhi/acquire_finance.py \
      --scope all --socks 127.0.0.1:1080 --download

No EC2 host details are stored here. If a SOCKS proxy is used, it is supplied by
the caller as a local endpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = ROOT / "data" / "cities" / "delhi" / "source" / "budget"

FINANCE_BASE = "https://finance.delhi.gov.in"
GNCTD_PAGES = {
    "budget_at_a_glance": f"{FINANCE_BASE}/finance/budget-glance",
    "receipts_budget": f"{FINANCE_BASE}/finance/receipts-budget",
    "budget_speech": f"{FINANCE_BASE}/finance/budget-speech",
    "gender_budget": f"{FINANCE_BASE}/finance/gender-budget",
}
DETAILED_DEMANDS_INDEX = f"{FINANCE_BASE}/finance/detailed-demands-grants-0"
LEGACY_DELHI_BUDGET_URLS = [
    "https://delhi.gov.in/wps/wcm/connect/lib_finance/Finance/Home/Budget",
    "https://delhi.gov.in/wps/wcm/connect/lib_finance/Finance/Home/Budget/Budget+2017_18",
]

MCD_BASE = "https://mcdonline.nic.in"
MCD_FINANCE_MENU_GUIDE = "914bf40f-81d3-4ae4-91c0-202a64bfa925"
MCD_PARENT_MENU_GUIDE = "561ea9dd-8ddb-46cf-b19f-a3eabd02903f"
MCD_SEED_URLS = [
    f"{MCD_BASE}/portal/officialLink",
    f"{MCD_BASE}/portal/showSubMenu?menuguide={MCD_FINANCE_MENU_GUIDE}",
    f"{MCD_BASE}/portal/showContent?menuguide={MCD_FINANCE_MENU_GUIDE}",
    f"{MCD_BASE}/portal/showPDFContent?menuguide={MCD_FINANCE_MENU_GUIDE}",
    f"{MCD_BASE}/portal/showSubMenu?menuguide={MCD_PARENT_MENU_GUIDE}",
]

USER_AGENT = (
    "sevent4-atlas/0.1 "
    "(+https://github.com/CommonerLLP/sevent4; public-interest research)"
)
TOOL_NAME = "scripts/recipes/delhi/acquire_finance.py"

FISCAL_YEAR_RE = re.compile(r"(?<!\d)(20\d{2})[-_/](\d{2,4})(?!\d)")
DETAIL_PAGE_RE = re.compile(r"/finance/detailed-demands-grants-[0-9]{4}-[0-9]{2}(?:-voa)?")
PDF_RE = re.compile(r"\.pdf(?:$|[?#])", re.I)
BUDGETISH_RE = re.compile(
    r"\b(budget|estimate|estimates|grant|grants|receipt|receipts|accounts?|finance|annual\s+account)\b",
    re.I,
)
URL_BUDGETISH_RE = re.compile(r"(budget|receipt|demand|grant|ddg|bag|gender|speech)", re.I)
MCD_BUDGET_RE = re.compile(
    r"\b(budget|estimate|estimates|grant|grants|receipt|receipts|rbe|be|income|expenditure)\b",
    re.I,
)


@dataclass(frozen=True)
class BudgetDocument:
    government: str
    document_type: str
    fiscal_year: str | None
    title: str
    url: str
    source_page: str
    local_path: str | None = None
    sha256: str | None = None
    status: str = "discovered"


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._text: list[str] = []
        self._in_title = False
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True
            return
        if tag.lower() != "a":
            return
        attr = {k.lower(): v or "" for k, v in attrs}
        self._current = {
            "href": attr.get("href", ""),
            "title": attr.get("title", ""),
        }
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._current is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
            return
        if tag.lower() == "a" and self._current is not None:
            self._current["text"] = clean_text(" ".join(self._text))
            self.anchors.append(self._current)
            self._current = None
            self._text = []

    @property
    def page_title(self) -> str:
        return clean_text(" ".join(self.title_parts))


class _LegacyDelhiParser(HTMLParser):
    """Python 3 port of the old CBGA Delhi crawler's HTML walk.

    The old scraper followed anchors inside ``td.subheading`` and downloaded the
    first PDF exposed through an ``iframe src`` on the child page. This parser
    extracts both structures without depending on lxml or Python 2 imports.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pages: list[dict[str, str]] = []
        self.iframes: list[str] = []
        self._td_subheading_depth = 0
        self._current_subheading_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = {k.lower(): v or "" for k, v in attrs}
        if tag == "td":
            classes = set(attr.get("class", "").lower().split())
            if "subheading" in classes:
                self._td_subheading_depth += 1
        elif tag == "a" and self._td_subheading_depth:
            self._current_subheading_href = attr.get("href", "")
            self._current_text = []
        elif tag == "iframe":
            src = attr.get("src", "")
            if src:
                self.iframes.append(src)

    def handle_data(self, data: str) -> None:
        if self._current_subheading_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._current_subheading_href is not None:
            title = clean_text(" ".join(self._current_text))
            if title and self._current_subheading_href:
                self.pages.append({"title": title, "href": self._current_subheading_href})
            self._current_subheading_href = None
            self._current_text = []
        elif tag == "td" and self._td_subheading_depth:
            self._td_subheading_depth -= 1


def clean_text(value: str | None) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def fiscal_year_from_text(value: str | None) -> str | None:
    if not value:
        return None
    candidates: list[tuple[int, str]] = []
    for match in FISCAL_YEAR_RE.finditer(value):
        start, end = match.groups()
        end_year = int(end) if len(end) == 4 else int(f"20{end}")
        if end_year == int(start) + 1:
            candidates.append((match.start(), f"{start}-{end[-2:]}"))
    for short_match in re.finditer(r"(?<!\d)([1-2]\d)[-_/]([1-3]\d)(?!\d)", value):
        start, end = (int(part) for part in short_match.groups())
        if end == start + 1:
            candidates.append((short_match.start(), f"20{start:02d}-{end:02d}"))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0])[0][1]


def _html_anchors(page_html: str) -> tuple[list[dict[str, str]], str]:
    parser = _AnchorParser()
    parser.feed(page_html)
    return parser.anchors, parser.page_title


def _is_pdf_url(url: str) -> bool:
    return bool(PDF_RE.search(urlparse(url).path))


def _looks_like_budget_doc(title: str, url: str, document_type: str) -> bool:
    haystack = f"{title} {url} {document_type}".replace("_", " ")
    return bool(BUDGETISH_RE.search(haystack))


def _url_looks_like_budget_doc(url: str) -> bool:
    return bool(URL_BUDGETISH_RE.search(urlparse(url).path))


def extract_finance_pdf_links(
    page_html: str,
    source_url: str,
    document_type: str,
) -> list[dict[str, str | None]]:
    """Extract GNCTD Finance PDF links from one official listing/detail page."""
    anchors, page_title = _html_anchors(page_html)
    docs: list[dict[str, str | None]] = []
    seen: set[str] = set()

    for anchor in anchors:
        href = anchor.get("href", "")
        if not href:
            continue
        url = urljoin(source_url, href)
        if not _is_pdf_url(url):
            continue

        title = clean_text(anchor.get("title")) or clean_text(anchor.get("text"))
        if title.lower() in {"download", "view"}:
            title = ""
        fallback_title = page_title if fiscal_year_from_text(page_title) else ""
        used_fallback_title = not title and bool(fallback_title)
        doc_title = title or fallback_title
        if used_fallback_title and not _url_looks_like_budget_doc(url):
            continue
        fy = fiscal_year_from_text(doc_title)

        # Only fall back to the filename year when the filename itself looks like
        # a budget document. This avoids unrelated dated PDFs in site chrome.
        if fy is None and _url_looks_like_budget_doc(url):
            fy = fiscal_year_from_text(urlparse(url).path)
        if fy is None:
            continue
        if not doc_title:
            doc_title = f"{document_type.replace('_', ' ').title()} {fy}"
        if not _looks_like_budget_doc(doc_title, url, ""):
            continue
        if url in seen:
            continue

        seen.add(url)
        docs.append(
            {
                "government": "Government of NCT of Delhi",
                "document_type": document_type,
                "fiscal_year": fy,
                "title": doc_title,
                "url": url,
                "source_page": source_url,
            }
        )

    return docs


def extract_detail_page_links(page_html: str, source_url: str) -> list[dict[str, str | None]]:
    """Extract detailed-demand intermediate pages from the GNCTD index."""
    anchors, _ = _html_anchors(page_html)
    pages: list[dict[str, str | None]] = []
    seen: set[str] = set()

    for anchor in anchors:
        href = anchor.get("href", "")
        if not href or not DETAIL_PAGE_RE.search(href):
            continue
        url = urljoin(source_url, href)
        if url in seen:
            continue
        seen.add(url)
        fy = fiscal_year_from_text(url)
        suffix = " VOA" if url.lower().endswith("-voa") else ""
        pages.append(
            {
                "fiscal_year": fy,
                "title": f"Detailed Demands for Grants {fy}{suffix}".strip(),
                "url": url,
                "source_page": source_url,
            }
        )

    return pages


def extract_legacy_delhi_budget_refs(
    page_html: str,
    source_url: str,
    title_hint: str | None = None,
) -> dict[str, list[dict[str, str | None]]]:
    """Extract old delhi.gov.in budget crawl refs from subheading links/iframes.

    This is the Python 3 version of budget-crawler's old CBGA Delhi scraper:
    ``td.subheading/a`` links are child pages; ``iframe/@src`` points to the
    downloadable PDF on a detail page.
    """
    parser = _LegacyDelhiParser()
    parser.feed(page_html)

    pages: list[dict[str, str | None]] = []
    seen_pages: set[str] = set()
    for ref in parser.pages:
        url = urljoin(source_url, ref["href"])
        title = ref["title"]
        haystack = f"{title} {url}"
        if not BUDGETISH_RE.search(haystack):
            continue
        if url == source_url or url in seen_pages:
            continue
        seen_pages.add(url)
        pages.append({"title": title, "url": url})

    docs: list[dict[str, str | None]] = []
    seen_docs: set[str] = set()
    for href in parser.iframes:
        url = urljoin(source_url, href)
        if not _is_pdf_url(url):
            continue
        title = clean_text(title_hint) or "Legacy Delhi Budget"
        fy = fiscal_year_from_text(f"{title} {url}")
        if fy is None:
            continue
        if url in seen_docs:
            continue
        seen_docs.add(url)
        docs.append(
            {
                "government": "Government of NCT of Delhi",
                "document_type": "legacy_delhi_budget",
                "fiscal_year": fy,
                "title": title if fiscal_year_from_text(title) else f"{title} {fy}",
                "url": url,
                "source_page": source_url,
            }
        )

    return {"pages": pages, "documents": docs}


def extract_mcd_budget_entries(payload: str, source_url: str) -> list[dict[str, str | None]]:
    """Extract likely public MCD budget/finance document links from JSON or HTML."""
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return _extract_mcd_from_html(payload, source_url)

    docs: list[dict[str, str | None]] = []
    seen: set[str] = set()

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            title = _first_text(
                obj,
                "menuName",
                "documentName",
                "docName",
                "title",
                "name",
                "label",
                "subject",
            )
            href = _first_text(
                obj,
                "pdfPath",
                "filePath",
                "documentPath",
                "downloadUrl",
                "url",
                "href",
                "link",
            )
            if href and title:
                _append_mcd_doc(docs, seen, title, href, source_url)
            for value in obj.values():
                if _string_contains_html(value):
                    for row in _extract_mcd_from_html(value, source_url):
                        key = str(row["url"])
                        if key not in seen:
                            seen.add(key)
                            docs.append(row)
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(parsed)
    return docs


def extract_mcd_menu_guides(payload: str) -> list[dict[str, str]]:
    """Extract child MCD menu guides worth crawling from JSON menu payloads."""
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return []

    guides: list[dict[str, str]] = []
    seen: set[str] = set()

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            title = _first_text(obj, "menuName", "title", "name", "label")
            menu_guide = _first_text(obj, "menuGuide", "menuGuid", "guide")
            if title and menu_guide and BUDGETISH_RE.search(title):
                if menu_guide not in seen:
                    seen.add(menu_guide)
                    guides.append({"title": title, "menu_guide": menu_guide})
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(parsed)
    return guides


def _extract_mcd_from_html(page_html: str, source_url: str) -> list[dict[str, str | None]]:
    anchors, _ = _html_anchors(page_html)
    docs: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for anchor in anchors:
        title = clean_text(anchor.get("title")) or clean_text(anchor.get("text"))
        href = anchor.get("href", "")
        if title and href:
            _append_mcd_doc(docs, seen, title, href, source_url)
    return docs


def _string_contains_html(value: Any) -> bool:
    return isinstance(value, str) and "<" in value and ">" in value


def _append_mcd_doc(
    docs: list[dict[str, str | None]],
    seen: set[str],
    title: str,
    href: str,
    source_url: str,
) -> None:
    url = urljoin(source_url, href)
    leaf = f"{title} {urlparse(url).path}".replace("_", "-")
    if not MCD_BUDGET_RE.search(leaf):
        return
    if not (_is_pdf_url(url) or "download" in url.lower() or "showpdf" in url.lower()):
        return
    if url in seen:
        return
    seen.add(url)
    docs.append(
        {
            "government": "Municipal Corporation of Delhi",
            "document_type": "mcd_budget",
            "fiscal_year": fiscal_year_from_text(leaf),
            "title": clean_text(title),
            "url": url,
            "source_page": source_url,
        }
    )


def _first_text(obj: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return clean_text(value)
    return ""


def discover_gnctd(socks: str | None = None, delay_sec: float = 1.0) -> list[BudgetDocument]:
    docs: list[BudgetDocument] = []
    for document_type, url in GNCTD_PAGES.items():
        page = fetch_text(url, socks=socks)
        docs.extend(_to_docs(extract_finance_pdf_links(page, url, document_type)))
        time.sleep(delay_sec)

    index = fetch_text(DETAILED_DEMANDS_INDEX, socks=socks)
    for detail_page in extract_detail_page_links(index, DETAILED_DEMANDS_INDEX):
        page_url = str(detail_page["url"])
        page = fetch_text(page_url, socks=socks)
        docs.extend(
            _to_docs(
                extract_finance_pdf_links(
                    page,
                    page_url,
                    "detailed_demands_for_grants",
                )
            )
        )
        time.sleep(delay_sec)

    return _dedupe_docs(docs)


def discover_legacy_delhi(
    start_urls: list[str] | None = None,
    socks: str | None = None,
    delay_sec: float = 1.0,
    max_pages: int = 80,
) -> list[BudgetDocument]:
    queue = list(start_urls or LEGACY_DELHI_BUDGET_URLS)
    seen_pages: set[str] = set()
    docs: list[BudgetDocument] = []

    while queue and len(seen_pages) < max_pages:
        url = queue.pop(0)
        if url in seen_pages:
            continue
        seen_pages.add(url)
        try:
            page = fetch_text(url, socks=socks)
        except RuntimeError as exc:
            docs.append(
                BudgetDocument(
                    government="Government of NCT of Delhi",
                    document_type="legacy_discovery_error",
                    fiscal_year=None,
                    title=f"Legacy discovery failed: {type(exc).__name__}",
                    url=url,
                    source_page=url,
                    status=str(exc),
                )
            )
            continue
        refs = extract_legacy_delhi_budget_refs(page, url)
        docs.extend(_to_docs(refs["documents"]))
        for page_ref in refs["pages"]:
            page_url = str(page_ref["url"])
            if page_url not in seen_pages and page_url not in queue:
                queue.append(page_url)
        time.sleep(delay_sec)

    return _dedupe_docs(docs)


def discover_mcd(
    socks: str | None = None,
    delay_sec: float = 1.0,
    max_menu_guides: int = 40,
) -> list[BudgetDocument]:
    docs: list[BudgetDocument] = []
    queue = list(MCD_SEED_URLS)
    seen_urls: set[str] = set()
    seen_guides: set[str] = {MCD_FINANCE_MENU_GUIDE, MCD_PARENT_MENU_GUIDE}

    while queue and len(seen_urls) < max_menu_guides * 3:
        url = queue.pop(0)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            payload = fetch_text(url, socks=socks)
        except RuntimeError as exc:
            docs.append(
                BudgetDocument(
                    government="Municipal Corporation of Delhi",
                    document_type="mcd_discovery_error",
                    fiscal_year=None,
                    title=f"Discovery failed: {type(exc).__name__}",
                    url=url,
                    source_page=url,
                    status=str(exc),
                )
            )
            continue
        docs.extend(_to_docs(extract_mcd_budget_entries(payload, url)))
        for guide in extract_mcd_menu_guides(payload):
            menu_guide = guide["menu_guide"]
            if menu_guide in seen_guides:
                continue
            seen_guides.add(menu_guide)
            queue.extend(
                [
                    f"{MCD_BASE}/portal/showSubMenu?menuguide={menu_guide}",
                    f"{MCD_BASE}/portal/showContent?menuguide={menu_guide}",
                    f"{MCD_BASE}/portal/showPDFContent?menuguide={menu_guide}",
                ]
            )
        time.sleep(delay_sec)
    return _dedupe_docs(docs)


def fetch_text(url: str, socks: str | None = None, timeout_sec: int = 90) -> str:
    cmd = _curl_cmd(url, socks=socks, timeout_sec=timeout_sec)
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed for {url}: {result.stderr.strip()}")
    return result.stdout


def download_file(url: str, dest: Path, socks: str | None = None, timeout_sec: int = 180) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = _curl_cmd(url, socks=socks, timeout_sec=timeout_sec) + ["--output", str(dest)]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed for {url}: {result.stderr.strip()}")


def _curl_cmd(url: str, socks: str | None, timeout_sec: int) -> list[str]:
    cmd = [
        "curl",
        "-fsSL",
        "--max-time",
        str(timeout_sec),
        "--retry",
        "2",
        "--retry-delay",
        "2",
        "-A",
        USER_AGENT,
    ]
    if socks:
        cmd.extend(["--socks5-hostname", socks])
    cmd.append(_encode_url_path(url))
    return cmd


def _encode_url_path(url: str) -> str:
    parts = urlsplit(url)
    encoded_path = quote(parts.path, safe="/%+")
    encoded_query = quote(parts.query, safe="=&%+")
    return urlunsplit((parts.scheme, parts.netloc, encoded_path, encoded_query, parts.fragment))


def _to_docs(rows: list[dict[str, str | None]]) -> list[BudgetDocument]:
    return [BudgetDocument(**row) for row in rows]


def _dedupe_docs(docs: list[BudgetDocument]) -> list[BudgetDocument]:
    seen: set[tuple[str, str]] = set()
    out: list[BudgetDocument] = []
    for doc in docs:
        key = (doc.government, doc.url)
        if key in seen:
            continue
        seen.add(key)
        out.append(doc)
    return sorted(out, key=lambda d: (d.government, d.document_type, d.fiscal_year or "", d.title))


def safe_filename(doc: BudgetDocument) -> str:
    bits = [doc.government, doc.document_type, doc.fiscal_year or "unknown", doc.title]
    name = "_".join(bit for bit in bits if bit)
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    name = re.sub(r"_+", "_", name)
    suffix = ".pdf"
    if name.lower().endswith(suffix):
        name = name[: -len(suffix)]
    return f"{name[: 180 - len(suffix)].rstrip('._')}{suffix}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(path: Path, docs: list[BudgetDocument], scope: str) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scope": scope,
        "sources": {
            "gnctd_finance_pages": GNCTD_PAGES,
            "gnctd_detailed_demands_index": DETAILED_DEMANDS_INDEX,
            "legacy_delhi_budget_urls": LEGACY_DELHI_BUDGET_URLS,
            "mcd_seed_urls": MCD_SEED_URLS,
        },
        "documents": [asdict(doc) for doc in docs],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def append_runlog(path: Path, *, scope: str, docs: list[BudgetDocument], started_at: str) -> None:
    statuses: dict[str, int] = {}
    for doc in docs:
        statuses[doc.status] = statuses.get(doc.status, 0) + 1
    record = {
        "run_id": hashlib.sha256(f"{started_at}:{scope}:{len(docs)}".encode()).hexdigest()[:16],
        "tool": TOOL_NAME,
        "scope": scope,
        "started_at": started_at,
        "ended_at": datetime.now().isoformat(timespec="seconds"),
        "documents": len(docs),
        "statuses": statuses,
        "sources": {
            "gnctd_finance_pages": list(GNCTD_PAGES.values()) if scope in {"gnctd", "all"} else [],
            "legacy_delhi_budget_urls": LEGACY_DELHI_BUDGET_URLS if scope in {"legacy", "all"} else [],
            "mcd_seed_urls": MCD_SEED_URLS if scope in {"mcd", "all"} else [],
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["gnctd", "legacy", "mcd", "all"], default="all")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--socks", help="Local SOCKS endpoint, e.g. 127.0.0.1:1080")
    parser.add_argument("--download", action="store_true", help="Download discovered PDFs")
    parser.add_argument("--delay-sec", type=float, default=1.0)
    args = parser.parse_args()

    started_at = datetime.now().isoformat(timespec="seconds")
    docs: list[BudgetDocument] = []
    if args.scope in {"gnctd", "all"}:
        docs.extend(discover_gnctd(socks=args.socks, delay_sec=args.delay_sec))
    if args.scope in {"legacy", "all"}:
        docs.extend(discover_legacy_delhi(socks=args.socks, delay_sec=args.delay_sec))
    if args.scope in {"mcd", "all"}:
        docs.extend(discover_mcd(socks=args.socks, delay_sec=args.delay_sec))
    docs = _dedupe_docs(docs)

    if args.download:
        updated: list[BudgetDocument] = []
        for doc in docs:
            if not _is_pdf_url(doc.url):
                updated.append(doc)
                continue
            group = "gnctd" if doc.government.startswith("Government") else "mcd"
            dest = args.out / group / "pdfs" / safe_filename(doc)
            try:
                if not dest.exists() or dest.stat().st_size <= 1000:
                    download_file(doc.url, dest, socks=args.socks)
                updated.append(
                    BudgetDocument(
                        **{
                            **asdict(doc),
                            "local_path": str(dest.relative_to(args.out)),
                            "sha256": sha256_file(dest),
                            "status": "downloaded",
                        }
                    )
                )
            except RuntimeError as exc:
                updated.append(BudgetDocument(**{**asdict(doc), "status": str(exc)}))
            time.sleep(args.delay_sec)
        docs = updated

    manifest = args.out / f"delhi_finance_{args.scope}_manifest.json"
    write_manifest(manifest, docs, args.scope)
    append_runlog(args.out / "_runs.jsonl", scope=args.scope, docs=docs, started_at=started_at)
    print(f"[delhi-finance] {len(docs)} records -> {manifest}", file=sys.stderr)


if __name__ == "__main__":
    main()
