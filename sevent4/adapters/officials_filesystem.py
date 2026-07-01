from __future__ import annotations

import json
from pathlib import Path

from sevent4.city_dataset import CityDataset
from sevent4.ports.officials import OfficialsInput


class FileOfficialsInputRepository:
    def __init__(self, city_config: str | Path) -> None:
        self.city_config = Path(city_config)

    def load(self) -> OfficialsInput:
        city = CityDataset.from_yaml(self.city_config)
        path = city.layers_dir / "officials.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return OfficialsInput(
            city=city,
            as_of=str(data.get("as_of", "")),
            attribution=str(data.get("attribution", "")),
            records=data.get("records", []),
        )
