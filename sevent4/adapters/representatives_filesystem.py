from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen


class RepresentativeDocumentDownloader:
    def download(self, url: str, out_path: str | Path) -> None:
        out_path = Path(out_path)
        request = Request(url, headers={"User-Agent": "The Unelected City city-representative fetcher"})
        try:
            with urlopen(request, timeout=60) as response:
                out_path.write_bytes(response.read())
                return
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
                out_path.write_bytes(result.stdout)
                return
            raise RuntimeError(result.stderr.decode("utf-8", errors="ignore").strip() or str(exc)) from exc


class PdfTextExtractor:
    def extract_text(self, pdf_path: str | Path) -> str:
        result = subprocess.run(
            ["pdftotext", "-raw", str(pdf_path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout


class JsonRepresentativeManifestWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_manifest(self, document: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")


class CsvCouncillorWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_rows(self, rows: list[dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(rows[0]) if rows else []
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            if fieldnames:
                writer.writeheader()
                writer.writerows(rows)


class JsonRepresentativeOfficerWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_officers(self, city: str, officers: list[dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"city": city, "items": officers}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


class WardRepresentativeLayerReader:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def read_document(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def ward_name_from_no(self, ward_no: int) -> str:
        for feature in self.read_document().get("features", []):
            name = str(feature.get("properties", {}).get("Name", ""))
            prefix = name.split(maxsplit=1)[0] if name else ""
            if prefix.isdigit() and int(prefix) == ward_no:
                return name
        return f"{ward_no:02d}"


class WardRepresentativeLayerWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_document(self, document: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
