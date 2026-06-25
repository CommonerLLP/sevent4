"""Pure OpenCity acquisition planning for Bengaluru recipes."""
from __future__ import annotations

import re

BOUNDARY_SPINE = {
    "wards": {
        "target": "wards.geojson",
        "dataset": "https://data.opencity.in/dataset/gba-wards-delimitation-2025",
        "resource": "https://data.opencity.in/dataset/863209cb-4ced-4f51-b5c5-156939c50922/resource/9013d656-8051-4e2d-9648-46efd0d86d3d/download/gba-369-wards-december-2025.kml",
        "publisher": "Greater Bengaluru Authority (GBA)",
        "label": "GBA Final Wards (369) — December 2025",
    },
    "wards_bbmp198": {
        "target": "wards_bbmp198.geojson",
        "dataset": "https://data.opencity.in/dataset/bbmp-wards-delimitation-2023",
        "resource": "https://data.opencity.in/dataset/7b492849-a5cb-439b-89e9-e03522055e6a/resource/7857d752-dda4-4e5e-b9e6-53146372f86b/download/b272c5b2-3e66-4b0f-a59f-35ec7b4caa1e.kml",
        "publisher": "Bruhat Bengaluru Mahanagara Palike (BBMP)",
        "label": "BBMP Final Wards Map 2023 (198) — historical join layer",
    },
    "acs": {
        "target": "acs.geojson",
        "dataset": "https://data.opencity.in/dataset/karnataka-and-bengaluru-assembly-constituency-maps",
        "resource": "https://data.opencity.in/dataset/f80a1ff2-a1f2-442a-aff0-f332acd14ae6/resource/c1c04138-0eeb-4e5f-b1ef-6932dbcd23c0/download/28add4af-0ee5-4f13-9c64-0e5b3927c321.kml",
        "publisher": "Karnataka State Election Commission / ECI",
        "label": "Bengaluru Assembly Constituencies Map",
    },
    "pcs": {
        "target": "pcs.geojson",
        "dataset": "https://data.opencity.in/dataset/karnataka-and-bengaluru-parliamentary-constituency-maps",
        "resource": "https://data.opencity.in/dataset/f4eea943-d4ef-484a-a636-8de9ca0b7497/resource/4ae8e478-8cbc-45ca-be75-e7e32938d11a/download/fb4523e8-985d-4f0a-815e-025504c3b9a9.kml",
        "publisher": "Election Commission of India (ECI)",
        "label": "Bengaluru Urban Parliamentary Constituencies Map",
    },
}

FINANCE_SLUGS = [
    "bbmp-budget",
    "bbmp-budget-2023-24",
    "bbmp-budget-2024-25",
    "bbmp-budget-2025-26",
    "bbmp-work-orders-by-ward-2013-2022",
    "bbmp-work-orders-and-bill-payment",
    "bengaluru-mla-local-area-development-funds",
]
FINANCE_KEEP = {"CSV", "XLSX", "XLS", "JSON", "GEOJSON"}

JURISDICTION_SLUGS = [
    "bda-jurisdiction-and-boundary",
    "greater-bengaluru-authority-corporations-delimitation-2025",
    "bwssb-boundary-maps",
    "bwssb-sewerage-line-maps-for-bengaluru",
    "bengaluru-traffic-police-jurisdictions",
    "bbmp-solid-waste-management-data",
    "bengaluru-zone-wise-streetlights",
    "bus-stops-and-routes-map-by-ward",
]
JURISDICTION_KEEP = {"KML", "KMZ", "GEOJSON"}
PER_DATASET_CAP = 40

BDA = "Bangalore Development Authority (BDA)"
GBA = "Greater Bengaluru Authority (GBA)"
BWSSB = "Bangalore Water Supply and Sewerage Board (BWSSB)"
TP = "Bengaluru Traffic Police"
BBMP = "Bruhat Bengaluru Mahanagara Palike (BBMP)"

