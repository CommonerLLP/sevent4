from __future__ import annotations

import csv
import json
from pathlib import Path

from sevent4.application.acquisition import INVENTORY_FIELDS
from sevent4.ports.acquisition import AtlasSourceInventory, OpenDataCatalogueInput


class JsonCatalogueRepository:
    def __init__(self, catalogue_path: str | Path, repo_root: str | Path | None = None) -> None:
        self.catalogue_path = Path(catalogue_path)
        self.repo_root = Path(repo_root) if repo_root is not None else None

    def load(self) -> OpenDataCatalogueInput:
        payload = json.loads(self.catalogue_path.read_text(encoding="utf-8"))
        source_catalogue = str(self.catalogue_path)
        if self.repo_root is not None and self.catalogue_path.is_relative_to(self.repo_root):
            source_catalogue = str(self.catalogue_path.relative_to(self.repo_root))
        return OpenDataCatalogueInput(
            source_catalogue=source_catalogue,
            datasets=[dataset for dataset in payload["datasets"]],
        )


class CsvJsonAtlasInventoryWriter:
    def __init__(
        self,
        out_dir: str | Path,
        inventory_filename: str,
        shortlist_filename: str,
        manifest_filename: str,
    ) -> None:
        self.out_dir = Path(out_dir)
        self.inventory_filename = inventory_filename
        self.shortlist_filename = shortlist_filename
        self.manifest_filename = manifest_filename

    def write(self, inventory: AtlasSourceInventory) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        _write_csv(self.out_dir / self.inventory_filename, inventory.inventory_rows)
        _write_csv(self.out_dir / self.shortlist_filename, inventory.shortlist_rows)
        (self.out_dir / self.manifest_filename).write_text(
            json.dumps(inventory.manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INVENTORY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
