#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "data" / "comparators" / "library_ifla_audit"
IFLA_REF = REPO / "data" / "reference" / "ifla" / "library_map_metrics.csv"

KPI_FIELDS = [
    "city",
    "library_system",
    "metric_name",
    "ifla_label",
    "status",
    "value",
    "year",
    "source_path",
    "notes",
    "request_priority",
]

GOV_FIELDS = [
    "city",
    "library_system",
    "role",
    "name",
    "source_status",
    "source_path",
    "term_start_month",
    "term_end_month",
    "professional_qualifications",
    "notes",
    "request_priority",
]

SERVICE_DETAIL_FIELDS = [
    "city",
    "library_system",
    "detail_field",
    "locations_with_value",
    "total_locations",
    "status",
    "source_path",
    "notes",
    "request_priority",
]

LEGAL_FIELDS = [
    "city",
    "library_system",
    "instrument_or_body",
    "governance_level",
    "source_status",
    "source_path_or_url",
    "what_it_governs",
    "known_gap",
    "request_priority",
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_DIR / "ifla_library_kpi_audit.csv", ifla_rows(), KPI_FIELDS)
    write_csv(OUT_DIR / "library_governance_contacts.csv", governance_rows(), GOV_FIELDS)
    write_csv(OUT_DIR / "branch_service_detail_audit.csv", service_detail_rows(), SERVICE_DETAIL_FIELDS)
    write_csv(OUT_DIR / "library_legal_governance_audit.csv", legal_rows(), LEGAL_FIELDS)
    print(f"wrote {OUT_DIR.relative_to(REPO)}")


