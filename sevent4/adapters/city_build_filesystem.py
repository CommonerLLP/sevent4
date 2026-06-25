from __future__ import annotations

import csv
import json
from pathlib import Path

from sevent4.application.city_build import CityBuildArtifacts, CityBuildInput, OSM_LAYERS


class FileCityBuildRepository:
    def __init__(self, root: str | Path, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.city_dir = self.root / "data" / "cities" / slug
        self.source_dir = self.city_dir / "source"

    def load(self) -> CityBuildInput:
        boundaries_dir = self.source_dir / "boundaries"
        boundaries = {
            "wards": _load_json(boundaries_dir / "wards.geojson"),
            "acs": _load_json(boundaries_dir / "acs.geojson"),
            "pcs": _load_json(boundaries_dir / "pcs.geojson"),
        }
        districts_path = boundaries_dir / "districts.geojson"
        if districts_path.exists():
            boundaries["districts"] = _load_json(districts_path)

        osm_layers = {}
        for source_name in OSM_LAYERS:
            path = self.source_dir / "osm" / f"{source_name}.geojson"
            if path.exists():
                osm_layers[source_name] = _load_json(path)

        councillors_path = self.source_dir / "corporation" / "councillors.csv"
        officers_path = self.source_dir / "officers.json"
        return CityBuildInput(
            slug=self.slug,
            boundaries=boundaries,
            osm_layers=osm_layers,
            councillors=_load_csv(councillors_path) if councillors_path.exists() else (),
            officers=_load_json(officers_path) if officers_path.exists() else (),
        )


class FileCityBuildArtifactWriter:
    def __init__(self, root: str | Path, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.city_dir = self.root / "data" / "cities" / slug
        self.layers_dir = self.city_dir / "layers"

    def write(self, artifacts: CityBuildArtifacts) -> None:
        self.layers_dir.mkdir(parents=True, exist_ok=True)
        for filename, document in artifacts.layers.items():
            _write_json(self.layers_dir / filename, document)
        (self.city_dir / "city.yaml").write_text(_city_yaml_text(artifacts.city_yaml), encoding="utf-8")
        _write_json(self.layers_dir / "governance.json", artifacts.governance)
        _write_json(self.layers_dir / "layer_manifest.json", artifacts.manifest)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, document) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def _load_csv(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _city_yaml_text(data) -> str:
    center = ", ".join(f"{value:.4f}" for value in data["center"])
    bbox = ", ".join(f"{value:.4f}" for value in data["bbox"])
    return (
        f"id: {data['id']}\n"
        f"name: {data['name']}\n"
        "country: India\n"
        f"state: {data['state']}\n"
        f"center: [{center}]\n"
        f"bbox: [{bbox}]\n"
        f"crs_metric: {data['crs_metric']}\n"
        f"layers_dir: {data['layers_dir']}\n"
        f"source_dir: {data['source_dir']}\n"
        f"outputs_dir: {data['outputs_dir']}\n"
    )
