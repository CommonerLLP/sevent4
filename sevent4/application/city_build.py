from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Mapping

from sevent4.ports.city_build import CityBuildArtifactWriter, CityBuildInputRepository


@dataclass(frozen=True)
class CityBuildInput:
    slug: str
    boundaries: Mapping[str, Mapping[str, Any]]
    osm_layers: Mapping[str, Mapping[str, Any]]
    councillors: tuple[Mapping[str, str], ...] | list[Mapping[str, str]] = ()
    officers: tuple[Mapping[str, str], ...] | list[Mapping[str, str]] = ()


@dataclass(frozen=True)
class CityBuildArtifacts:
    slug: str
    layers: Mapping[str, Mapping[str, Any]]
    city_yaml: Mapping[str, Any]
    governance: Mapping[str, Any]
    manifest: Mapping[str, Any]
    summary: Mapping[str, Any]


CITY_META = {
    "chennai": {"name": "Chennai", "state": "Tamil Nadu", "district": "Chennai",
        "council": {"status": "elected", "since": "2022-02",
            "note": "Elected GCC council since Feb 2022 (DMK-led, ~178/200). Mayor R. Priya (DMK) — Chennai's first Dalit woman mayor."}},
    "mumbai": {"name": "Mumbai", "state": "Maharashtra", "district": "Mumbai",
        "council": {"status": "elected", "since": "2026-01",
            "note": "Elected BMC council since Jan 2026 (BJP-led Maha Yuti, Mayor Ritu Tawde) — ending ~4 years of state-appointed administrator rule (Mar 2022-Jan 2026)."}},
    "bengaluru": {"name": "Bengaluru", "state": "Karnataka", "district": "Bengaluru Urban",
        "council": {"status": "administrator", "since": "2020-09",
            "note": "NO elected council since 2020. BBMP dissolved into the Greater Bengaluru Authority (5 corps, 369 wards) under IAS Chief Commissioner M. Maheshwar Rao; first elections only by Aug 2026 — an 11-year democratic gap."}},
    "kolkata": {"name": "Kolkata", "state": "West Bengal", "district": "Kolkata",
        "council": {"status": "elected", "since": "2021-12",
            "note": "Elected KMC council since Dec 2021 (TMC, 134/144). Mayoralty currently vacant — Firhad Hakim resigned June 2026."}},
    "hyderabad": {"name": "Hyderabad", "state": "Telangana", "district": "Hyderabad",
        "council": {"status": "administrator", "since": "2026-02",
            "note": "NO sitting council — the 2020 GHMC term expired Feb 2026 and GHMC was trifurcated; run by IAS Special Officer Jayesh Ranjan. Fresh polls pending."}},
    "visakhapatnam": {"name": "Visakhapatnam", "state": "Andhra Pradesh", "district": "Visakhapatnam",
        "council": {"status": "elected", "since": "2021-03",
            "note": "Elected GVMC council since 2021; mayoralty flipped to TDP/NDA (Peela Srinivasa Rao) via a no-confidence motion in Apr 2025."}},
    "bhubaneswar": {"name": "Bhubaneswar", "state": "Odisha", "district": "Khordha",
        "council": {"status": "elected", "since": "2022-03",
            "note": "Elected BMC council since Mar 2022 (BJD, 48/67). Mayor Sulochana Das — Bhubaneswar's first woman mayor."}},
    "kochi": {"name": "Kochi", "state": "Kerala", "district": "Ernakulam",
        "council": {"status": "elected", "since": "2025-12",
            "note": "Elected Kochi Corporation council since Dec 2025 (UDF, Mayor V.K. Minimol, INC) — Kerala holds local elections on time every 5 years; no administrator gap, ever."}},
    "pune": {"name": "Pune", "state": "Maharashtra", "district": "Pune",
        "council": {"status": "elected", "since": "2026-01",
            "note": "Elected PMC council since Jan 2026 (BJP, Mayor Manjusha Nagpure) — ending ~4 years of administrator rule (Maharashtra delimitation case)."}},
    "kanpur": {"name": "Kanpur", "state": "Uttar Pradesh", "district": "Kanpur Nagar",
        "council": {"status": "elected", "since": "2023-05",
            "note": "Elected Kanpur Nagar Nigam council since May 2023 (BJP, Mayor Pramila Pandey). Note: only legacy 58-ward geometry is openly available; current count is 110."}},
    "lucknow": {"name": "Lucknow", "state": "Uttar Pradesh", "district": "Lucknow",
        "council": {"status": "elected", "since": "2023-05",
            "note": "Elected Lucknow Municipal Corporation council since May 2023 (BJP, Mayor Sushma Kharakwal — BJP took 80 of 110 wards). UP holds its urban-local-body polls on schedule; no administrator gap. Note: the Lucknow Cantonment is a separately-governed area outside LMC's 110 wards."}},
    "jaipur": {"name": "Jaipur", "state": "Rajasthan", "district": "Jaipur",
        "council": {"status": "administrator", "since": "2025-04",
            "note": "Administrator-run — the Heritage & Greater corporations' terms expired and the state is merging them; elections delayed on the Rajasthan OBC-report question."}},
    "delhi": {"name": "Delhi", "state": "Delhi (NCT)", "district": "Delhi",
        "council": {"status": "elected", "since": "2022-12",
            "note": "Elected MCD council since Dec 2022 — the trifurcated North/South/East corporations were re-unified into a single 250-ward Municipal Corporation of Delhi. AAP won the 2022 poll (~134/250); the mayoralty passed to the BJP (Mayor Raja Iqbal Singh, Apr 2025) after the BJP's Feb 2025 NCT assembly win. NCT special case: the MCD is only one of three civic bodies — the New Delhi Municipal Council (NDMC) and the Delhi Cantonment Board run their own areas, and most city functions sit with the GNCTD / Lieutenant-Governor, not the municipality."}},
}

