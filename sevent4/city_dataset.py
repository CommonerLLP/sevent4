from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class CityDataset:
    id: str
    name: str
    country: str
    state: str
    center: tuple[float, float]
    bbox: tuple[float, float, float, float]
    crs_metric: str
    layers_dir: Path
    source_dir: Path
    outputs_dir: Path
    config_path: Path
    repo_root: Path

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CityDataset":
        config_path = _absolute_path(path)
        repo_root = _find_repo_root(config_path)
        data = yaml.safe_load(config_path.read_text()) or {}

        def req(key: str) -> Any:
            if key not in data:
                raise KeyError(f"{config_path} is missing required key: {key}")
            return data[key]

        return cls(
            id=str(req("id")),
            name=str(req("name")),
            country=str(req("country")),
            state=str(req("state")),
            center=_pair(req("center"), "center"),
            bbox=_bbox(req("bbox")),
            crs_metric=str(req("crs_metric")),
            layers_dir=_resolve(repo_root, req("layers_dir")),
            source_dir=_resolve(repo_root, req("source_dir")),
            outputs_dir=_resolve(repo_root, req("outputs_dir")),
            config_path=config_path,
            repo_root=repo_root,
        )

    def resolve(self, value: str | Path) -> Path:
        return _resolve(self.repo_root, value)


def _find_repo_root(path: Path) -> Path:
    for candidate in (path, path.resolve()):
        for parent in [candidate.parent, *candidate.parents]:
            if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
                return parent
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return path.parent


def _absolute_path(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else Path.cwd() / candidate


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _pair(value: Any, label: str) -> tuple[float, float]:
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise ValueError(f"{label} must be [lon, lat]")
    return float(value[0]), float(value[1])


def _bbox(value: Any) -> tuple[float, float, float, float]:
    if not isinstance(value, list | tuple) or len(value) != 4:
        raise ValueError("bbox must be [west, south, east, north]")
    return tuple(float(v) for v in value)  # type: ignore[return-value]
