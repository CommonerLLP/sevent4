from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import yaml
from shapely.validation import make_valid

from sevent4.application.jurisdiction import pick_populated_field
from sevent4.ports.jurisdiction import OverlapCrosswalkInput


PROJECTED_CRS = 3857


class RepresentativePointJurisdictionRepository:
    def __init__(self, root: str | Path, metric_crs: int = PROJECTED_CRS) -> None:
        self.root = Path(root)
        self.metric_crs = metric_crs

    def load_representative_point_records(self, city: str) -> tuple[dict[str, str], ...]:
        layers_dir = self.root / "data" / "cities" / city / "layers"
        wards = gpd.read_file(layers_dir / "wards.geojson")
        acs = gpd.read_file(layers_dir / "acs.geojson")
        pcs = gpd.read_file(layers_dir / "pcs.geojson") if (layers_dir / "pcs.geojson").exists() else None

        ward_name = pick_populated_field(_properties(wards), ("ward_name", "Name", "name", "ward_no", "WARD_NO"))
        ac_name = pick_populated_field(
            _properties(acs),
            ("AC_NAME", "ac_name", "ASSEM_CSTNY_NAME", "ASSMBLY_NAME", "Name", "name"),
        )
        district_name = pick_populated_field(_properties(acs), ("DIST_NAME", "district", "DISTRICT", "dt_name"))
        pc_name = (
            pick_populated_field(_properties(pcs), ("PC_NAME", "pc_name", "PARLY_CSTNY_NAME", "Name", "name"))
            if pcs is not None
            else None
        )
        pc_name_on_ac = pick_populated_field(_properties(acs), ("PC_NAME", "pc_name", "PARLY_CSTNY_NAME"))
        if not (ward_name and ac_name):
            raise ValueError(f"{city}: missing AC name ({ac_name}) or ward name ({ward_name}) field")

        ward_points = wards.to_crs(self.metric_crs).copy()
        ward_points["geometry"] = ward_points.geometry.representative_point()
        ac_series = self._nearest_attr(ward_points, acs, ac_name)
        district_series = self._nearest_attr(ward_points, acs, district_name) if district_name else None
        if pcs is not None and pc_name:
            pc_series = self._nearest_attr(ward_points, pcs, pc_name)
        elif pc_name_on_ac:
            pc_series = self._nearest_attr(ward_points, acs, pc_name_on_ac)
        else:
            pc_series = None

        records = []
        for index, ward in wards.iterrows():
            ward_label = _clean(ward[ward_name])
            if ward_name in ("ward_no", "WARD_NO") and ward_label and not ward_label.lower().startswith("ward"):
                ward_label = f"Ward {ward_label}"
            ac_label = _clean(ac_series.get(index))
            if not (ward_label and ac_label):
                continue
            records.append(
                {
                    "ward_name": ward_label,
                    "ac_name": ac_label,
                    "pc_name": _clean(pc_series.get(index)) if pc_series is not None else "",
                    "district_name": _clean(district_series.get(index)) if district_series is not None else "",
                }
            )
        return tuple(records)

    def write_crosswalk(self, city: str, document: dict[str, Any]) -> Path:
        out = self.root / "data" / "cities" / city / "layers" / "jurisdiction_crosswalk.json"
        out.write_text(json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8")
        return out

    def _nearest_attr(self, points, polygons, column: str):
        polygon_values = polygons.to_crs(self.metric_crs)[[column, "geometry"]].rename(columns={column: "_v"})
        joined = gpd.sjoin(points[["geometry"]], polygon_values, predicate="within", how="left")
        joined = joined[~joined.index.duplicated(keep="first")]
        missing = joined["_v"].isna()
        if missing.any():
            missing_index = missing[missing].index
            nearest = gpd.sjoin_nearest(points.loc[missing_index][["geometry"]], polygon_values, how="left")
            nearest = nearest[~nearest.index.duplicated(keep="first")]
            joined.loc[nearest.index, "_v"] = nearest["_v"]
        return joined["_v"].reindex(points.index)


class AhmedabadOverlapJurisdictionRepository:
    def __init__(
        self,
        root: str | Path,
        city_yaml: str | Path | None = None,
        out: str | Path | None = None,
        min_ward_pct: float = 0.005,
        min_area_m2: float = 2500.0,
        drop_parent_like_acs: bool = True,
    ) -> None:
        self.root = Path(root)
        self.city_yaml = Path(city_yaml) if city_yaml else None
        self.out = Path(out) if out else None
        self.min_ward_pct = min_ward_pct
        self.min_area_m2 = min_area_m2
        self.drop_parent_like_acs = drop_parent_like_acs

    def load_overlap_crosswalk_input(self, city: str) -> OverlapCrosswalkInput:
        city_yaml = self.city_yaml or self.root / "data" / "cities" / city / "city.yaml"
        if not city_yaml.exists():
            raise FileNotFoundError(f"Missing city config: {city_yaml}")
        config = yaml.safe_load(city_yaml.read_text(encoding="utf-8"))
        layers_dir = self.root / config["layers_dir"]
        metric_crs = str(config.get("crs_metric", "EPSG:32643"))
        wards = _read_layer(layers_dir / "wards.geojson", metric_crs)
        acs = _read_layer(layers_dir / "acs.geojson", metric_crs)
        districts = _read_layer(layers_dir / "districts.geojson", metric_crs)

        wards["_area_m2"] = wards.geometry.area
        acs["_area_m2"] = acs.geometry.area
        excluded_acs = _parent_like_acs(acs) if self.drop_parent_like_acs else []
        if excluded_acs:
            acs = acs[~acs["ac_name"].isin(excluded_acs)].copy()

        rows: list[dict[str, Any]] = []
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
                if overlap_area < self.min_area_m2 and ward_pct < self.min_ward_pct:
                    continue
                rows.append(
                    {
                        "district_name": _best_district(overlap, districts, str(ac.get("district", "")).strip()),
                        "pc_code": ac.get("pc_code", ""),
                        "pc_name": ac.get("pc_name", ""),
                        "ac_no": ac.get("ac_no", ""),
                        "ac_name": ac.get("ac_name", ""),
                        "ward_no": ward_no,
                        "ward_name": ward_name,
                        "overlap_area_m2": overlap_area,
                        "overlap_pct_of_ward": ward_pct,
                        "overlap_pct_of_ac": overlap_area / float(ac["_area_m2"]),
                    }
                )
        return OverlapCrosswalkInput(
            city=city,
            state=str(config.get("state", "")),
            records=tuple(rows),
            thresholds={"min_ward_pct": self.min_ward_pct, "min_area_m2": self.min_area_m2},
            excluded_acs=tuple(excluded_acs),
        )

    def write_crosswalk(self, city: str, document: dict[str, Any]) -> Path:
        out = self.out or self.root / "data" / "cities" / city / "layers" / "jurisdiction_crosswalk.json"
        out.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
        return out


def _properties(frame) -> tuple[dict[str, Any], ...]:
    if frame is None:
        return ()
    return tuple(row.drop(labels=["geometry"], errors="ignore").to_dict() for _, row in frame.iterrows())


def _clean(value: Any) -> str:
    cleaned = "" if value is None else str(value).strip()
    return "" if cleaned.lower() in ("nan", "none", "") else cleaned


def _read_layer(path: Path, crs_metric: str):
    return gpd.read_file(path).to_crs(crs_metric)


def _leading_number(value: str) -> str:
    digits = []
    for char in value.strip():
        if char.isdigit():
            digits.append(char)
        elif digits:
            break
    return "".join(digits)


def _parent_like_acs(acs) -> list[str]:
    excluded: list[str] = []
    for _, row in acs.iterrows():
        pc = str(row.get("pc_name", "")).strip()
        same_pc = acs[acs["pc_name"].astype(str).str.strip() == pc]
        if len(same_pc) <= 1:
            continue
        contained = 0
        geom = make_valid(row.geometry)
        for _, other in same_pc.iterrows():
            if str(other.get("ac_name", "")) == str(row.get("ac_name", "")):
                continue
            other_geom = make_valid(other.geometry)
            if geom.contains(other_geom.centroid):
                contained += 1
        if contained >= 2:
            excluded.append(str(row.get("ac_name", "")).strip())
    return excluded


def _best_district(overlap, districts, fallback: str) -> str:
    if districts.empty:
        return fallback
    matches = districts[districts.intersects(overlap)]
    if matches.empty:
        return fallback
    best_name = fallback
    best_area = 0.0
    for _, district in matches.iterrows():
        geom = make_valid(district.geometry)
        area = float(overlap.intersection(geom).area)
        if area > best_area:
            best_area = area
            best_name = str(district.get("district", "") or district.get("DISTRICT", "") or fallback).strip()
    return best_name
