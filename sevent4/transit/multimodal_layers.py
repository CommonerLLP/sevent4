from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path

from sevent4.adapters.transit_filesystem import FileGtfsCorridorInputRepository
from sevent4.application.transit import (
    GtfsLayerBundleResult,
    TransitFeedSpec,
    build_multimodal_gtfs_layers,
    coastal_multimodal_feed_specs,
)


@dataclass(frozen=True)
class TransitFeedRunSpec:
    spec: TransitFeedSpec
    gtfs_path: Path | None = None


def feed_run_specs_from_manifest(document: dict, city: str | None = None) -> list[TransitFeedRunSpec]:
    runs = []
    for row in document.get("feeds", []):
        spec = _feed_spec_from_mapping(row)
        if city and spec.city != city:
            continue
        path_value = row.get("path") or row.get("dir") or row.get("zip")
        runs.append(TransitFeedRunSpec(spec=spec, gtfs_path=Path(path_value) if path_value else None))
    return runs


def default_feed_run_specs(city: str) -> list[TransitFeedRunSpec]:
    return [TransitFeedRunSpec(spec) for spec in coastal_multimodal_feed_specs() if spec.city == city]


def build_city_multimodal_layers(
    city: str,
    feed_runs: list[TransitFeedRunSpec],
    city_root: Path,
    *,
    merge_existing_sources: bool = False,
) -> GtfsLayerBundleResult:
    city_dir = Path(city_root) / city
    layers_dir = city_dir / "layers"
    sources_dir = city_dir / "source" / "transit"
    specs = []
    inputs_by_feed = {}
    for run in feed_runs:
        spec = run.spec
        gtfs_path = _resolve_gtfs_path(run.gtfs_path, city_dir)
        if spec.status == "available" and gtfs_path is not None and gtfs_path.exists():
            inputs_by_feed[spec.feed_id] = FileGtfsCorridorInputRepository(gtfs_path).load()
        elif spec.status == "available":
            spec = replace(
                spec,
                status="missing",
                missing_reason=f"GTFS path not found: {run.gtfs_path}" if run.gtfs_path else "No GTFS path configured.",
            )
        specs.append(spec)

    result = build_multimodal_gtfs_layers(specs, inputs_by_feed)
    layers_dir.mkdir(parents=True, exist_ok=True)
    for filename, document in result.layers.items():
        _write_json(layers_dir / filename, document)
    _patch_layer_manifest(layers_dir / "layer_manifest.json", specs, set(result.layers))
    sources_dir.mkdir(parents=True, exist_ok=True)
    sources_path = sources_dir / "multimodal_transit.sources.json"
    provenance = _merge_source_manifest(sources_path, result.provenance) if merge_existing_sources else result.provenance
    _write_json(sources_path, provenance, indent=1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build city multimodal transit layers from GTFS feeds.")
    parser.add_argument("city", choices=("ahmedabad", "bengaluru", "bhubaneswar", "chennai", "kolkata", "mumbai", "surat"))
    parser.add_argument("--manifest", type=Path, help="JSON feed manifest with a feeds[] array.")
    parser.add_argument("--city-root", type=Path, default=Path("data/cities"))
    parser.add_argument(
        "--merge-existing-sources",
        action="store_true",
        help="Replace matching feed_id rows in the existing transit source manifest and preserve unrelated rows.",
    )
    args = parser.parse_args()

    if args.manifest:
        feed_runs = feed_run_specs_from_manifest(json.loads(args.manifest.read_text(encoding="utf-8")), args.city)
    else:
        feed_runs = default_feed_run_specs(args.city)
    result = build_city_multimodal_layers(
        args.city,
        feed_runs,
        args.city_root,
        merge_existing_sources=args.merge_existing_sources,
    )
    print(
        f"wrote {len(result.layers)} layers and {len(result.provenance['feeds'])} provenance records "
        f"for {args.city}"
    )


def _feed_spec_from_mapping(row: dict) -> TransitFeedSpec:
    status, provenance_status = _runner_status(row)
    return TransitFeedSpec(
        feed_id=row["feed_id"],
        city=row["city"],
        mode=row["mode"],
        operator=row["operator"],
        stop_layer=row["stop_layer"],
        route_layer=row["route_layer"],
        source_url=row.get("source_url", ""),
        license=row.get("license", ""),
        status=status,
        provenance_status=provenance_status,
        missing_reason=row.get("missing_reason", ""),
        notes=row.get("notes", ""),
        route_types=tuple(str(route_type) for route_type in row.get("route_types", ())),
        bbox=_bbox_from_mapping(row),
    )


def _runner_status(row: dict) -> tuple[str, str]:
    status = row.get("status", "available")
    if status in {"ok", "iudx_policy_approved_export"}:
        return "available", row.get("provenance_status", status)
    return status, row.get("provenance_status", "ok")


def _bbox_from_mapping(row: dict) -> tuple[float, float, float, float] | None:
    value = row.get("bbox")
    if value is None:
        return None
    if not isinstance(value, list | tuple) or len(value) != 4:
        raise ValueError("bbox must be [minlon, minlat, maxlon, maxlat]")
    return tuple(float(part) for part in value)


def _resolve_gtfs_path(path: Path | None, city_dir: Path) -> Path | None:
    if path is None or path.is_absolute():
        return path
    direct = Path(path)
    if direct.exists():
        return direct
    return city_dir / path


def _write_json(path: Path, document: dict, indent: int | None = None) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":")),
        encoding="utf-8",
    )


