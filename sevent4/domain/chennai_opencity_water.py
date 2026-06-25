"""Pure OpenCity acquisition planning for Chennai water and flood layers."""
from __future__ import annotations

import re


KEEP = {"KML", "KMZ"}
SLUGS = [
    "chennai-stormwater-drain-swd-maps",
    "chennai-flooding-data",
    "chennai-sewage-pumping-network",
    "chennai-sewerage-collection-system",
    "chennai-water-distribution-stations",
    "cmwssb-administrative-boundaries",
]

KML_CRUFT = {
    "id",
    "Name",
    "description",
    "timestamp",
    "begin",
    "end",
    "altitudeMode",
    "tessellate",
    "extrude",
    "visibility",
    "drawOrder",
    "icon",
    "snippet",
}

GCC = "Greater Chennai Corporation (GCC)"
CMWSSB = "Chennai Metropolitan Water Supply and Sewerage Board (CMWSSB)"
DRAIN_KEEP = [
    "DRAIN_TYPE",
    "DRAIN_SIZE",
    "DRAIN_DEP",
    "DRAIN_WID",
    "DRAIN_LEN",
    "MAT_TYP",
    "SWD_MAT",
    "STATUS",
    "COVER",
    "FUND",
    "CONTRACTOR",
    "CONST_DATE",
    "RECONST",
    "WARD",
    "ZONE",
    "ST_NAME",
    "LOCATION",
    "WATER_FLOW",
    "RD_CLASS",
]

CURATED_WATER_LAYERS = [
    {
        "id": "flood_hazard",
        "slug": "chennai-flooding-data",
        "file": "Chennai_Flood_Hazard_Zones_Map.kml",
        "pub": GCC,
        "centroid": False,
        "simplify": 0.0001,
        "keep": ["CATEGORY"],
    },
    {
        "id": "flood_inundation",
        "slug": "chennai-flooding-data",
        "file": "Chennai_Inundation_Points_with_Depth_of_Inundation.kml",
        "pub": GCC,
        "centroid": False,
        "simplify": 0.0,
        "keep": ["DEPTH", "F_REMARKS", "WARD", "ZONE"],
    },
    {
        "id": "flood_2015",
        "slug": "chennai-flooding-data",
        "file": "Chennai_Flooding_Points_in_2015.kml",
        "pub": GCC,
        "centroid": False,
        "simplify": 0.0,
        "keep": ["ZONE", "DIVISION"],
    },
    {
        "id": "stormwater_drains",
        "slug": "chennai-stormwater-drain-swd-maps",
        "file": "Chennai_Storm_Water_Drains_-_SWD_-_Map_2023.kml",
        "pub": GCC,
        "centroid": False,
        "simplify": 0.00003,
        "keep": DRAIN_KEEP,
    },
    {
        "id": "cmwssb_depots",
        "slug": "cmwssb-administrative-boundaries",
        "file": "Depot_Boundaries_Map.kml",
        "pub": CMWSSB,
        "centroid": False,
        "simplify": 0.0001,
        "keep": ["depot", "dae_range", "se_territory", "area_in_sqkm"],
    },
    {
        "id": "sewer_command_area",
        "slug": "chennai-sewerage-collection-system",
        "file": "Sewerage_Command_Area.kml",
        "pub": CMWSSB,
        "centroid": False,
        "simplify": 0.0001,
        "keep": ["name_of_the_sps", "area_no_of_the_sps", "length_of_sewer_m", "no_of_mh", "se_territory_of_the_sps", "status"],
    },
    {
        "id": "water_overhead_tanks",
        "slug": "chennai-water-distribution-stations",
        "file": "Water_Supply_Overhead_Tanks.kml",
        "pub": CMWSSB,
        "centroid": True,
        "simplify": 0.0,
        "keep": ["location", "depot", "capacity_of_oht_ml", "name_of_the_wds", "commissioned_on", "status"],
    },
]


def safe_filename(value: str, fallback: str, limit: int = 80) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip())[:limit].strip("_")
    return cleaned or fallback


def water_resource_jobs(package_meta: dict, slug: str) -> list[dict]:
    result = package_meta["result"]
    organization = (result.get("organization") or {}).get("title", "?")
    license_title = result.get("license_title", "?")
    dataset_url = f"https://data.opencity.in/dataset/{slug}"
    resources = [
        resource for resource in result.get("resources", [])
        if (resource.get("format") or "").upper() in KEEP
    ]
    jobs = []
    for index, resource in enumerate(resources):
        fmt = (resource.get("format") or "kml").upper()
        filename = f"{safe_filename(resource.get('name') or resource.get('id'), f'r{index}')}.{fmt.lower()}"
        jobs.append(
            {
                "slug": slug,
                "filename": filename,
                "url": resource["url"],
                "record": {
                    "dataset_slug": slug,
                    "dataset_url": dataset_url,
                    "organization": organization,
                    "license": license_title,
                    "resource_name": resource.get("name"),
                    "format": fmt,
                    "resource_url": resource["url"],
                    "local": f"data/cities/chennai/source/opencity/_raw/{slug}/{filename}",
                },
            }
        )
    return jobs