CURATED_JURISDICTION_LAYERS = [
    {"id": "gba_corporations", "slug": "greater-bengaluru-authority-corporations-delimitation-2025",
     "file": "Greater_Bengaluru_Authority_Five_Corporations_Map_-_September_2025.kml",
     "pub": GBA, "simplify": 0.0002},
    {"id": "gba_zones", "slug": "greater-bengaluru-authority-corporations-delimitation-2025",
     "file": "GBA_Zones_2025.kml", "pub": GBA, "simplify": 0.0002},
    {"id": "bda_zones", "slug": "bda-jurisdiction-and-boundary",
     "file": "BDA_Zones_and_Subdivisions.geojson", "pub": BDA, "simplify": 0.0002},
    {"id": "bwssb_divisions", "slug": "bwssb-boundary-maps",
     "file": "BWSSB_Division_Boundary_Maps.kml", "pub": BWSSB, "simplify": 0.0002},
    {"id": "traffic_police_jurisdiction", "slug": "bengaluru-traffic-police-jurisdictions",
     "file": "Bengaluru_Traffic_Police_Jurisdictions_Map_2022.kml", "pub": TP, "simplify": 0.0002},
    {"id": "bbmp_dry_waste_centres", "slug": "bbmp-solid-waste-management-data",
     "file": "BBMP_Dry_Waste_Collection_Centres_Map.kml", "pub": BBMP, "simplify": 0.0},
    {"id": "bbmp_landfills", "slug": "bbmp-solid-waste-management-data",
     "file": "BBMP_Landfill_Locations_Map.kml", "pub": BBMP, "simplify": 0.0},
]

KML_CRUFT = {
    "id", "Name", "description", "timestamp", "begin", "end", "altitudeMode",
    "tessellate", "extrude", "visibility", "drawOrder", "icon", "snippet",
    "fid", "layer",
}


def safe_filename(name: str, fallback: str, limit: int = 90) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (name or "").strip())[:limit].strip("_")
    return cleaned or fallback


def finance_download_jobs(catalogue: dict, slugs: list[str] | None = None) -> tuple[list[dict], list[str]]:
    wanted = slugs or FINANCE_SLUGS
    by_slug = {dataset["name"]: dataset for dataset in catalogue.get("datasets", [])}
    jobs: list[dict] = []
    missing: list[str] = []
    for slug in wanted:
        dataset = by_slug.get(slug)
        if not dataset:
            missing.append(slug)
            continue
        for index, resource in enumerate(dataset.get("resources", [])):
            fmt = (resource.get("format") or "").upper()
            if fmt not in FINANCE_KEEP:
                continue
            filename = f"{safe_filename(resource.get('name') or '', f'res_{index}')}.{fmt.lower()}"
            jobs.append(
                {
                    "slug": slug,
                    "filename": filename,
                    "url": resource["url"],
                    "record": {
                        "slug": slug,
                        "dataset_title": dataset["title"],
                        "publisher_org": dataset["organization"],
                        "opencity_dataset": dataset["url"],
                        "resource_name": resource.get("name"),
                        "resource_url": resource["url"],
                        "format": fmt,
                        "file": f"{slug}/{filename}",
                        "last_modified": resource.get("last_modified"),
                    },
                }
            )
    return jobs, missing


def jurisdiction_resource_jobs(package_meta: dict, slug: str, cap: int = PER_DATASET_CAP) -> list[dict]:
    result = package_meta["result"]
    organization = (result.get("organization") or {}).get("title", "?")
    license_title = result.get("license_title", "?")
    dataset_url = f"https://data.opencity.in/dataset/{slug}"
    resources = [
        resource for resource in result.get("resources", [])
        if (resource.get("format") or "").upper() in JURISDICTION_KEEP
    ][:cap]
    jobs = []
    for index, resource in enumerate(resources):
        fmt = (resource.get("format") or "kml").upper()
        filename = f"{safe_filename(resource.get('name') or resource.get('id'), f'r{index}', limit=80)}.{fmt.lower()}"
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
                    "local": f"data/cities/bengaluru/source/opencity/_raw/{slug}/{filename}",
                },
            }
        )
    return jobs


def boundary_provenance_record(layer_id: str, spec: dict, size: int, converted: dict) -> dict[str, object]:
    return {
        "layer": layer_id,
        "file": spec["target"],
        "features": converted["features"],
        "publisher_org": spec["publisher"],
        "opencity_dataset": spec["dataset"],
        "resource_url": spec["resource"],
        "format_source": "KML",
        "processor": "sevent4 (scripts/recipes/bengaluru/acquire_boundaries.py)",
        "retrieved": "2026-06-11",
        "bytes": size,
        "columns": converted.get("columns", []),
    }
