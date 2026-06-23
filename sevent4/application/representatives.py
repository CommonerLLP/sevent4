from __future__ import annotations

import re
from collections import defaultdict
from typing import Callable, Iterable, Mapping


DEFAULT_COUNCILLOR_URL = "https://ahmedabadcity.gov.in/ViewFile/ViewFile?TYPE=FileRepository,2638"
DEFAULT_CONTACT_DIRECTORY_URL = "https://ahmedabad.gujarat.gov.in/assets/downloads/AMC_Contact_Directory_.pdf"
GUJARATI_DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")
ZONE_RE = re.compile(
    r"(ઉતર\s+પિ\s*મ\s+ઝોન|દ\s*ણ\s+પિ\s*મ\s+ઝોન|પિ\s*મ\s+ઝોન|મ\s*ય\s+ઝોન|ઉતર\s+ઝોન|દ\s*ણ\s+ઝોન|ૂવ\s+ઝોન)"
)
PHONE_RE = re.compile(r"\b[6-9]\d{9}\b")


CITY_REPRESENTATIVE_SOURCES = {
    "ahmedabad": [
        {
            "id": "ward_councillors_2026_27",
            "label": "Councillors 2026-27",
            "url": DEFAULT_COUNCILLOR_URL,
            "notes": "AMC ward councillor names and information.",
        },
        {
            "id": "standing_committee_english_2026_27",
            "label": "Standing Committee Member List - English",
            "url": "https://ahmedabadcity.gov.in/ViewFile/ViewFile?TYPE=FileRepository,2645",
            "notes": "AMC Standing Committee member list in English.",
        },
    ]
}

CITY_OFFICERS = {
    "ahmedabad": [
        {
            "office": "Municipal Commissioner",
            "name": "Shri Banchhanidhi Pani, IAS",
            "phone_office": "079-25391811",
            "fax": "079-25354638",
            "email": "mc@ahmedabadcity.gov.in",
            "source_url": DEFAULT_CONTACT_DIRECTORY_URL,
        }
    ]
}


def build_representative_source_manifest(
    city: str,
    sources: Iterable[Mapping[str, str]],
    path_for_source: Callable[[Mapping[str, str]], str],
) -> dict:
    rows = []
    for source in sources:
        rows.append({**source, "city": city, "path": path_for_source(source)})
    return {"city": city, "items": rows}


