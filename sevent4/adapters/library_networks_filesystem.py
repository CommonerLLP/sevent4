from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from sevent4.domain.library_networks import sorted_js_object


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
    return sorted_js_object(json.loads(result.stdout))


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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        rows.append({
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
        })
    return rows


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