def ifla_rows() -> list[dict[str, str]]:
    refs = {row["metric_name"]: row for row in read_csv(IFLA_REF)}
    ahm_stats = latest_csv_row(REPO / "data/cities/ahmedabad/source/libraries/mj_library_annual_stats.csv")
    dpl_metrics = metric_values(REPO / "data/cities/delhi/source/libraries/dpl_metrics_long.csv")
    dpl_hierarchy = latest_csv_row(REPO / "data/cities/delhi/derived/library_access/dpl_service_hierarchy_summary.csv")
    ahm_locations = read_csv(REPO / "data/cities/ahmedabad/source/libraries/ahmedabad_library_locations.csv")

    rows: list[dict[str, str]] = []

    def add(city: str, system: str, metric: str, status: str, value: str, year: str, source: str, notes: str, priority: str = "") -> None:
        ref = refs[metric]
        rows.append(
            {
                "city": city,
                "library_system": system,
                "metric_name": metric,
                "ifla_label": ref["ifla_label"],
                "status": status,
                "value": value,
                "year": year,
                "source_path": source,
                "notes": notes,
                "request_priority": priority,
            }
        )

    ahm_system = "Sheth M.J. Library / Ahmedabad municipal library network"
    ahm_year = ahm_stats["year"]
    ahm_source = "data/cities/ahmedabad/source/libraries/mj_library_annual_stats.csv"
    add("ahmedabad", ahm_system, "service_points", "available", str(len(ahm_locations)), "current_extract", "data/cities/ahmedabad/source/libraries/ahmedabad_library_locations.csv", "AMC/M.J. location inventory has 83 geocoded library rows.")
    add("ahmedabad", ahm_system, "libraries_with_internet_access", "partial", "1+", "current_site_capture", "data/cities/ahmedabad/source/libraries/mj_library_site_content.json", "M.J. site says Wi-Fi is available at M.J. Library; branch-wise internet availability is not disclosed.", "ask_librarian")
    add("ahmedabad", ahm_system, "full_time_staff", "missing", "", "", "", "No network-level FTE/full-time staff count found in the curated public extract.", "rti_or_request")
    add("ahmedabad", ahm_system, "volunteers", "missing", "", "", "", "No volunteer count found in the curated public extract.", "low")
    add("ahmedabad", ahm_system, "registered_users", "available", ahm_stats["network_total_with_gyanvihar"], ahm_year, ahm_source, "Registered member roll, including annual, lifetime, and Gyanvihar members.")
    add("ahmedabad", ahm_system, "physical_visits", "missing", "", "", "", "Gate/physical visit count is not in the curated M.J. disclosure table.", "rti_or_request")
    add("ahmedabad", ahm_system, "physical_loans", "available", ahm_stats["circulation_total"], ahm_year, ahm_source, "M.J. annual circulation/issue count.")
    add("ahmedabad", ahm_system, "ebook_loans", "missing", "", "", "", "Digital/e-book loan count is not in the curated public extract.", "ask_librarian")
    add("ahmedabad", ahm_system, "audio_book_loans", "missing", "", "", "", "Audio/talking-book loan count is not in the curated public extract.", "ask_librarian")
    add("ahmedabad", ahm_system, "downloads", "missing", "", "", "", "Digital download count is not in the curated public extract.", "ask_librarian")

    dpl_system = "Delhi Public Library"
    dpl_year = "2023-24"
    dpl_source = "data/cities/delhi/source/libraries/dpl_metrics_long.csv"
    add("delhi", dpl_system, "service_points", "partial", dpl_hierarchy["total_locations"], "current_extract", "data/cities/delhi/derived/library_access/dpl_service_hierarchy_summary.csv", "111 DPL-published/geocoded locations are in the working hierarchy; DPL annual report also reports a broader 163-touchpoint inclusive count.")
    add("delhi", dpl_system, "libraries_with_internet_access", "missing", "", "", "", "No branch-wise internet-access count found in the curated DPL extract.", "rti_or_request")
    add("delhi", dpl_system, "full_time_staff", "partial", dpl_metrics.get("staff_filled", ""), dpl_year, dpl_source, "DPL reports filled posts, but not a clean IFLA full-time/FTE field in the current extract.", "clarify_with_dpl")
    add("delhi", dpl_system, "volunteers", "missing", "", "", "", "No volunteer count found in the curated DPL extract.", "low")
    add("delhi", dpl_system, "registered_users", "available", dpl_metrics.get("registered_members", ""), dpl_year, dpl_source, "DPL registered members from annual report.")
    add("delhi", dpl_system, "physical_visits", "partial", dpl_metrics.get("reading_room_attendance", ""), dpl_year, dpl_source, "DPL reports reading-room attendance, not total branch visits.", "clarify_with_dpl")
    add("delhi", dpl_system, "physical_loans", "available", dpl_metrics.get("annual_issues", ""), dpl_year, dpl_source, "DPL annual book issues.")
    add("delhi", dpl_system, "ebook_loans", "missing", "", "", "", "No e-book loan count found in the curated DPL extract.", "rti_or_request")
    add("delhi", dpl_system, "audio_book_loans", "missing", "", "", "", "No audio-book loan count found in the curated DPL extract.", "rti_or_request")
    add("delhi", dpl_system, "downloads", "missing", "", "", "", "No digital-download count found in the curated DPL extract.", "rti_or_request")
    return rows


