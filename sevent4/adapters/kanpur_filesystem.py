from __future__ import annotations

import json
from pathlib import Path

from sevent4.domain.kanpur_wards import HEAT_FIELD_KEYS, WARD_FIELD_KEYS, apply_fields


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _dump(obj: dict, path: Path) -> None:
    Path(path).write_text(json.dumps(obj), encoding="utf-8")


class FileKanpurWardRepository:
    def __init__(self, repo_root: str | Path) -> None:
        root = Path(repo_root)
        city = root / "data" / "cities" / "kanpur"
        self.src = city / "source" / "boundaries" / "wards.geojson"
        self.layer_wards = city / "layers" / "wards.geojson"
        self.pub_wards = root / "public" / "cities" / "kanpur" / "layers" / "wards.geojson"
        self.layer_heat = city / "layers" / "ward_heat.geojson"
        self.pub_heat = root / "public" / "cities" / "kanpur" / "layers" / "ward_heat.geojson"

    def load_source_wards(self) -> dict:
        return _load(self.src)

    def load_heat(self) -> dict:
        return _load(self.layer_heat) if self.layer_heat.exists() else {"features": []}

    def write_source_wards(self, wards: dict) -> None:
        _dump(wards, self.src)

    def propagate_ward_fields(self, wards: dict) -> None:
        for target in (self.layer_wards, self.pub_wards):
            _dump(apply_fields(_load(target), wards, WARD_FIELD_KEYS), target)

    def propagate_heat_fields(self, wards: dict) -> None:
        for target in (self.layer_heat, self.pub_heat):
            if not target.exists():
                continue
            _dump(apply_fields(_load(target), wards, HEAT_FIELD_KEYS), target)
