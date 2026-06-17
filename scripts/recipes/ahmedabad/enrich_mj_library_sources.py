#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.recipes.library_networks import parse_js_object, plain_text


OUT_DIR = REPO / "data" / "cities" / "ahmedabad" / "source" / "libraries"
DOC_DIR = OUT_DIR / "docs"
TEXT_DIR = OUT_DIR / "docs_text"
IMAGE_DIR = OUT_DIR / "page_images"
CACHE_DIR = Path("/private/tmp/sevent4_mj_library_sources")
CONTENT_JS_URL = "https://mjlibrary.in/assets/frontend/en-lang/content.js"
ABOUT_URL = "https://mjlibrary.in/about-us"


DOCUMENTS = [
    {
        "document_id": "mj_disclosure_2025_26",
        "category": "proactive_disclosure",
        "year": "2025-26",
        "url": "https://mjlibrary.in/assets/img/pdf/mj_discloser_rti_2025-26.pdf",
        "local_name": "mj_discloser_rti_2025-26.pdf",
        "notes": "Current proactive disclosure used for budget, RTI officers, and staff-establishment page 70.",
    },
    {
        "document_id": "amc_library_balbhavan_mj_library_list_2025_07_08",
        "category": "service_locations",
        "year": "2025",
        "url": "https://mjlibrary.in/assets/files/AMC_Library_%20Balbhavan_MJ%20Library_%20List_08_07_2025.pdf",
        "local_name": "amc_library_balbhavan_mj_library_list_2025-07-08.pdf",
        "notes": "Official July 2025 list with AMC library, Balbhavan, and M.J. branch addresses, contacts, and hours.",
    },
    {
        "document_id": "list_of_ccc",
        "category": "rti_submission_civic_centres",
        "year": "",
        "url": "https://mjlibrary.in/assets/img/pdf/list_of_ccc.pdf",
        "local_name": "list_of_ccc.pdf",
        "notes": "AMC city civic centres where applicants can submit RTI/application material; not a library-branch list.",
    },
    {
        "document_id": "admissionformeng",
        "category": "rti_application_form",
        "year": "",
        "url": "https://mjlibrary.in/assets/img/pdf/admissionformeng.pdf",
        "local_name": "admissionformeng.pdf",
        "notes": "RTI Form A for obtaining information; not the M.J. Library membership form.",
    },
    {
        "document_id": "fees_stucture_eng",
        "category": "rti_fee_structure",
        "year": "",
        "url": "https://mjlibrary.in/assets/img/pdf/fees_stucture_eng.pdf",
        "local_name": "fees_stucture_eng.pdf",
        "notes": "RTI fee schedule, not the library membership fee schedule.",
    },
    {
        "document_id": "annual_report",
        "category": "rti_annual_return",
        "year": "2005-06_to_2011-12",
        "url": "https://mjlibrary.in/assets/img/pdf/annual_report.pdf",
        "local_name": "annual_report.pdf",
        "notes": "AMC RTI annual-return statistics linked from M.J. Library RTI page.",
    },
    {
        "document_id": "listpionew",
        "category": "amc_pio_list",
        "year": "",
        "url": "https://mjlibrary.in/assets/img/pdf/listpionew.pdf",
        "local_name": "listpionew.pdf",
        "notes": "Corporation-wide PIO/appellate-officer list linked as NEW; metadata is older, so M.J.-specific 2025-26 disclosure is preferred for current library officers.",
    },
]


