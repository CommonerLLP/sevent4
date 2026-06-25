from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

CONTENT_JS_URL = "https://mjlibrary.in/assets/frontend/en-lang/content.js"
ABOUT_URL = "https://mjlibrary.in/about-us"


def _natural_key(value: str) -> list:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


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
    return {str(key): value for key, value in sorted(parsed.items(), key=lambda item: _natural_key(item[0]))}


class MjLibraryStore:
    """All filesystem/network/subprocess IO for the M.J. Library enrichment:
    curl fetch, pdftotext (layout + TSV), pdftoppm, tesseract, hashing, CSV out."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo = Path(repo_root)
        self.out_dir = self.repo / "data" / "cities" / "ahmedabad" / "source" / "libraries"
        self.doc_dir = self.out_dir / "docs"
        self.text_dir = self.out_dir / "docs_text"
        self.image_dir = self.out_dir / "page_images"
        self.cache_dir = Path("/private/tmp/sevent4_mj_library_sources")

    def ensure_dirs(self) -> None:
        for directory in (self.doc_dir, self.text_dir, self.image_dir, self.cache_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def fetch(self, url: str, dest: Path) -> None:
        curl = shutil.which("curl")
        if not curl:
            sys.exit("curl is required")
        subprocess.run([curl, "-L", "--fail", "--silent", "--show-error", "-o", str(dest), url], check=True)

    def parse_content_js(self) -> dict:
        content_js = self.cache_dir / "content.js"
        self.fetch(CONTENT_JS_URL, content_js)
        return parse_js_object(content_js, "content")

    def fetch_about(self) -> None:
        self.fetch(ABOUT_URL, self.cache_dir / "about-us.html")

    def export_text(self, pdf_path: Path, text_path: Path) -> str:
        pdftotext = shutil.which("pdftotext")
        if not pdftotext:
            return "not_available"
        subprocess.run([pdftotext, "-layout", str(pdf_path), str(text_path)], check=True)
        text = Path(text_path).read_text(encoding="utf-8", errors="ignore")
        return "pdftotext -layout" if len(text.strip()) > 50 else "pdftotext minimal_or_image_only"

    def render_page(self, pdf_path: Path, page: int, image_path: Path) -> None:
        pdftoppm = shutil.which("pdftoppm")
        if not pdftoppm:
            return
        prefix = Path(image_path).with_suffix("")
        subprocess.run(
            [pdftoppm, "-r", "300", "-png", "-f", str(page), "-l", str(page), str(pdf_path), str(prefix)],
            check=True,
        )
        generated = prefix.with_name(f"{prefix.name}-{page}").with_suffix(".png")
        if generated.exists() and generated != Path(image_path):
            generated.replace(image_path)

    def ocr_image(self, image_path: Path, text_path: Path, lang: str) -> None:
        tesseract = shutil.which("tesseract")
        if not tesseract or not Path(image_path).exists():
            return
        outbase = Path(text_path).with_suffix("")
        subprocess.run([tesseract, str(image_path), str(outbase), "-l", lang, "--psm", "6"], check=True)

    def pdf_pages(self, pdf_path: Path) -> int:
        pdfinfo = shutil.which("pdfinfo")
        if not pdfinfo:
            return 0
        result = subprocess.run([pdfinfo, str(pdf_path)], check=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1].strip())
        return 0

    def pdf_words(self, pdf_path: Path) -> list[dict]:
        pdftotext = shutil.which("pdftotext")
        if not pdftotext:
            return []
        tsv_path = self.cache_dir / f"{Path(pdf_path).stem}.tsv"
        subprocess.run([pdftotext, "-tsv", str(pdf_path), str(tsv_path)], check=True)
        rows: list[dict] = []
        with tsv_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row.get("level") != "5":
                    continue
                text = row.get("text", "").strip()
                if not text or text == "###PAGE###":
                    continue
                rows.append({"page": int(row["page_num"]), "left": float(row["left"]),
                             "top": float(row["top"]), "text": text})
        return sorted(rows, key=lambda row: (row["page"], row["top"], row["left"]))

    def sha256(self, pdf_path: Path) -> str:
        digest = hashlib.sha256()
        with Path(pdf_path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def rel(self, path: Path) -> str:
        return str(Path(path).relative_to(self.repo))

    def write_csv(self, name: str, rows: list[dict]) -> None:
        if not rows:
            return
        path = self.out_dir / name
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def doc_path(self, name: str) -> Path:
        return self.doc_dir / name

    def text_path(self, stem: str) -> Path:
        return self.text_dir / f"{stem}.txt"

    def image_path(self, name: str) -> Path:
        return self.image_dir / name
