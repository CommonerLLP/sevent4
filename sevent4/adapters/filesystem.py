from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any, Mapping
import html.parser

from sevent4.domain.evidence import (
    EvidenceBundle,
    claim_ids_in_html,
    evidence_bundle_from_dict,
    validate_claim_ids,
)
from sevent4.domain.pollution import PollutionBoardCapacityRecord
from sevent4.city_dataset import CityDataset
from sevent4.layer_manifest import LayerManifest
from sevent4.ports.publication import CityConsoleCity, CityConsoleInput, CityConsoleManifest


class _LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


class PublicSiteFileRepository:
    def __init__(self, public_dir: str | Path) -> None:
        self.public_dir = Path(public_dir)

    def page_ids(self) -> set[str]:
        return {_page_id(page.relative_to(self.public_dir)) for page in self.public_dir.glob("**/index.html")}

    def links_for_page(self, page_id: str) -> list[str]:
        parser = _LinkParser()
        parser.feed((self.public_dir / _path_from_page_id(page_id)).read_text(encoding="utf-8"))
        return parser.links


class FileDevolutionScorecardRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.service_providers_path = self.root / "data" / "institutions" / "service_providers.json"
        self.registry_path = self.root / "public" / "cities" / "registry.json"
        self.scorecard_path = self.root / "public" / "cities" / "scorecard.json"
        self.city_layers_dir = self.root / "data" / "cities"

    def load_service_providers(self) -> Mapping[str, Mapping[str, Any]]:
        return json.loads(self.service_providers_path.read_text(encoding="utf-8"))

    def load_registry_city_ids(self) -> tuple[str, ...]:
        return tuple(row["id"] for row in json.loads(self.registry_path.read_text(encoding="utf-8")))

    def load_existing_scorecard(self) -> Mapping[str, Mapping[str, Any]]:
        if not self.scorecard_path.exists():
            return {}
        return json.loads(self.scorecard_path.read_text(encoding="utf-8"))

    def write_scorecard(self, scorecard: Mapping[str, Mapping[str, Any]]) -> None:
        self.scorecard_path.parent.mkdir(parents=True, exist_ok=True)
        self.scorecard_path.write_text(json.dumps(scorecard, ensure_ascii=False, indent=1), encoding="utf-8")

    def write_governance_metrics(self, city_id: str, update: Mapping[str, Mapping[str, int]]) -> bool:
        governance_path = self.city_layers_dir / city_id / "layers" / "governance.json"
        if not governance_path.exists():
            return False
        governance = json.loads(governance_path.read_text(encoding="utf-8"))
        governance["devolution"] = dict(update["devolution"])
        governance["decided_by"] = dict(update["decided_by"])
        governance_path.write_text(json.dumps(governance, ensure_ascii=False), encoding="utf-8")
        return True


class FileCityConsoleInputRepository:
    def __init__(self, city_config: str | Path, layer_manifest: str | Path) -> None:
        self.city_config = Path(city_config)
        self.layer_manifest = Path(layer_manifest)

    def load(self) -> CityConsoleInput:
        city = CityDataset.from_yaml(self.city_config)
        manifest = LayerManifest.from_json(self.layer_manifest, city)
        return CityConsoleInput(city=city, manifest=manifest)


class FileCityConsolePublicSurface:
    def __init__(self, out: str | Path) -> None:
        self.out = Path(out).resolve()

    @property
    def output_dir(self) -> Path:
        return self.out.parent

    def prepare(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "layers").mkdir(parents=True, exist_ok=True)

    def publish_layers(self, city: CityConsoleCity, manifest: CityConsoleManifest) -> None:
        layer_out = self.output_dir / "layers"
        for layer in manifest.layers:
            shutil.copy2(city.layers_dir / layer.file, layer_out / layer.file)
            _canonicalise_geojson(layer_out / layer.file)
            if layer.bounds_file:
                shutil.copy2(city.layers_dir / layer.bounds_file, layer_out / layer.bounds_file)
        for sidecar in ("jurisdiction_crosswalk.json",):
            path = city.layers_dir / sidecar
            if path.exists():
                shutil.copy2(path, layer_out / sidecar)

    def write_index(self, html: str) -> None:
        self.out.write_text(html, encoding="utf-8")


class JsonEvidenceBundleRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> EvidenceBundle:
        return evidence_bundle_from_dict(json.loads(self.path.read_text(encoding="utf-8")))


class FilePollutionBoardCapacityRepository:
    def __init__(self, cities_dir: str | Path) -> None:
        self.cities_dir = Path(cities_dir)

    def list_capacity_records(self) -> tuple[PollutionBoardCapacityRecord, ...]:
        records: list[PollutionBoardCapacityRecord] = []
        for capacity_path in sorted(self.cities_dir.glob("*/source/pollution/capacity.json")):
            city = capacity_path.relative_to(self.cities_dir).parts[0]
            data = json.loads(capacity_path.read_text(encoding="utf-8"))
            records.append(PollutionBoardCapacityRecord.from_dict(city, data))
        return tuple(records)


class JsonFilePublicSurfaceWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_json(self, document: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def load_evidence_bundle(path: str | Path) -> EvidenceBundle:
    return JsonEvidenceBundleRepository(path).load()


def claim_ids_in_page(path: str | Path) -> tuple[str, ...]:
    return claim_ids_in_html(Path(path).read_text(encoding="utf-8"))


def validate_page_claim_ids(path: str | Path, bundle: EvidenceBundle) -> None:
    validate_claim_ids(claim_ids_in_page(path), bundle, str(Path(path)))


def _page_id(rel: Path) -> str:
    if rel == Path("index.html"):
        return ""
    if rel.name == "index.html":
        return rel.parent.as_posix() + "/"
    return rel.as_posix()


def _path_from_page_id(page_id: str) -> Path:
    return Path("index.html") if page_id == "" else Path(page_id) / "index.html"


_CANONICAL_GEOJSON_FIELDS = {
    "wards.geojson": ("Name", ("ward_name", "Name", "name", "ward_no", "WARD_NO")),
    "acs.geojson": ("ac_name", ("AC_NAME", "ac_name", "ASSEM_CSTNY_NAME", "Name", "name")),
    "pcs.geojson": ("pc_name", ("PC_NAME", "pc_name", "PARLY_CSTNY_NAME", "Name", "name")),
}


def _canonicalise_geojson(path: Path) -> None:
    if path.name not in _CANONICAL_GEOJSON_FIELDS:
        return
    canonical_field, candidates = _CANONICAL_GEOJSON_FIELDS[path.name]
    data = json.loads(path.read_text())
    features = data.get("features", [])
    if not features:
        return
    source_field = next(
        (candidate for candidate in candidates if any(_has_value(feature["properties"].get(candidate)) for feature in features)),
        None,
    )
    if not source_field:
        return
    changed = False
    for feature in features:
        properties = feature["properties"]
        if not _has_value(properties.get(canonical_field)) and _has_value(properties.get(source_field)):
            properties[canonical_field] = properties[source_field]
            changed = True
    if changed:
        path.write_text(json.dumps(data))


def _has_value(value) -> bool:
    return str(value if value is not None else "").strip() not in ("", "None", "nan")