OSM_LAYERS = {
    "roads": ("roads", "Roads", "line", "Mobility", False),
    "metro_lines": ("metro_lines", "Metro lines", "line", "Transit", True),
    "metro_stations": ("metro", "Metro stations", "circle", "Transit", True),
    "bus_stops": ("stops", "Bus stops", "circle", "Transit", False),
    "hospitals": ("health", "Health facilities", "circle", "Public services", False),
    "schools": ("schools", "Schools", "circle", "Public services", False),
    "libraries": ("libraries", "Libraries", "circle", "Public services", True),
    "toilets": ("toilets", "Public toilets", "circle", "Public services", False),
    "police": ("police", "Police", "circle", "Public services", False),
    "fire_stations": ("fire", "Fire & emergency", "circle", "Public services", False),
}
CIRCLE_COLOR = {
    "metro": "#5c8af2", "stops": "#9ca3ad", "health": "#49a35f", "schools": "#1e9f8f",
    "libraries": "#e0b84d", "toilets": "#46c1b4", "police": "#4d76c7", "fire": "#db4c45",
}
WARD_KEYS = ("ward_no", "WARD_NO", "Ward_No", "ward", "WARD", "no", "NO", "wardno", "Name", "name")


def build_city_artifacts(input_data: CityBuildInput) -> CityBuildArtifacts:
    meta = CITY_META.get(input_data.slug)
    if not meta:
        raise ValueError(f"add {input_data.slug} to CITY_META first")

    layers: dict[str, Mapping[str, Any]] = {}
    wards = deepcopy(input_data.boundaries["wards"])
    roster = _councillor_roster(input_data.councillors)
    for feature in wards["features"]:
        properties = feature["properties"]
        ward_number = str(next((properties[key] for key in WARD_KEYS if str(properties.get(key) or "").strip()), "")).strip()
        zone = properties.get("zone_name") or properties.get("ZONE") or properties.get("zone") or properties.get("CIRCLE") or ""
        if "Name" not in properties:
            properties["Name"] = f"Ward {ward_number}" + (f" · {zone}" if zone else "")
        representative = roster.get(wardkey(ward_number))
        if representative and representative["name"]:
            properties["councillor_count"] = 1
            properties["councillors"] = representative["name"]
            properties["councillor_parties"] = representative["party"]
            properties["councillor_phones"] = representative["phone"]
    layers["wards.geojson"] = wards

    acs = deepcopy(input_data.boundaries["acs"])
    for feature in acs["features"]:
        properties = feature["properties"]
        properties.setdefault("ac_name", properties.get("AC_NAME") or properties.get("ac_name") or "")
        properties.setdefault("office", "MLA")
    layers["acs.geojson"] = acs

    pcs = deepcopy(input_data.boundaries["pcs"])
    for feature in pcs["features"]:
        properties = feature["properties"]
        properties.setdefault("pc_name", properties.get("PC_NAME") or properties.get("pc_name") or "")
        properties.setdefault("office", "MP")
    layers["pcs.geojson"] = pcs

    if "districts" in input_data.boundaries:
        districts = deepcopy(input_data.boundaries["districts"])
        for feature in districts["features"]:
            feature["properties"].setdefault("district", feature["properties"].get("DISTRICT", ""))
        layers["districts.geojson"] = districts

    present_osm = []
    for source_name, spec in OSM_LAYERS.items():
        data = input_data.osm_layers.get(source_name)
        if data and data.get("features"):
            layer_id = spec[0]
            layers[f"{layer_id}.geojson"] = deepcopy(data)
            present_osm.append(spec)

    bbox = bbox_of(wards["features"])
    center_x, center_y = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    utm = 32600 + int((center_x + 180) / 6) + 1
    city_yaml = {
        "id": input_data.slug,
        "name": meta["name"],
        "country": "India",
        "state": meta["state"],
        "center": [round(center_x, 4), round(center_y, 4)],
        "bbox": [round(value, 4) for value in bbox],
        "crs_metric": f"EPSG:{utm}",
        "layers_dir": f"data/cities/{input_data.slug}/layers",
        "source_dir": f"data/cities/{input_data.slug}/source",
        "outputs_dir": f"public/cities/{input_data.slug}",
    }
    municipal_commissioner = _officer(input_data.officers, "municipal commissioner") or _officer(input_data.officers, "commissioner")
    police_commissioner = _officer(input_data.officers, "police")
    governance = {
        "city": meta["name"], "council": meta["council"],
        "municipal_commissioner": municipal_commissioner.get("name", ""),
        "mc_service": municipal_commissioner.get("service", ""),
        "police_commissioner": police_commissioner.get("name", ""),
        "pc_service": police_commissioner.get("service", ""),
    }
    manifest = _build_manifest("districts.geojson" in layers, present_osm)
    summary = {
        "slug": input_data.slug,
        "ward_count": len(wards["features"]),
        "councillor_ward_count": sum(1 for feature in wards["features"] if feature["properties"].get("councillors")),
        "ac_count": len(acs["features"]),
        "pc_count": len(pcs["features"]),
        "osm_layer_count": len(present_osm),
        "layers_path": f"data/cities/{input_data.slug}/layers",
        "commissioner": municipal_commissioner.get("name", "?"),
        "council_status": meta["council"]["status"],
        "council_since": meta["council"]["since"],
    }
    return CityBuildArtifacts(
        slug=input_data.slug,
        layers=layers,
        city_yaml=city_yaml,
        governance=governance,
        manifest=manifest,
        summary=summary,
    )