def governance_rows() -> list[dict[str, str]]:
    return [
        {
            "city": "ahmedabad",
            "library_system": "Sheth M.J. Library / Ahmedabad municipal library network",
            "role": "Librarian",
            "name": "Dr Bipin J Modi",
            "source_status": "official_site_capture",
            "source_path": "data/cities/ahmedabad/source/libraries/mj_library_site_content.json#instruction-176",
            "term_start_month": "",
            "term_end_month": "",
            "professional_qualifications": "",
            "notes": "Official M.J. site-content capture lists him as Librarian. Appointment month, term length/end, and qualifications are not in the current extract.",
            "request_priority": "ask_librarian",
        },
        {
            "city": "ahmedabad",
            "library_system": "Sheth M.J. Library / Ahmedabad municipal library network",
            "role": "Assistant Librarian",
            "name": "Mr. YogeshKumar J Patel",
            "source_status": "official_site_capture",
            "source_path": "data/cities/ahmedabad/source/libraries/mj_library_site_content.json#instruction-177",
            "term_start_month": "",
            "term_end_month": "",
            "professional_qualifications": "",
            "notes": "Official M.J. site-content capture lists him as Assistant Librarian.",
            "request_priority": "ask_librarian",
        },
        {
            "city": "ahmedabad",
            "library_system": "Sheth M.J. Library / Ahmedabad municipal library network",
            "role": "Municipal Director",
            "name": "Shri Prashant Pandya",
            "source_status": "official_site_capture",
            "source_path": "data/cities/ahmedabad/source/libraries/mj_library_site_content.json#instruction-356",
            "term_start_month": "",
            "term_end_month": "",
            "professional_qualifications": "",
            "notes": "Administrative/library management contact, not necessarily the head librarian.",
            "request_priority": "confirm_current",
        },
        {
            "city": "ahmedabad",
            "library_system": "Sheth M.J. Library / Ahmedabad municipal library network",
            "role": "I/C Deputy Municipal Commissioner (Library)",
            "name": "Mr. Deepak Trivedi",
            "source_status": "official_site_capture",
            "source_path": "data/cities/ahmedabad/source/libraries/mj_library_site_content.json#instruction-372",
            "term_start_month": "",
            "term_end_month": "",
            "professional_qualifications": "",
            "notes": "Administrative AMC-side library contact; current tenure and qualifications not in extract.",
            "request_priority": "confirm_current",
        },
        {
            "city": "delhi",
            "library_system": "Delhi Public Library",
            "role": "Delhi Library Board",
            "name": "Delhi Library Board",
            "source_status": "official_manifest_only",
            "source_path": "data/cities/delhi/source/libraries/dpl_fetch_manifest.csv",
            "term_start_month": "",
            "term_end_month": "",
            "professional_qualifications": "",
            "notes": "DPL RTI manifest includes Annexure-I: Functions and powers of Delhi Library Board. Board composition, member terms, and current office-holders need the PDF/raw page promoted or re-fetched.",
            "request_priority": "rti_or_refetch",
        },
        {
            "city": "delhi",
            "library_system": "Delhi Public Library",
            "role": "Director General",
            "name": "Dr. R. K. Sharma",
            "source_status": "secondary_web_unverified",
            "source_path": "https://en.wikipedia.org/wiki/Delhi_Public_Library",
            "term_start_month": "",
            "term_end_month": "",
            "professional_qualifications": "",
            "notes": "Secondary source lists Dr. R. K. Sharma as Director. DPL live site fetch timed out in this session; confirm from DPL staff directory/annual report before publication.",
            "request_priority": "confirm_current",
        },
    ]


def service_detail_rows() -> list[dict[str, str]]:
    delhi = latest_csv_row(REPO / "data/cities/delhi/derived/library_access/dpl_service_hierarchy_summary.csv")
    ahm_total = str(len(read_csv(REPO / "data/cities/ahmedabad/source/libraries/ahmedabad_library_locations.csv")))
    rows = []
    for city, system, total, source, values in [
        (
            "ahmedabad",
            "Sheth M.J. Library / Ahmedabad municipal library network",
            ahm_total,
            "data/cities/ahmedabad/source/libraries/ahmedabad_library_locations.csv",
            {"max_seating_capacity": "", "opening_hours": "", "branch_collection_size": "", "collection_types": ""},
        ),
        (
            "delhi",
            "Delhi Public Library",
            delhi["total_locations"],
            "data/cities/delhi/derived/library_access/dpl_service_hierarchy_summary.csv",
            {
                "max_seating_capacity": delhi["branchwise_seating_capacity_locations"],
                "opening_hours": delhi["branchwise_opening_hours_locations"],
                "branch_collection_size": delhi["branchwise_collection_size_locations"],
                "collection_types": delhi["branchwise_collection_type_locations"],
            },
        ),
    ]:
        for field in ("max_seating_capacity", "opening_hours", "branch_collection_size", "collection_types"):
            count = values[field]
            rows.append(
                {
                    "city": city,
                    "library_system": system,
                    "detail_field": field,
                    "locations_with_value": count or "0",
                    "total_locations": total,
                    "status": "missing_branchwise_public_detail",
                    "source_path": source,
                    "notes": "Branch-wise field not available in the current public extract; request from librarian/board or file RTI.",
                    "request_priority": "rti_or_request",
                }
            )
    return rows


