from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from sevent4.ports.jurisdiction import (
    JurisdictionCrosswalkWriter,
    OverlapJurisdictionRepository,
    RepresentativePointJurisdictionRepository,
)


CROSSWALK_SCHEMA = "sevent4.jurisdiction_crosswalk.v1"


@dataclass(frozen=True)
class JurisdictionCrosswalkResult:
    document: dict[str, Any]
    output_path: Any
    ward_count: int
    ac_count: int
    pc_count: int
    district_count: int = 0


def pick_populated_field(rows: Iterable[Mapping[str, Any]], candidates: Iterable[str]) -> str | None:
    row_list = list(rows)
    fields: list[str] = []
    seen: set[str] = set()
    for row in row_list:
        for field in row:
            if field not in seen:
                fields.append(field)
                seen.add(field)
    case_insensitive: dict[str, list[str]] = {}
    for field in fields:
        case_insensitive.setdefault(field.lower(), []).append(field)
    for candidate in candidates:
        candidate_fields = ([candidate] if candidate in seen else []) + [
            field for field in case_insensitive.get(candidate.lower(), []) if field != candidate
        ]
        for field in candidate_fields:
            if any(_clean_value(row.get(field)) for row in row_list):
                return field
    return None


def build_representative_point_crosswalk(city: str, rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    records = []
    for row in rows:
        ward_name = _clean_value(row.get("ward_name"))
        ac_name = _clean_value(row.get("ac_name"))
        if not (ward_name and ac_name):
            continue
        records.append(
            {
                "ward_name": ward_name,
                "ac_name": ac_name,
                "pc_name": _clean_value(row.get("pc_name")),
                "district_name": _clean_value(row.get("district_name")),
            }
        )
    return {
        "schema": CROSSWALK_SCHEMA,
        "city": city,
        "country": "India",
        "levels": ["state", "district"],
        "thresholds": {"method": "ward representative point within AC/PC polygon (nearest fallback), EPSG:3857"},
        "excluded_acs": [],
        "source": "spatial join of city ward/AC/PC layers",
        "records": records,
    }


def build_overlap_crosswalk(
    *,
    city: str,
    state: str,
    records: Iterable[Mapping[str, Any]],
    thresholds: Mapping[str, float],
    excluded_acs: Iterable[str] = (),
) -> dict[str, Any]:
    clean_records = [
        {
            "state_name": state,
            "district_name": _clean_value(row.get("district_name")),
            "pc_code": _clean_number(row.get("pc_code")),
            "pc_name": _clean_value(row.get("pc_name")),
            "ac_no": _clean_number(row.get("ac_no")),
            "ac_name": _clean_value(row.get("ac_name")),
            # Keep ward_no as the source string: zero-padded IDs like "02" are the
            # canonical form in the public crosswalk and representative parser.
            # _clean_number would strip the pad ("02" -> "2") and break those joins.
            "ward_no": _clean_value(row.get("ward_no")),
            "ward_name": _clean_value(row.get("ward_name")),
            "overlap_area_m2": round(float(row.get("overlap_area_m2") or 0.0), 2),
            "overlap_pct_of_ward": round(float(row.get("overlap_pct_of_ward") or 0.0), 5),
            "overlap_pct_of_ac": round(float(row.get("overlap_pct_of_ac") or 0.0), 7),
        }
        for row in records
    ]
    clean_records.sort(key=lambda row: (row["district_name"], row["pc_name"], _sort_int(row["ac_no"]), _sort_int(row["ward_no"])))
    return {
        "schema": CROSSWALK_SCHEMA,
        "city": city,
        "country": "India",
        "levels": ["state", "district", "pc", "ac", "ward"],
        "thresholds": dict(thresholds),
        "excluded_acs": [
            {
                "ac_name": name,
                "reason": "geometry appears to contain several sibling ACs in the same PC; excluded from filter crosswalk",
            }
            for name in excluded_acs
        ],
        "records": clean_records,
    }


def publish_representative_point_crosswalk(
    city: str,
    repository: RepresentativePointJurisdictionRepository,
    writer: JurisdictionCrosswalkWriter,
) -> JurisdictionCrosswalkResult:
    document = build_representative_point_crosswalk(city, repository.load_representative_point_records(city))
    output_path = writer.write_crosswalk(city, document)
    return _result(document, output_path)


def publish_overlap_crosswalk(
    city: str,
    repository: OverlapJurisdictionRepository,
    writer: JurisdictionCrosswalkWriter,
) -> JurisdictionCrosswalkResult:
    input_data = repository.load_overlap_crosswalk_input(city)
    document = build_overlap_crosswalk(
        city=input_data.city,
        state=input_data.state,
        records=input_data.records,
        thresholds=input_data.thresholds,
        excluded_acs=input_data.excluded_acs,
    )
    output_path = writer.write_crosswalk(input_data.city, document)
    return _result(document, output_path)


def _result(document: dict[str, Any], output_path: Any) -> JurisdictionCrosswalkResult:
    records = document["records"]
    return JurisdictionCrosswalkResult(
        document=document,
        output_path=output_path,
        ward_count=len({row["ward_name"] for row in records}),
        ac_count=len({row["ac_name"] for row in records}),
        pc_count=len({row["pc_name"] for row in records if row.get("pc_name")}),
        district_count=len({row["district_name"] for row in records if row.get("district_name")}),
    )


def _clean_value(value: Any) -> str:
    cleaned = "" if value is None else str(value).strip()
    return "" if cleaned.lower() in ("nan", "none", "") else cleaned


def _clean_number(value: Any) -> str:
    cleaned = _clean_value(value)
    if not cleaned:
        return ""
    try:
        number = float(cleaned)
    except ValueError:
        return cleaned
    return str(int(number)) if number.is_integer() else cleaned


def _sort_int(value: Any) -> int:
    cleaned = _clean_number(value)
    try:
        return int(cleaned)
    except ValueError:
        return 0