def build_city_from_repository(
    repository: CityBuildInputRepository,
    writer: CityBuildArtifactWriter,
) -> CityBuildArtifacts:
    artifacts = build_city_artifacts(repository.load())
    writer.write(artifacts)
    return artifacts


def city_build_summary_lines(artifacts: CityBuildArtifacts) -> tuple[str, str, str]:
    summary = artifacts.summary
    return (
        f"{summary['slug']}: {summary['ward_count']} wards ({summary['councillor_ward_count']} with councillor), "
        f"{summary['ac_count']} ACs, {summary['pc_count']} PCs, {summary['osm_layer_count']} OSM layers",
        f"  city.yaml + layer_manifest.json + governance.json written to {summary['layers_path']}",
        f"  commissioner: {summary['commissioner']} | council: {summary['council_status']} since {summary['council_since']}",
    )


def wardkey(value) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return str(int(digits)) if digits else ""


def bbox_of(features) -> list[float]:
    xs, ys = [], []

    def walk(coords):
        if coords and isinstance(coords[0], (int, float)):
            xs.append(coords[0])
            ys.append(coords[1])
        else:
            for child in coords:
                walk(child)

    for feature in features:
        walk(feature["geometry"]["coordinates"])
    return [min(xs), min(ys), max(xs), max(ys)]


