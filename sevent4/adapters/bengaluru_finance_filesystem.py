"""Filesystem adapter for Bengaluru work-order finance recipes."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path(os.environ.get("OPENCITY_ARCHIVE", str(ROOT / "data" / "sources" / "opencity")))
RAW = ARCHIVE / "bengaluru" / "raw" / "bbmp-work-orders-by-ward-2013-2022"
CITY = ROOT / "data" / "cities" / "bengaluru"
FINANCE_OUT = CITY / "source" / "finance"
LAYERS = CITY / "layers"
BOUNDARY = CITY / "source" / "boundaries" / "wards_bbmp198.geojson"


def read_workorder_file_rows(raw_dir: Path) -> list[tuple[str, list[dict]]]:
    rows = []
    for path in sorted(Path(raw_dir).glob("*.csv")):
        rows.append((str(path), read_workorder_rows(path)))
    return rows


def read_workorder_rows(path: Path) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    header_index = next(
        (index for index, line in enumerate(lines) if "Name of Work" in line or "Job Number" in line),
        0,
    )
    return list(csv.DictReader(lines[header_index:]))


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, data, indent: int | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")


def exists(path: Path) -> bool:
    return Path(path).exists()
