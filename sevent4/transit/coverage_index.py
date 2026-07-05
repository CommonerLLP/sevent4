from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TRANSIT_COVERAGE_SCHEMA = "sevent4.transit_coverage.v1"
COVERAGE_STATUSES = frozenset(
    {
        "ok",
        "official_inventory_fallback",
        "osm_fallback_constructed",
        "sample_public_constructed_gtfs",
        "unofficial_constructed",
        "unofficial_gtfs_lead",
    }
)


def build_transit_coverage_index(
    city_root: str | Path,
    public_city_root: str | Path,
    *,
    compiled: str,
) -> dict[str, Any]:
    city_root = Path(city_root)
    public_city_root = Path(public_city_root)
    cities = []
    for manifest_path in sorted(city_root.glob("*/source/transit/multimodal_transit.sources.json")):
        city = manifest_path.parts[-4]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        cities.append(
            {
                "city": city,
                "feeds": [
                    _coverage_row(feed, public_city_root / city / "layers")
                    for feed in manifest.get("feeds", [])
                ],
            }
        )
    return {
        "schema": TRANSIT_COVERAGE_SCHEMA,
        "compiled": compiled,
        "coverage_statuses": sorted(COVERAGE_STATUSES),
        "cities": cities,
    }


def write_transit_coverage_index(
    city_root: str | Path,
    public_city_root: str | Path,
    out_path: str | Path,
    *,
    compiled: str,
) -> dict[str, Any]:
    payload = build_transit_coverage_index(city_root, public_city_root, compiled=compiled)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the public all-city transit coverage index.")
    parser.add_argument("--city-root", type=Path, default=Path("data/cities"))
    parser.add_argument("--public-city-root", type=Path, default=Path("public/cities"))
    parser.add_argument("--out", type=Path, default=Path("public/cities/transit_coverage.json"))
    parser.add_argument("--compiled", required=True)
    args = parser.parse_args()

    payload = write_transit_coverage_index(
        args.city_root,
        args.public_city_root,
        args.out,
        compiled=args.compiled,
    )
    print(f"wrote {args.out} for {len(payload['cities'])} cities")


def _coverage_row(feed: dict[str, Any], layers_dir: Path) -> dict[str, Any]:
    stop_layer = _layer_filename(feed.get("stop_layer"))
    route_layer = _layer_filename(feed.get("route_layer"))
    stop_exists = bool(stop_layer and (layers_dir / stop_layer).exists())
    route_exists = bool(route_layer and (layers_dir / route_layer).exists())
    stop_features = feed.get("stop_features")
    route_features = feed.get("route_features")
    public_coverage = (
        feed.get("status") in COVERAGE_STATUSES
        and _has_positive_count(stop_features, route_features)
        and (stop_exists or route_exists)
    )
    row = {
        "feed_id": feed.get("feed_id"),
        "mode": feed.get("mode"),
        "operator": feed.get("operator"),
        "status": feed.get("status"),
        "stop_layer": stop_layer,
        "route_layer": route_layer,
        "stop_features": stop_features,
        "route_features": route_features,
        "missing_reason": feed.get("missing_reason"),
        "public_layer_files": {
            "stop_layer_exists": stop_exists,
            "route_layer_exists": route_exists,
        },
        "public_coverage": public_coverage,
    }
    if "coverage_scope" in feed:
        row["coverage_scope"] = feed["coverage_scope"]
    return row


def _layer_filename(value: Any) -> str | None:
    if value is None:
        return None
    filename = str(value)
    if not filename:
        return None
    return filename if filename.endswith(".geojson") else f"{filename}.geojson"


def _has_positive_count(*values: Any) -> bool:
    for value in values:
        try:
            if int(value or 0) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


if __name__ == "__main__":
    main()