def _councillor_roster(rows) -> dict[str, dict[str, str]]:
    if not rows:
        return {}
    columns = {column.lower().strip(): column for column in rows[0].keys()}
    ward_column = _pick(columns, "ward_no", "ward", "ward_number", "wardno", "ward_id", "division")
    name_column = _pick(columns, "councillor_name", "corporator_name", "name", "member_name", "councillor")
    party_column = _pick(columns, "party")
    phone_column = _pick(columns, "phone", "contact", "mobile", "phone_number")
    roster: dict[str, dict[str, str]] = {}
    for row in rows:
        key = wardkey(row.get(ward_column, "")) if ward_column else ""
        if not key:
            continue
        roster[key] = {
            "name": (row.get(name_column) or "").strip() if name_column else "",
            "party": (row.get(party_column) or "").strip() if party_column else "",
            "phone": (row.get(phone_column) or "").strip() if phone_column else "",
        }
    return roster


def _pick(columns: Mapping[str, str], *names: str) -> str | None:
    for name in names:
        if name in columns:
            return columns[name]
    return None


def _officer(officers, role: str) -> Mapping[str, str]:
    for officer in officers:
        if role.lower() in (officer.get("role") or "").lower():
            return officer
    return {}


def _build_manifest(has_districts: bool, present_osm) -> dict[str, Any]:
    manifest: dict[str, Any] = {"layers": []}
    manifest["layers"].append({
        "id": "wards", "label": "Wards", "file": "wards.geojson", "kind": "fill",
        "group": "Civic baseline", "default": True, "outline": True,
        "popup": ["Name", "councillors", "councillor_parties", "councillor_phones",
                   "population_2020", "pop_density_km2", "ward_coverage"],
        "paint": {"fill-color": "#1f6f8b", "fill-opacity": 0.18},
    })
    if has_districts:
        manifest["layers"].append({
            "id": "districts", "label": "District boundary", "file": "districts.geojson",
            "kind": "line", "group": "Civic baseline", "default": True, "popup": ["district"],
            "paint": {"line-color": "#c9c2b3", "line-width": 1.3, "line-opacity": 0.55},
        })
    manifest["layers"].append({
        "id": "pcs", "label": "Parliament constituencies", "file": "pcs.geojson",
        "kind": "line", "group": "Public jurisdictions", "default": True,
        "popup": ["pc_name", "office", "representative", "party"],
        "paint": {"line-color": "#d6a946", "line-width": 2.0, "line-opacity": 0.78},
    })
    manifest["layers"].append({
        "id": "acs", "label": "Assembly constituencies", "file": "acs.geojson",
        "kind": "line", "group": "Public jurisdictions", "default": True,
        "popup": ["ac_name", "office", "representative", "party"],
        "paint": {"line-color": "#5c8af2", "line-width": 1.6, "line-opacity": 0.82},
    })
    for layer_id, label, kind, group, default in present_osm:
        if kind == "line":
            paint = {
                "line-color": "#dc4c4c" if layer_id == "metro_lines" else "#58606d",
                "line-width": 2.4 if layer_id == "metro_lines" else 0.5,
                "line-opacity": 0.9 if layer_id == "metro_lines" else 0.4,
            }
        else:
            paint = {
                "circle-color": CIRCLE_COLOR.get(layer_id, "#9ca3ad"),
                "circle-radius": 3.2,
                "circle-stroke-color": "#101318",
                "circle-stroke-width": 0.6,
                "circle-opacity": 0.85,
            }
        manifest["layers"].append({
            "id": layer_id, "label": label, "file": f"{layer_id}.geojson", "kind": kind,
            "group": group, "default": default, "popup": ["name"], "paint": paint,
        })
    return manifest