def legal_rows() -> list[dict[str, str]]:
    return [
        {
            "city": "delhi",
            "library_system": "Delhi Public Library",
            "instrument_or_body": "Delhi Library Board",
            "governance_level": "central/autonomous-library-board",
            "source_status": "official_manifest_only",
            "source_path_or_url": "data/cities/delhi/source/libraries/dpl_fetch_manifest.csv",
            "what_it_governs": "DPL RTI manifest lists Annexure-I: Functions and powers of Delhi Library Board.",
            "known_gap": "Board composition, current chair/members, appointment dates, member terms, and by-laws need the Annexure-I PDF/raw page promoted or re-fetched.",
            "request_priority": "rti_or_refetch",
        },
        {
            "city": "delhi",
            "library_system": "Delhi Public Library",
            "instrument_or_body": "Delivery of Books and Newspapers (Public Libraries) Act, 1954",
            "governance_level": "union_statutory-deposit",
            "source_status": "secondary_web_unverified",
            "source_path_or_url": "https://en.wikipedia.org/wiki/Delhi_Public_Library",
            "what_it_governs": "DPL is described as a recipient/depository library under the Act.",
            "known_gap": "Need primary Act text and DPL-specific notification/order before publication.",
            "request_priority": "primary_source",
        },
        {
            "city": "delhi",
            "library_system": "Delhi Public Library",
            "instrument_or_body": "Ministry of Culture autonomous-body grant/annual-report framework",
            "governance_level": "union-administrative",
            "source_status": "official_derived_extract",
            "source_path_or_url": "data/cities/delhi/source/libraries/dpl_metrics_long.csv",
            "what_it_governs": "Annual reports and grant/expenditure data show DPL as centrally funded through Ministry of Culture disclosures.",
            "known_gap": "Need memorandum/rules/by-laws of the autonomous body and current delegation of powers.",
            "request_priority": "rti_or_request",
        },
        {
            "city": "ahmedabad",
            "library_system": "Sheth M.J. Library / Ahmedabad municipal library network",
            "instrument_or_body": "M.J. Library Board / Library Committee",
            "governance_level": "municipal-library-board",
            "source_status": "official_site_capture",
            "source_path_or_url": "data/cities/ahmedabad/source/libraries/mj_library_site_content.json",
            "what_it_governs": "Official site capture lists Library Committee, M.J. Library Board references, library staff, librarian decision powers, and management-committee appeal powers.",
            "known_gap": "Need formal constitution/by-laws, current board membership, appointment dates, term lengths, and librarian qualifications.",
            "request_priority": "ask_librarian",
        },
        {
            "city": "ahmedabad",
            "library_system": "Sheth M.J. Library / Ahmedabad municipal library network",
            "instrument_or_body": "Gujarat Provincial Municipal Corporations Act, 1949 / AMC municipal structure",
            "governance_level": "municipal-corporation",
            "source_status": "secondary_web_unverified",
            "source_path_or_url": "https://en.wikipedia.org/wiki/Ahmedabad_Municipal_Corporation",
            "what_it_governs": "AMC structure includes the Municipal Commissioner, committees, M.J. Library Board, and Granthpal/library function in public descriptions.",
            "known_gap": "Need primary GPMC Act provisions and AMC rules/resolutions specific to library governance.",
            "request_priority": "primary_source",
        },
    ]


def metric_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in read_csv(path):
        values[row["metric_name"]] = row["value"]
    return values


def latest_csv_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[-1] if rows else {}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
