from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sevent4.city_dataset import CityDataset
from sevent4.ports.sources import SourcesInput


class FileSourcesInputRepository:
    """Loads data/cities/{city}/source/public_sources.json for publication.

    The build-time gate lives here, not in the application layer: every entry
    that names an `evidence` path must point at a record that actually exists
    on disk. A source inventory whose evidence has gone missing must fail the
    build, not silently publish.
    """

    def __init__(self, city_config: str | Path) -> None:
        self.city_config = Path(city_config)

    def load(self) -> SourcesInput:
        city = CityDataset.from_yaml(self.city_config)
        path = city.source_dir / "public_sources.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        entries: list[dict[str, Any]] = data.get("sources", [])
        missing = [
            str(entry.get("evidence"))
            for entry in entries
            if entry.get("evidence") and not city.resolve(entry["evidence"]).exists()
        ]
        if missing:
            raise FileNotFoundError(
                f"{path}: evidence records missing on disk: {missing}"
            )
        return SourcesInput(
            city=city,
            compiled=str(data.get("compiled", "")),
            entries=entries,
        )


class JsonFileWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_json(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
