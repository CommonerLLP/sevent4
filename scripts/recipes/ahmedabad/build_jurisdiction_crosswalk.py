#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import geopandas as gpd
import yaml
from shapely.validation import make_valid


REPO = Path(__file__).resolve().parents[3]
DEFAULT_CITY = "ahmedabad"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build District/PC/AC/Ward many-to-many jurisdiction crosswalk.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Ahmedabad is implemented first.")
    parser.add_argument("--city-yaml", help="Path to city.yaml.")
    parser.add_argument("--out", help="Output JSON path.")
    parser.add_argument("--min-ward-pct", type=float, default=0.005, help="Minimum ward-overlap share to keep.")
    parser.add_argument("--min-area-m2", type=float, default=2500.0, help="Minimum overlap area to keep.")
    parser.add_argument(
        "--keep-parent-like-acs",
        action="store_true",
        help="Keep AC polygons that appear to contain several sibling ACs in the same PC.",
    )
    args = parser.parse_args()

    city = args.city.lower()
    city_yaml = Path(args.city_yaml) if args.city_yaml else REPO / "data" / "cities" / city / "city.yaml"
    if not city_yaml.exists():
        sys.exit(f"Missing city config: {city_yaml}")

    cfg = yaml.safe_load(city_yaml.read_text(encoding="utf-8"))
    layers_dir = REPO / cfg["layers_dir"]
    out = Path(args.out) if args.out else layers_dir / "jurisdiction_crosswalk.json"
    result = build_crosswalk(
        city=city,
        state=str(cfg.get("state", "")),
        layers_dir=layers_dir,
        crs_metric=str(cfg.get("crs_metric", "EPSG:32643")),
        min_ward_pct=args.min_ward_pct,
        min_area_m2=args.min_area_m2,
        drop_parent_like_acs=not args.keep_parent_like_acs,
    )
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    print(
        "records={records} wards={wards} acs={acs} pcs={pcs} districts={districts}".format(
            records=len(result["records"]),
            wards=len({row["ward_name"] for row in result["records"]}),
            acs=len({row["ac_name"] for row in result["records"]}),
            pcs=len({row["pc_name"] for row in result["records"]}),
            districts=len({row["district_name"] for row in result["records"]}),
        )
    )


def build_crosswalk(
    *,
    city: str,
    state: str,
    layers_dir: Path,
    crs_metric: str,
    min_ward_pct: float,
    min_area_m2: float,
    drop_parent_like_acs: bool,
) -> dict[str, Any]:
    wards = _read_layer(layers_dir / "wards.geojson", crs_metric)
    acs = _read_layer(layers_dir / "acs.geojson", crs_metric)
    districts = _read_layer(layers_dir / "districts.geojson", crs_metric)

    wards["_area_m2"] = wards.geometry.area
    acs["_area_m2"] = acs.geometry.area
    excluded_acs = _parent_like_acs(acs) if drop_parent_like_acs else []
    if excluded_acs:
        acs = acs[~acs["ac_name"].isin(excluded_acs)].copy()

    records: list[dict[str, Any]] = []
    for _, ward in wards.iterrows():
        ward_geom = make_valid(ward.geometry)
        ward_name = str(ward.get("Name", "")).strip()
        ward_no = str(ward.get("ward_no", "")).strip() or _leading_number(ward_name)
        if not ward_name or ward_geom.is_empty:
            continue
        for _, ac in acs[acs.intersects(ward_geom)].iterrows():
            ac_geom = make_valid(ac.geometry)
            if ac_geom.is_empty:
                continue
            overlap = ward_geom.intersection(ac_geom)
            if overlap.is_empty:
                continue
            overlap_area = float(overlap.area)
            ward_pct = overlap_area / float(ward["_area_m2"])
            if overlap_area < min_area_m2 and ward_pct < min_ward_pct:
                continue
            ac_name = str(ac.get("ac_name", "")).strip()
            pc_name = str(ac.get("pc_name", "")).strip()
            district_name = _best_district(overlap, districts, str(ac.get("district", "")).strip())
            records.append(
                {
                    "state_name": state,
                    "district_name": district_name,
                    "pc_code": _clean_number(ac.get("pc_code", "")),
                    "pc_name": pc_name,
                    "ac_no": _clean_number(ac.get("ac_no", "")),
                    "ac_name": ac_name,
                    "ward_no": ward_no,
                    "ward_name": ward_name,
                    "overlap_area_m2": round(overlap_area, 2),
                    "overlap_pct_of_ward": round(ward_pct, 5),
                    "overlap_pct_of_ac": round(overlap_area / float(ac["_area_m2"]), 7),
                }
            )

    records.sort(key=lambda row: (row["district_name"], row["pc_name"], int(row["ac_no"]), int(row["ward_no"] or 0)))
    return {
        "schema": "sevent4.jurisdiction_crosswalk.v1",
        "city": city,
        "country": "India",
        "levels": ["state", "district", "pc", "ac", "ward"],
        "thresholds": {
            "min_ward_pct": min_ward_pct,
            "min_area_m2": min_area_m2,
        },
        "excluded_acs": [
            {
                "ac_name": name,
                "reason": "geometry appears to contain several sibling ACs in the same PC; excluded from filter crosswalk",
            }
            for name in excluded_acs
        ],
        "records": records,
    }


def _read_layer(path: Path, crs_metric: str) -> gpd.GeoDataFrame:
    if not path.exists():
        sys.exit(f"Missing layer: {path}")
    data = gpd.read_file(path)
    if data.crs is None:
        data = data.set_crs("EPSG:4326")
    return data.to_crs(crs_metric)


def _parent_like_acs(acs: gpd.GeoDataFrame) -> list[str]:
    excluded: list[str] = []
    for _, candidate in acs.iterrows():
        candidate_name = str(candidate.get("ac_name", "")).strip()
        candidate_pc = str(candidate.get("pc_name", "")).strip()
        if not candidate_name or not candidate_pc:
            continue
        sibling_count = 0
        for _, sibling in acs[acs["pc_name"] == candidate_pc].iterrows():
            sibling_name = str(sibling.get("ac_name", "")).strip()
            if sibling_name == candidate_name:
                continue
            sibling_area = float(sibling.geometry.area)
            if sibling_area <= 0:
                continue
            contained_pct = float(candidate.geometry.intersection(sibling.geometry).area) / sibling_area
            if contained_pct >= 0.8:
                sibling_count += 1
        if sibling_count >= 4:
            excluded.append(candidate_name)
    return sorted(excluded)


def _best_district(geom: Any, districts: gpd.GeoDataFrame, fallback: str) -> str:
    best_name = fallback
    best_area = 0.0
    for _, district in districts[districts.intersects(geom)].iterrows():
        area = float(geom.intersection(make_valid(district.geometry)).area)
        if area > best_area:
            best_area = area
            best_name = str(district.get("DISTRICT", district.get("district", fallback))).strip()
    return best_name


def _leading_number(value: str) -> str:
    token = value.strip().split(" ", 1)[0]
    return token if token.isdigit() else ""


def _clean_number(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


if __name__ == "__main__":
    main()
