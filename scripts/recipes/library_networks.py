from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


class PlainTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def fetch_bytes(url: str, user_agent: str = "The Unelected City library-network extractor") -> bytes:
    request = Request(url, headers={"User-Agent": user_agent})
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


def parse_js_object(path: Path, global_name: str) -> dict[str, dict[str, str]]:
    node = shutil.which("node")
    if not node:
        sys.exit("node is required to parse JavaScript content sources safely")
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", global_name):
        raise ValueError(f"invalid JavaScript global name: {global_name!r}")

    script = f"""
const fs = require('fs');
const vm = require('vm');
const sandbox = {{}};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8') + '\\nthis.__payload = {global_name};', sandbox);
process.stdout.write(JSON.stringify(sandbox.__payload));
"""
    result = subprocess.run([node, "-e", script, str(path)], check=True, capture_output=True, text=True)
    parsed = json.loads(result.stdout)
    return {str(key): value for key, value in sorted(parsed.items(), key=lambda item: natural_key(item[0]))}


def export_pdf_texts(
    pdf_rows: list[dict[str, str]],
    cache_dir: Path,
    text_dir: Path,
    repo_root: Path,
    *,
    category: str,
    no_download: bool,
    user_agent: str,
) -> list[dict[str, str]]:
    text_dir.mkdir(parents=True, exist_ok=True)
    by_year: dict[str, dict[str, str]] = {}
    for row in pdf_rows:
        if row["category"] == category and row["year"]:
            by_year.setdefault(row["year"], row)

    rows = []
    for year, row in sorted(by_year.items()):
        pdf_path = cache_dir / f"{year}.pdf"
        if not pdf_path.exists():
            if no_download:
                raise FileNotFoundError(f"missing cached PDF for {year}: {pdf_path}")
            pdf_path.write_bytes(fetch_bytes(row["url"], user_agent=user_agent))

        text_path = text_dir / f"{year}.txt"
        run_pdftotext(pdf_path, text_path)
        text = text_path.read_text(encoding="utf-8", errors="ignore")
        pages = pdf_pages(pdf_path)
        rel_text_path = text_path.relative_to(repo_root) if text_path.is_relative_to(repo_root) else text_path
        rows.append(
            {
                "year": year,
                "source_url": row["url"],
                "text_path": str(rel_text_path),
                "pdf_sha256": sha256(pdf_path),
                "pages": str(pages),
                "text_chars": str(len(text)),
                "text_lines": str(len(text.splitlines())),
                "extraction_method": "pdftotext -layout",
                "confidence": "medium",
                "notes": "Full disclosure text export; key numeric tables are separately curated/manual-checked in CSV files.",
            }
        )
    return rows


def run_pdftotext(pdf_path: Path, text_path: Path) -> None:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        sys.exit("pdftotext is required to extract disclosure text")
    subprocess.run([pdftotext, "-layout", str(pdf_path), str(text_path)], check=True)


def pdf_pages(pdf_path: Path) -> int:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        return 0
    result = subprocess.run([pdfinfo, str(pdf_path)], check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    return 0


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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