STAFF_2025 = [
    ("technical", 1, "Librarian", "67700/208700", "Class 1", "Pay level 1000/-", 1, 0, 1),
    ("technical", 2, "Assistant Librarian", "53100/167800", "Class 2", "", 1, 2, 3),
    ("technical", 3, "Junior Assistant Librarian", "44800/142400", "Class 2", "Motor cycle allowance", 0, 1, 1),
    ("technical", 4, "Technical Assistant", "35400/112400", "Class 3", "", 1, 1, 2),
    ("technical", 5, "Junior Technical Assistant", "25500/81100", "Class 3", "", 2, 0, 2),
    ("technical", 6, "Attendant Library", "19900/63200", "Class 3", "", 17, 31, 48),
    ("administrative", 7, "Office Superintendent", "44800/142400", "Class 2", "", 1, 0, 1),
    ("administrative", 8, "Accountant", "29200/92300", "Class 3", "", 1, 0, 1),
    ("administrative", 9, "Head Clerk", "35400/112400", "Class 3", "", 1, 3, 4),
    ("administrative", 10, "Senior Clerk", "25500/81100", "Class 3", "", 3, 2, 5),
    ("administrative", 11, "Junior Computer-cum-Clerk", "19900/63200", "Class 3", "On deputation from AMC", 1, 2, 3),
    ("isolated", 12, "Junior Computer Programmer", "35400/112400", "Class 3", "", 0, 1, 1),
    ("isolated", 13, "Typist", "25500/81100", "Class 3", "", 3, 0, 3),
    ("isolated", 14, "Event Programmer", "25500/81100", "Class 3", "", 0, 1, 1),
    ("isolated", 15, "Machine Operator", "19900/63200", "Class 3", "", 0, 1, 1),
    ("isolated", 16, "Museum Attendant", "19900/63200", "Class 3", "", 2, 0, 2),
    ("isolated", 17, "Driver", "19900/63200", "Class 3", "Two drivers also noted on daily wage", 1, 2, 3),
    ("class_4", 18, "Nayak", "15700/50000", "Class 4", "", 1, 0, 1),
    ("class_4", 19, "Patawala", "14800/47100", "Class 4", "", 1, 9, 10),
    ("class_4", 20, "Faras", "14800/47100", "Class 4", "", 5, 13, 18),
    ("class_4", 21, "Paniwala Behen", "14800/47100", "Class 4", "", 1, 0, 1),
    ("class_4", 22, "Safai Kamdar", "14800/47100", "Class 4", "", 0, 6, 6),
]