def parse_ahmedabad_councillor_rows(
    text: str,
    ward_name_from_no: Callable[[int], str],
    *,
    source_url: str = DEFAULT_COUNCILLOR_URL,
    source_document: str = "data/cities/ahmedabad/source/representatives/docs/ward_councillors_2026_27.pdf",
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for block in _serial_blocks(text):
        serial_match = re.match(r"^(\d{1,3})", block[0])
        if not serial_match:
            continue
        serial = int(serial_match.group(1))
        ward_no = (serial - 1) // 4 + 1
        ward_name_gu, zone_gu, councillor_name_gu = _name_parts(block)
        phones = "; ".join(dict.fromkeys(PHONE_RE.findall("\n".join(block))))
        rows.append(
            {
                "serial": str(serial),
                "ward_no": f"{ward_no:02d}",
                "ward_name": ward_name_from_no(ward_no),
                "ward_name_gu": ward_name_gu,
                "zone_gu": zone_gu,
                "councillor_name_gu": councillor_name_gu,
                "councillor_name_en": "",
                "party": _party("\n".join(block)),
                "phones": phones,
                "source_url": source_url,
                "source_document": source_document,
                "raw_text": " | ".join(block),
            }
        )
    return rows


def validate_councillor_rows(
    rows: list[Mapping[str, str]],
    *,
    expected_rows: int = 192,
    expected_wards: int = 48,
    councillors_per_ward: int = 4,
) -> None:
    if len(rows) != expected_rows:
        raise ValueError(f"Expected {expected_rows} councillor rows, parsed {len(rows)}")
    by_ward: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        by_ward[str(row["ward_no"])].append(row)
    bad = {ward_no: len(items) for ward_no, items in by_ward.items() if len(items) != councillors_per_ward}
    if len(by_ward) != expected_wards or bad:
        raise ValueError(f"Ward grouping failed: {bad}")


def build_ward_representative_document(
    ward_document: dict,
    rows: list[Mapping[str, str]],
    commissioner: Mapping[str, str],
) -> dict:
    document = {
        **ward_document,
        "features": [
            {
                **feature,
                "properties": dict(feature.get("properties", {})),
                "geometry": feature.get("geometry"),
            }
            for feature in ward_document.get("features", [])
        ],
    }
    by_ward: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        by_ward[str(row["ward_no"])].append(row)
    for feature in document["features"]:
        props = feature["properties"]
        match = re.match(r"^(\d+)\s+", str(props.get("Name", "")))
        if not match:
            continue
        ward_no = f"{int(match.group(1)):02d}"
        councillors = by_ward[ward_no]
        props["ward_no"] = ward_no
        props["councillor_count"] = str(len(councillors))
        props["councillors_gu"] = "; ".join(row["councillor_name_gu"] for row in councillors if row["councillor_name_gu"])
        props["councillors_en"] = "; ".join(row["councillor_name_en"] for row in councillors if row["councillor_name_en"])
        props["councillors"] = props["councillors_gu"]
        props["councillor_parties"] = "; ".join(row["party"] for row in councillors if row["party"])
        props["councillor_phones"] = "; ".join(row["phones"] for row in councillors if row["phones"])
        props["councillor_summaries"] = "; ".join(_councillor_summary(row) for row in councillors)
        props["councillor_roster_status"] = "AMC Gujarati roster parsed; names need OCR/manual verification before public display"
        props["councillor_source"] = DEFAULT_COUNCILLOR_URL
        props["municipal_commissioner"] = commissioner["name"]
        props["municipal_commissioner_phone"] = commissioner["phone_office"]
        props["municipal_commissioner_email"] = commissioner["email"]
        props["municipal_commissioner_source"] = commissioner["source_url"]
    return document


def _serial_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] | None = None
    expected = 1
    for line in text.translate(GUJARATI_DIGITS).splitlines():
        clean = " ".join(line.strip().split())
        if not clean:
            continue
        match = re.match(r"^(\d{1,3})(?:\s+|$)", clean)
        if match and int(match.group(1)) == expected:
            if current:
                blocks.append(current)
            current = [clean]
            expected += 1
        elif current:
            current.append(clean)
    if current:
        blocks.append(current)
    return blocks


def _name_parts(block: list[str]) -> tuple[str, str, str]:
    first = block[0]
    serial = re.match(r"^(\d{1,3})", first).group(1)
    payload = first[len(serial) :].strip()
    lines = ([payload] if payload else []) + block[1:]
    for start in range(len(lines)):
        for end in range(start + 1, min(start + 4, len(lines)) + 1):
            candidate = " ".join(lines[start:end])
            zone_match = ZONE_RE.search(candidate)
            if not zone_match:
                continue
            before_zone = candidate[: zone_match.start()].strip()
            after_zone = candidate[zone_match.end() :].strip()
            ward_parts = lines[:start]
            if before_zone:
                ward_parts.append(before_zone)
            name_parts: list[str] = []
            if after_zone:
                name_parts.append(after_zone)
            for line in lines[end:]:
                if _looks_like_address_or_party(line):
                    break
                name_parts.append(line)
            return " ".join(ward_parts).strip(), zone_match.group(1).strip(), _clean_name(" ".join(name_parts))
    return "", "", _clean_name(lines[0] if lines else "")


def _clean_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value.rstrip(" ,")


def _looks_like_address_or_party(line: str) -> bool:
    if PHONE_RE.search(line) or "ભાજપ" in line or "ક ેસ" in line or "ક ે સ" in line:
        return True
    return bool(re.search(r"\d|,|અમદાવાદ|સામે|પાસે|રોડ|સોસાયટ|એપાટ", line))


def _party(text: str) -> str:
    if "ભાજપ" in text:
        return "BJP"
    if re.search(r"ક\s*ે\s*સ", text):
        return "INC"
    return ""


def _councillor_summary(row: Mapping[str, str]) -> str:
    phones = row["phones"].replace("; ", ", ")
    if row["councillor_name_en"] and row["councillor_name_gu"]:
        name = f"{row['councillor_name_en']} ({row['councillor_name_gu']})"
    else:
        name = row["councillor_name_en"] or row["councillor_name_gu"]
    return " · ".join(part for part in (name, row["party"], phones) if part)
