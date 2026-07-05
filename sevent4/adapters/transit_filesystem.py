from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Iterable
import zipfile

from sevent4.ports.transit import GtfsCorridorInput


class FileGtfsCorridorInputRepository:
    def __init__(self, gtfs_path: str | Path) -> None:
        self.gtfs_path = Path(gtfs_path)

    def load(self) -> GtfsCorridorInput:
        if self.gtfs_path.is_file():
            return _read_zip_feed(self.gtfs_path)
        return GtfsCorridorInput(
            stops=list(_read_csv(self.gtfs_path / "stops.txt")),
            routes=list(_read_csv(self.gtfs_path / "routes.txt")),
            trips=list(_read_csv(self.gtfs_path / "trips.txt")),
            shapes=list(_read_optional_csv(self.gtfs_path / "shapes.txt")),
            stop_times=list(_read_optional_csv(self.gtfs_path / "stop_times.txt")),
        )


class GeoJsonGtfsCorridorWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_geojson(self, document: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(document, separators=(",", ":")), encoding="utf-8")


class AgencyCorridorWriter:
    """Writes per-agency corridor splits into a layers directory and can drop the
    combined all-routes file."""

    def __init__(self, out_dir: str | Path) -> None:
        self.out_dir = Path(out_dir)

    def write(self, filename: str, document: dict) -> int:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / filename).write_text(
            json.dumps(document, separators=(",", ":")), encoding="utf-8"
        )
        return len(document.get("features", []))

    def remove(self, filename: str) -> None:
        (self.out_dir / filename).unlink(missing_ok=True)


def _read_csv(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


def _read_optional_csv(path: Path) -> Iterable[dict[str, str]]:
    if not path.exists():
        return []
    return _read_csv(path)


def _read_zip_feed(path: Path) -> GtfsCorridorInput:
    with zipfile.ZipFile(path) as zf:
        names = {Path(name).name: name for name in zf.namelist()}
        return GtfsCorridorInput(
            stops=_read_zip_csv(zf, names, "stops.txt"),
            routes=_read_zip_csv(zf, names, "routes.txt"),
            trips=_read_zip_csv(zf, names, "trips.txt"),
            shapes=_read_zip_csv(zf, names, "shapes.txt", required=False),
            stop_times=_read_zip_csv(zf, names, "stop_times.txt", required=False),
        )


def _read_zip_csv(
    zf: zipfile.ZipFile,
    names: dict[str, str],
    filename: str,
    required: bool = True,
) -> list[dict[str, str]]:
    archive_name = names.get(filename)
    if archive_name is None:
        if required:
            raise FileNotFoundError(filename)
        return []
    with zf.open(archive_name) as handle:
        text = io.TextIOWrapper(handle, encoding="utf-8-sig", newline="")
        return list(csv.DictReader(text))