def main() -> None:
    for directory in (DOC_DIR, TEXT_DIR, IMAGE_DIR, CACHE_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    content_js = CACHE_DIR / "content.js"
    fetch(CONTENT_JS_URL, content_js)
    fetch(ABOUT_URL, CACHE_DIR / "about-us.html")
    content = parse_js_object(content_js, "content")

    document_rows = []
    for doc in DOCUMENTS:
        pdf_path = DOC_DIR / doc["local_name"]
        fetch(doc["url"], pdf_path)
        text_path = TEXT_DIR / f"{Path(doc['local_name']).stem}.txt"
        method = export_text(pdf_path, text_path)
        document_rows.append(
            {
                **doc,
                "local_path": rel(pdf_path),
                "text_path": rel(text_path) if text_path.exists() else "",
                "sha256": sha256(pdf_path),
                "bytes": str(pdf_path.stat().st_size),
                "pages": str(pdf_pages(pdf_path)),
                "text_extraction_method": method,
                "fetched_or_refreshed_at": "2026-06-15",
            }
        )

    render_page(DOC_DIR / "admissionformeng.pdf", 1, IMAGE_DIR / "admissionformeng-1.png")
    render_page(DOC_DIR / "mj_discloser_rti_2025-26.pdf", 70, IMAGE_DIR / "mj_discloser_rti_2025-26_page70-70.png")
    ocr_image(IMAGE_DIR / "admissionformeng-1.png", TEXT_DIR / "admissionformeng_ocr.txt", "eng")
    ocr_image(IMAGE_DIR / "mj_discloser_rti_2025-26_page70-70.png", TEXT_DIR / "mj_discloser_rti_2025-26_page70_ocr_guj.txt", "guj+eng")

    write_csv(OUT_DIR / "mj_library_source_documents.csv", document_rows)
    write_csv(OUT_DIR / "mj_library_service_locations_2025.csv", parse_service_locations(DOC_DIR / "amc_library_balbhavan_mj_library_list_2025-07-08.pdf"))
    write_csv(OUT_DIR / "mj_library_staff_establishment_2025.csv", staff_rows())
    write_csv(OUT_DIR / "mj_library_rti_officers_2025.csv", rti_officer_rows())
    write_csv(OUT_DIR / "mj_library_governance_roster_current.csv", governance_rows(content))
    write_csv(OUT_DIR / "mj_library_membership_requirements.csv", membership_rows(content))
    write_csv(OUT_DIR / "mj_library_rti_application_fields.csv", rti_form_rows())
    write_csv(OUT_DIR / "mj_library_civic_centres_rti_submission.csv", parse_civic_centres(DOC_DIR / "list_of_ccc.pdf"))

    print("wrote M.J. Library source-document manifest and normalized source tables")


def fetch(url: str, dest: Path) -> None:
    curl = shutil.which("curl")
    if not curl:
        sys.exit("curl is required")
    subprocess.run([curl, "-L", "--fail", "--silent", "--show-error", "-o", str(dest), url], check=True)


def export_text(pdf_path: Path, text_path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        return "not_available"
    subprocess.run([pdftotext, "-layout", str(pdf_path), str(text_path)], check=True)
    text = text_path.read_text(encoding="utf-8", errors="ignore")
    return "pdftotext -layout" if len(text.strip()) > 50 else "pdftotext minimal_or_image_only"


def render_page(pdf_path: Path, page: int, image_path: Path) -> None:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        return
    prefix = image_path.with_suffix("")
    subprocess.run(
        [pdftoppm, "-r", "300", "-png", "-f", str(page), "-l", str(page), str(pdf_path), str(prefix)],
        check=True,
    )
    generated = prefix.with_name(f"{prefix.name}-{page}").with_suffix(".png")
    if generated.exists() and generated != image_path:
        generated.replace(image_path)


def ocr_image(image_path: Path, text_path: Path, lang: str) -> None:
    tesseract = shutil.which("tesseract")
    if not tesseract or not image_path.exists():
        return
    outbase = text_path.with_suffix("")
    subprocess.run([tesseract, str(image_path), str(outbase), "-l", lang, "--psm", "6"], check=True)


def pdf_pages(pdf_path: Path) -> int:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        return 0
    result = subprocess.run([pdfinfo, str(pdf_path)], check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    return 0


def parse_service_locations(pdf_path: Path) -> list[dict[str, str]]:
    words = pdf_words(pdf_path)
    rows: list[dict[str, str]] = []
    starts = [
        (int(word["text"]), int(word["page"]), float(word["top"]))
        for word in words
        if float(word["left"]) <= 65 and str(word["text"]).isdigit()
    ]
    for index, (sr, page, top) in enumerate(starts):
        section = service_section(page, top)
        if not section:
            continue
        if section == "amc_library" and not 1 <= sr <= 56:
            continue
        if section == "amc_balbhavan" and not 1 <= sr <= 3:
            continue
        if section == "mj_library_branch" and not 1 <= sr <= 6:
            continue

        next_top = None
        for _, later_page, later_top in starts[index + 1 :]:
            if later_page == page and later_top > top:
                next_top = later_top
                break
        end_top = next_top or top + 90
        if page == 6 and section == "amc_library":
            end_top = min(end_top, 175)
        if page == 6 and section == "amc_balbhavan":
            end_top = min(end_top, 350)
        group_words = [
            word
            for word in words
            if int(word["page"]) == page and top - 2 <= float(word["top"]) < end_top
        ]
        rows.append(
            {
                "section": section,
                "source_record_id": str(sr),
                "name": join_col(group_words, 70, 250),
                "area": join_col(group_words, 250, 360),
                "address": join_col(group_words, 360, 585),
                "contact": join_col(group_words, 585, 730),
                "timings_raw": normalize_timing(join_col(group_words, 730, 1000)),
                "source_document": "amc_library_balbhavan_mj_library_list_2025_07_08",
                "source_url": "https://mjlibrary.in/assets/files/AMC_Library_%20Balbhavan_MJ%20Library_%20List_08_07_2025.pdf",
                "confidence": "medium",
                "notes": "Parsed from pdftotext TSV column positions; manually review rows with multi-line timing text before publication.",
            }
        )
    return clean_service_rows(rows)


def service_section(page: int, top: float) -> str:
    if page < 6 or (page == 6 and top < 175):
        return "amc_library"
    if page == 6 and 175 <= top < 350:
        return "amc_balbhavan"
    if page > 6 or (page == 6 and top >= 350):
        return "mj_library_branch"
    return ""


def clean_service_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    overrides = {
        ("amc_library", "56"): {
            "name": "Library Department Head Office",
            "area": "Ellisbridge",
            "address": "Sheth Maneklal Jethabhai Pustakalaya, Ellisbridge, Ahmedabad-380006.",
            "contact": "079-26581229; mobile 9712720533; balbhavanpustakalay@ahmedabadcity.gov.in",
            "timings_raw": "10-30 am to 6.10 pm",
            "confidence": "high",
            "notes": "Manually corrected from the official July 2025 PDF text because the row spans contact and email lines.",
        },
        ("mj_library_branch", "1"): {
            "name": "Sheth Maneklal Jethabhai Pustakalaya",
            "area": "Ellisbridge",
            "address": "Ellisbridge, Ahmedabad-380006.",
            "contact": "079-26578513; 079-26574482; www.mjlibrary.in; mjlibrary@ahmedabadcity.gov.in",
            "timings_raw": "Library 7-30 am to 10-00 pm; book issue/return 7-30 am to 7-30 pm; public holiday close",
        },
        ("mj_library_branch", "2"): {
            "name": "Chandrakant Keshavlal Kastiya Shakha Pustakalay",
            "area": "Vijaynagar",
            "address": "Opp-Block No. 83, Gujarat Housing Board, Vijaynagar, Naranpura, Ahmedabad-380013.",
            "contact": "079-27474968",
            "timings_raw": "Library 7-40 am to 7-40 pm; book issue/return Monday to Friday 8-00 am to 7-30 pm; Saturday 8-00 am to 2-20 pm; public holiday close",
        },
        ("mj_library_branch", "3"): {
            "name": "Kavi Rajendra Keshavlal Shah Shakha Pustakalay",
            "area": "Himmatlalpark",
            "address": "Opp-Gandhigram Sub Zonal Office, Himmatlalpark Char Rasta, Aazad Society, Ahmedabad-380015.",
            "contact": "079-26761159",
            "timings_raw": "Library 7-40 am to 7-40 pm; book issue/return Monday to Friday 8-00 am to 7-30 pm; Saturday 8-00 am to 2-20 pm; public holiday close",
        },
        ("mj_library_branch", "4"): {
            "name": "Gachhadhipati Acharya Shree Subodhsagar Surishvarji Maharaj Shree Shakha Pustakalay",
            "area": "Vasna",
            "address": "Chandranagar Road, Opp-Anjali Char Rasta, Vasna, Ahmedabad-380007.",
            "contact": "079-26607903",
            "timings_raw": "Library 7-40 am to 7-40 pm; book issue/return Monday to Friday 8-00 am to 7-30 pm; Saturday 8-00 am to 2-20 pm; public holiday close",
        },
        ("mj_library_branch", "5"): {
            "name": "Aatma Science & Technology Shakha Pustakalay",
            "area": "Maninagar",
            "address": "Opp-Maninagar Tennis Court, behind Kamla Nehru Udhyan, Uttamnagar, Maninagar, Ahmedabad-380008.",
            "contact": "079-25440035",
            "timings_raw": "Library 7-40 am to 7-40 pm; Sunday and public holiday close",
        },
        ("mj_library_branch", "6"): {
            "name": "Dr. Shyama Prasad Mukharji Vachanalaya",
            "area": "Vejalpur",
            "address": "Dr. Shyama Prashad Mukharji Over Bridge, under 132 Foot Ring Road, Vejalpur, Ahmedabad-380051.",
            "contact": "-",
            "timings_raw": "Monday to Friday 10-30 am to 6-00 pm; Saturday 10-30 am to 2-20 pm; Sunday and public holiday close",
        },
    }
    for row in rows:
        override = overrides.get((row["section"], row["source_record_id"]))
        if not override:
            continue
        row.update(override)
        if row["section"] == "mj_library_branch":
            row["confidence"] = "high"
            row["notes"] = "Manually corrected from the official July 2025 PDF text because M.J. timing/contact cells span multiple lines."
    return rows


def parse_civic_centres(pdf_path: Path) -> list[dict[str, str]]:
    words = pdf_words(pdf_path)
    names = []
    for word in words:
        if 120 <= word["left"] <= 232 and word["text"].isupper() and len(word["text"]) > 2:
            names.append(word)

    rows = []
    for index, word in enumerate(names):
        page = word["page"]
        top = word["top"]
        next_top = None
        for later in names[index + 1 :]:
            if later["page"] == page and later["top"] > top:
                next_top = later["top"]
                break
        group_words = [
            candidate
            for candidate in words
            if candidate["page"] == page and top - 20 <= candidate["top"] < (next_top or top + 70)
        ]
        rows.append(
            {
                "source_record_id": str(len(rows) + 1),
                "zone": join_col(group_words, 65, 125),
                "civic_center_name": join_col(group_words, 120, 232),
                "address": join_col(group_words, 232, 386),
                "phone": join_col(group_words, 386, 486),
                "timings_raw": normalize_timing(join_col(group_words, 486, 610)),
                "source_document": "list_of_ccc",
                "source_url": "https://mjlibrary.in/assets/img/pdf/list_of_ccc.pdf",
                "confidence": "low",
                "notes": "City Civic Centre means AMC public service counter for submitting applications/RTI material; parser uses column positions and should be reviewed.",
            }
        )
    return rows


def pdf_words(pdf_path: Path) -> list[dict[str, object]]:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        return []
    tsv_path = CACHE_DIR / f"{pdf_path.stem}.tsv"
    subprocess.run([pdftotext, "-tsv", str(pdf_path), str(tsv_path)], check=True)
    rows: list[dict[str, object]] = []
    with tsv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("level") != "5":
                continue
            text = row.get("text", "").strip()
            if not text or text == "###PAGE###":
                continue
            rows.append(
                {
                    "page": int(row["page_num"]),
                    "left": float(row["left"]),
                    "top": float(row["top"]),
                    "text": text,
                }
            )
    return sorted(rows, key=lambda row: (row["page"], row["top"], row["left"]))


def row_groups(words: list[dict[str, object]], *, sr_x_max: float) -> list[dict[str, object]]:
    starts = []
    for word in words:
        text = str(word["text"])
        if word["left"] <= sr_x_max and text.isdigit():
            starts.append((int(text), int(word["page"]), float(word["top"])))
    groups = []
    for index, (sr, page, top) in enumerate(starts):
        next_top = None
        for _, later_page, later_top in starts[index + 1 :]:
            if later_page == page and later_top > top:
                next_top = later_top
                break
        group_words = [
            word
            for word in words
            if int(word["page"]) == page and top - 2 <= float(word["top"]) < (next_top or top + 44)
        ]
        groups.append({"sr": sr, "page": page, "top": top, "words": group_words})
    return groups


def join_col(words: list[dict[str, object]], left: float, right: float) -> str:
    selected = [word for word in words if left <= float(word["left"]) < right]
    selected.sort(key=lambda word: (float(word["top"]), float(word["left"])))
    return " ".join(str(word["text"]) for word in selected).replace(" ,", ",").strip()


def normalize_timing(value: str) -> str:
    return " ".join(value.replace("Fariday", "Friday").split())


def governance_rows(content: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    order = ["79", "80", "84", "81", "82", "83", "85", "86"]
    basis = {
        "79": "Mayor, Amdavad Municipal Corporation; Chairman",
        "80": "Chairman, Library Standing Committee",
        "81": "Member, Sheth M.J. Library management committee; Chairman, School Board, Ahmedabad",
        "82": "Scholar member, Sheth M.J. Library management committee",
        "83": "Scholar member, Sheth M.J. Library management committee",
        "84": "Deputy Municipal Commissioner (Library)",
        "85": "Municipal Chief Auditor",
        "86": "Municipal Secretary",
    }
    rows = []
    for key in order:
        entry = content.get(f"instruction-{key}", {})
        text = plain_text(entry.get("eng", ""))
        name = text.split("  ")[0].strip() if "  " in text else text.split("Member")[0].split("Mayor")[0].split("Chairman")[0].strip()
        rows.append(
            {
                "source_key": f"instruction-{key}",
                "name": name,
                "role_or_title": basis[key],
                "raw_english": text,
                "source_url": ABOUT_URL,
                "source_status": "live_about_us_content_js",
                "currentness_note": "Live page uses language keys from content.js; municipal office-holders still need cross-check against AMC current office rosters.",
            }
        )
    return rows


def membership_rows(content: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    keys = ["45", "196", "197", "199", "201"]
    rows = []
    for key in keys:
        rows.append(
            {
                "source_key": f"instruction-{key}",
                "requirement_type": {
                    "45": "counter_membership_documents",
                    "196": "eligibility",
                    "197": "documents",
                    "199": "fees",
                    "201": "member_entitlements",
                }[key],
                "raw_english": plain_text(content.get(f"instruction-{key}", {}).get("eng", "")),
                "source_url": ABOUT_URL,
                "notes": "Official about-us/membership section.",
            }
        )
    rows.extend(
        [
            {
                "source_key": "about_us_membership_form_documentType",
                "requirement_type": "online_kyc_dropdown",
                "raw_english": "Online form documentType options: Aadhar card; Driving Licence; voter id card.",
                "source_url": ABOUT_URL,
                "notes": "Online KYC choices are narrower than the older counter-membership rules, which also name ration card and passport as residence/photo proof alternatives.",
            },
            {
                "source_key": "instruction-275",
                "requirement_type": "digital_or_physical_registration_workflow",
                "raw_english": plain_text(content.get("instruction-275", {}).get("eng", "")),
                "source_url": ABOUT_URL,
                "notes": "FAQ workflow says digital-only registration asks for valid mobile; physical M.J. membership asks for KYC.",
            },
            {
                "source_key": "instruction-281",
                "requirement_type": "digital_vs_physical_eligibility",
                "raw_english": plain_text(content.get("instruction-281", {}).get("eng", "")),
                "source_url": ABOUT_URL,
                "notes": "FAQ language differs from membership section; keep both as evidence.",
            },
            {
                "source_key": "instruction-303",
                "requirement_type": "alternate_registration_faq",
                "raw_english": plain_text(content.get("instruction-303", {}).get("eng", "")),
                "source_url": ABOUT_URL,
                "notes": "A second FAQ block again makes mobile/OTP central and adds guarantor name/mobile plus KYC for M.J. membership.",
            },
        ]
    )
    return rows


def staff_rows() -> list[dict[str, str]]:
    rows = []
    for category, serial, title, pay_band, class_group, allowance, filled, vacant, total in STAFF_2025:
        rows.append(
            {
                "as_of_date": "2025-07-31",
                "category": category,
                "serial": str(serial),
                "post_title_en": title,
                "pay_band": pay_band,
                "class_or_grade": class_group,
                "allowance_or_note": allowance,
                "filled_posts": str(filled),
                "vacant_posts": str(vacant),
                "sanctioned_posts": str(total),
                "source_document": "mj_disclosure_2025_26",
                "source_page": "70",
                "source_url": "https://mjlibrary.in/assets/img/pdf/mj_discloser_rti_2025-26.pdf",
                "confidence": "medium",
                "notes": "Translated from Gujarati page image; totals reconcile to 43 filled, 75 vacant, 118 sanctioned.",
            }
        )
    return rows


def rti_officer_rows() -> list[dict[str, str]]:
    return [
        {
            "as_of_source_year": "2025-26",
            "rti_role": "appellate_officer",
            "name": "Dr. Bipinbhai J. Modi",
            "designation": "Librarian",
            "office_phone": "079-26578513; 079-26574482",
            "fax": "079-26586908",
            "mobile": "9328303366",
            "email": "mjlibrary@ahmedabadcity.gov.in",
            "address": "M.J. Library, Ellisbridge, Ahmedabad - 380006",
            "source_document": "mj_disclosure_2025_26",
            "source_page_note": "Proactive Disclosure 16",
        },
        {
            "as_of_source_year": "2025-26",
            "rti_role": "public_information_officer",
            "name": "Shri Yogeshkumar J. Patel",
            "designation": "Junior Assistant Librarian",
            "office_phone": "079-26574482",
            "fax": "",
            "mobile": "9426344225",
            "email": "vrajraj2001@gmail.com",
            "address": "M.J. Library, Ellisbridge, Ahmedabad - 380006",
            "source_document": "mj_disclosure_2025_26",
            "source_page_note": "Proactive Disclosure 16",
        },
        {
            "as_of_source_year": "2025-26",
            "rti_role": "public_information_officer",
            "name": "Shri Rameshbhai P. Ganvit",
            "designation": "Officer Incharge Library, Municipal Library Department",
            "office_phone": "079-26574482",
            "fax": "",
            "mobile": "9712720533",
            "email": "ganvitramesh@yahoo.com",
            "address": "M.J. Library, Ellisbridge, Ahmedabad - 380006",
            "source_document": "mj_disclosure_2025_26",
            "source_page_note": "Proactive Disclosure 16",
        },
    ]


def rti_form_rows() -> list[dict[str, str]]:
    fields = [
        ("name", "Name of the Applicant", "personal_identity", "Required field on RTI Form A."),
        ("full_address", "Full Address", "contact_or_residence", "Required field on RTI Form A."),
        ("information_required", "Particulars of information required in brief", "request_scope", "Substantive RTI request field."),
        ("declaration_section_8_9", "Statement that information is not exempt under section 8 or section 9", "legal_declaration", "Standard RTI declaration language."),
        ("fee_payment", "Fee paid / demand draft / pay order / non-judicial stamp", "payment", "Fee route; BPL applicants exempt."),
        ("bpl_document", "BPL card or certificate copy if claiming BPL status", "concession_document", "Only applies to fee waiver claim."),
        ("signature", "Signature of Applicant", "authentication", "Signature field."),
        ("email", "Email address if any", "contact", "Optional email field."),
        ("telephone", "Telephone office/residence", "contact", "Optional telephone field."),
    ]
    return [
        {
            "field_id": field_id,
            "field_label": label,
            "field_type": field_type,
            "privacy_note": note,
            "source_document": "admissionformeng",
            "source_url": "https://mjlibrary.in/assets/img/pdf/admissionformeng.pdf",
            "interpretation": "This is an RTI application form, not a library membership/admission form.",
        }
        for field_id, label, field_type, note in fields
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
