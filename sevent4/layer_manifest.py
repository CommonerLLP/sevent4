from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .city_dataset import CityDataset

VALID_KINDS = {"fill", "line", "circle", "image"}


@dataclass(frozen=True)
class LayerSpec:
    id: str
    label: str
    file: str
    kind: str
    default: bool
    group: str
    popup: tuple[str, ...]
    paint: dict[str, Any]
    outline: bool = False
    bounds_file: str | None = None

    @property
    def is_interactive(self) -> bool:
        return bool(self.popup)


@dataclass(frozen=True)
class LayerManifest:
    path: Path
    layers: tuple[LayerSpec, ...]

    @classmethod
    def from_json(cls, path: str | Path, city: CityDataset) -> "LayerManifest":
        manifest_path = Path(path).resolve()
        data = json.loads(manifest_path.read_text())
        specs = tuple(_layer_spec(item) for item in data.get("layers", []))
        manifest = cls(path=manifest_path, layers=specs)
        manifest.validate(city)
        return manifest

    def validate(self, city: CityDataset) -> None:
        seen: set[str] = set()
        for layer in self.layers:
            if layer.id in seen:
                raise ValueError(f"duplicate layer id: {layer.id}")
            seen.add(layer.id)
            if layer.kind not in VALID_KINDS:
                raise ValueError(f"{layer.id}: invalid kind {layer.kind}")
            layer_path = city.layers_dir / layer.file
            if not layer_path.exists():
                raise FileNotFoundError(f"{layer.id}: missing layer file {layer_path}")
            if layer.kind == "image":
                if not layer.bounds_file:
                    raise ValueError(f"{layer.id}: image layers require bounds_file")
                bounds_path = city.layers_dir / layer.bounds_file
                if not bounds_path.exists():
                    raise FileNotFoundError(f"{layer.id}: missing bounds file {bounds_path}")


def _layer_spec(item: dict[str, Any]) -> LayerSpec:
    return LayerSpec(
        id=str(item["id"]),
        label=str(item.get("label", item["id"])),
        file=str(item["file"]),
        kind=str(item.get("kind", "fill")),
        default=bool(item.get("default", False)),
        group=str(item.get("group", "Layers")),
        popup=tuple(str(v) for v in item.get("popup", [])),
        paint=dict(item.get("paint", {})),
        outline=bool(item.get("outline", False)),
        bounds_file=str(item["bounds_file"]) if item.get("bounds_file") else None,
    )
