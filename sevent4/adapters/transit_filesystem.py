from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from sevent4.ports.transit import GtfsCorridorInput


class FileGtfsCorridorInputRepository:
    def __init__(self, gtfs_dir: str | Path) -> None:
        self.gtfs_dir = Path(gtfs_dir)

    def load(self) -> GtfsCorridorInput:
        return GtfsCorridorInput(
            stops=list(_read_csv(self.gtfs_dir / "stops.txt")),
            routes=list(_read_csv(self.gtfs_dir / "routes.txt")),
            trips=list(_read_csv(self.gtfs_dir / "trips.txt")),
            shapes=list(_read_optional_csv(self.gtfs_dir / "shapes.txt")),
            stop_times=list(_read_optional_csv(self.gtfs_dir / "stop_times.txt")),
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
