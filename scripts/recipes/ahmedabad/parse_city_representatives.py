#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]

# Ahmedabad is the first implemented representative parser. Other cities will
# need city-specific roster parsing because municipal source formats vary.
DEFAULT_CITY = "ahmedabad"
DEFAULT_COUNCILLOR_URL = "https://ahmedabadcity.gov.in/ViewFile/ViewFile?TYPE=FileRepository,2638"
DEFAULT_CONTACT_DIRECTORY_URL = "https://ahmedabad.gujarat.gov.in/assets/downloads/AMC_Contact_Directory_.pdf"

GUJARATI_DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")
ZONE_RE = re.compile(
    r"(ઉતર\s+પિ\s*મ\s+ઝોન|દ\s*ણ\s+પિ\s*મ\s+ઝોન|પિ\s*મ\s+ઝોન|મ\s*ય\s+ઝોન|ઉતર\s+ઝોન|દ\s*ણ\s+ઝોન|ૂવ\s+ઝોન)"
)
PHONE_RE = re.compile(r"\b[6-9]\d{9}\b")

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse public city representative documents and join them to city layers.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Ahmedabad is implemented first.")
    parser.add_argument("--pdf", help="Ward councillor PDF path.")
    parser.add_argument("--wards", help="Ward layer to update.")
    parser.add_argument("--out-csv", help="Parsed councillor CSV output path.")
    parser.add_argument("--officers", help="City officer JSON output path.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and validate without writing outputs.")
    args = parser.parse_args()

    city = args.city.lower()
    if city != "ahmedabad":
        sys.exit("Only the Ahmedabad representative parser is implemented.")

    pdf = Path(args.pdf) if args.pdf else REPO / "data" / "cities" / city / "source" / "representatives" / "docs" / "ward_councillors_2026_27.pdf"
    wards = Path(args.wards) if args.wards else REPO / "data" / "cities" / city / "layers" / "wards.geojson"
    out_csv = Path(args.out_csv) if args.out_csv else REPO / "data" / "cities" / city / "source" / "representatives" / "ward_councillors_2026_27.csv"
    officers_path = Path(args.officers) if args.officers else REPO / "data" / "cities" / city / "source" / "representatives" / "city_officers.json"

    rows = parse_councillors(pdf)
    validate_rows(rows)
    if args.dry_run:
        print(f"parsed {len(rows)} councillor rows")
        print(f"first: {rows[0]['ward_name']} -> {rows[0]['councillor_name_gu']} {rows[0]['phones']}")
        print(f"last: {rows[-1]['ward_name']} -> {rows[-1]['councillor_name_gu']} {rows[-1]['phones']}")
        return

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv(rows, out_csv)
    officers_path.write_text(
        json.dumps({"city": city, "items": CITY_OFFICERS[city]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    update_ward_layer(wards, rows, CITY_OFFICERS[city][0])
    print(f"wrote {out_csv}")
    print(f"wrote {officers_path}")
    print(f"updated {wards}")


def parse_councillors(pdf: Path) -> list[dict[str, str]]:
    if not pdf.exists():
        sys.exit(f"Missing councillor PDF: {pdf}")
    result = subprocess.run(
        ["pdftotext", "-raw", str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    blocks = _serial_blocks(result.stdout)
    rows: list[dict[str, str]] = []
    for block in blocks:
        serial = int(re.match(r"^(\d{1,3})", block[0]).group(1))
        ward_no = (serial - 1) // 4 + 1
        ward_name = _ward_name_from_no(ward_no)
        ward_name_gu, zone_gu, councillor_name_gu = _name_parts(block)
        phones = "; ".join(dict.fromkeys(PHONE_RE.findall("\n".join(block))))
        rows.append(
            {
                "serial": str(serial),
                "ward_no": f"{ward_no:02d}",
                "ward_name": ward_name,
                "ward_name_gu": ward_name_gu,
                "zone_gu": zone_gu,
                "councillor_name_gu": councillor_name_gu,
                "councillor_name_en": "",
                "party": _party("\n".join(block)),
                "phones": phones,
                "source_url": DEFAULT_COUNCILLOR_URL,
                "source_document": "data/cities/ahmedabad/source/representatives/docs/ward_councillors_2026_27.pdf",
                "raw_text": " | ".join(block),
            }
        )
    return rows


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
    else:
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


def _ward_name_from_no(ward_no: int) -> str:
    wards = json.loads((REPO / "data" / "cities" / "ahmedabad" / "layers" / "wards.geojson").read_text(encoding="utf-8"))
    for feature in wards["features"]:
        name = str(feature["properties"].get("Name", ""))
        match = re.match(r"^(\d+)\s+", name)
        if match and int(match.group(1)) == ward_no:
            return name
    return f"{ward_no:02d}"


def validate_rows(rows: list[dict[str, str]]) -> None:
    if len(rows) != 192:
        sys.exit(f"Expected 192 councillor rows, parsed {len(rows)}")
    by_ward: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_ward[row["ward_no"]].append(row)
    bad = {ward_no: len(items) for ward_no, items in by_ward.items() if len(items) != 4}
    if len(by_ward) != 48 or bad:
        sys.exit(f"Ward grouping failed: {bad}")


def write_csv(rows: list[dict[str, str]], out_csv: Path) -> None:
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def update_ward_layer(wards_path: Path, rows: list[dict[str, str]], commissioner: dict[str, str]) -> None:
    data = json.loads(wards_path.read_text(encoding="utf-8"))
    by_ward: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_ward[row["ward_no"]].append(row)
    for feature in data["features"]:
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
    wards_path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _councillor_summary(row: dict[str, str]) -> str:
    phones = row["phones"].replace("; ", ", ")
    if row["councillor_name_en"] and row["councillor_name_gu"]:
        name = f"{row['councillor_name_en']} ({row['councillor_name_gu']})"
    else:
        name = row["councillor_name_en"] or row["councillor_name_gu"]
    return " · ".join(part for part in (name, row["party"], phones) if part)


if __name__ == "__main__":
    main()