def _merge_source_manifest(existing_path: Path, updates: dict) -> dict:
    if not existing_path.exists():
        return updates
    existing = json.loads(existing_path.read_text(encoding="utf-8"))
    rows_by_feed = {row.get("feed_id"): row for row in updates.get("feeds", [])}
    merged = []
    seen = set()
    for row in existing.get("feeds", []):
        feed_id = row.get("feed_id")
        if feed_id in rows_by_feed:
            merged.append(rows_by_feed[feed_id])
            seen.add(feed_id)
        else:
            merged.append(row)
    for row in updates.get("feeds", []):
        feed_id = row.get("feed_id")
        if feed_id not in seen:
            merged.append(row)
            seen.add(feed_id)
    return {
        "schema": updates.get("schema", existing.get("schema", "sevent4.multimodal_transit.sources.v1")),
        "feeds": merged,
    }


def _patch_layer_manifest(manifest_path: Path, specs: list[TransitFeedSpec], written_layers: set[str]) -> None:
    if not manifest_path.exists() or not written_layers:
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = []
    for spec in specs:
        if f"{spec.stop_layer}.geojson" in written_layers:
            entries.append(_stop_manifest_entry(spec))
        if f"{spec.route_layer}.geojson" in written_layers:
            entries.append(_route_manifest_entry(spec))
    if entries:
        manifest["layers"] = _merge_layer_entries(manifest.get("layers", []), entries)
        _write_json(manifest_path, manifest, indent=2)


def _merge_layer_entries(layers: list[dict], entries: list[dict]) -> list[dict]:
    out = list(layers)
    by_id = {layer.get("id"): idx for idx, layer in enumerate(out)}
    for entry in entries:
        idx = by_id.get(entry["id"])
        if idx is None:
            by_id[entry["id"]] = len(out)
            out.append(entry)
        else:
            out[idx] = entry
    return out


def _stop_manifest_entry(spec: TransitFeedSpec) -> dict:
    return {
        "id": spec.stop_layer,
        "label": _stop_label(spec),
        "file": f"{spec.stop_layer}.geojson",
        "kind": "circle",
        "group": "Transit",
        "default": False,
        "popup": ["stop_name", "operator", "mode"],
        "paint": {
            "circle-color": _mode_color(spec.mode),
            "circle-radius": 3.2,
            "circle-stroke-color": "#101318",
            "circle-stroke-width": 0.6,
            "circle-opacity": 0.85,
        },
    }


def _route_manifest_entry(spec: TransitFeedSpec) -> dict:
    return {
        "id": spec.route_layer,
        "label": _route_label(spec),
        "file": f"{spec.route_layer}.geojson",
        "kind": "line",
        "group": "Transit",
        "default": False,
        "popup": ["route_short_name", "route_long_name", "operator", "mode"],
        "paint": {
            "line-color": _mode_color(spec.mode),
            "line-width": 1.8 if spec.mode != "metro" else 2.4,
            "line-opacity": 0.88,
        },
    }


def _stop_label(spec: TransitFeedSpec) -> str:
    if spec.provenance_status == "unofficial_constructed":
        return f"{_mode_display_name(spec.mode)} stops (unofficial GTFS)"
    if spec.provenance_status == "osm_fallback_constructed":
        return f"{_mode_display_name(spec.mode)} stops (OSM fallback GTFS)"
    if spec.provenance_status == "sample_public_constructed_gtfs":
        return f"{_mode_display_name(spec.mode)} stops (IUDX sample GTFS)"
    labels = {
        "suburban_rail": "Suburban rail stations",
        "mrts": "MRTS stations",
        "metro": "Metro stations (GTFS)",
        "bus": "Bus stops",
        "regulated_private_bus": "Regulated private bus stops",
        "ferry": "Ferry stops",
    }
    return labels.get(spec.mode, f"{spec.operator} stops")


def _route_label(spec: TransitFeedSpec) -> str:
    if spec.provenance_status == "unofficial_constructed":
        return f"{_mode_display_name(spec.mode)} routes (unofficial GTFS)"
    if spec.provenance_status == "osm_fallback_constructed":
        return f"{_mode_display_name(spec.mode)} routes (OSM fallback GTFS)"
    if spec.provenance_status == "sample_public_constructed_gtfs":
        return f"{_mode_display_name(spec.mode)} routes (IUDX sample GTFS)"
    labels = {
        "suburban_rail": "Suburban rail",
        "mrts": "MRTS",
        "metro": "Metro routes (GTFS)",
        "bus": "Bus routes",
        "regulated_private_bus": "Regulated private bus routes",
        "ferry": "Ferry routes",
    }
    return labels.get(spec.mode, f"{spec.operator} routes")


def _mode_display_name(mode: str) -> str:
    return {
        "suburban_rail": "Suburban rail",
        "mrts": "MRTS",
        "metro": "Metro",
        "bus": "Bus",
        "regulated_private_bus": "Regulated private bus",
        "ferry": "Ferry",
    }.get(mode, mode.replace("_", " ").title())


def _mode_color(mode: str) -> str:
    return {
        "suburban_rail": "#edc233",
        "mrts": "#d68032",
        "metro": "#dc4c4c",
        "bus": "#9ca3ad",
        "regulated_private_bus": "#46c1b4",
        "ferry": "#3aa0d6",
    }.get(mode, "#8a8f98")


if __name__ == "__main__":
    main()
