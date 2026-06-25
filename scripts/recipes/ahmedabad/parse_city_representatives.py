#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sevent4.adapters.representatives_filesystem import (
    CsvCouncillorWriter,
    JsonRepresentativeOfficerWriter,
    PdfTextExtractor,
    WardRepresentativeLayerReader,
    WardRepresentativeLayerWriter,
)
from sevent4.application.representatives import (
    CITY_OFFICERS,
    build_ward_representative_document,
    parse_ahmedabad_councillor_rows,
    validate_councillor_rows,
)


REPO = Path(__file__).resolve().parents[3]
DEFAULT_CITY = "ahmedabad"


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

    pdf = (
        Path(args.pdf)
        if args.pdf
        else REPO
        / "data"
        / "cities"
        / city
        / "source"
        / "representatives"
        / "docs"
        / "ward_councillors_2026_27.pdf"
    )
    wards = Path(args.wards) if args.wards else REPO / "data" / "cities" / city / "layers" / "wards.geojson"
    out_csv = (
        Path(args.out_csv)
        if args.out_csv
        else REPO / "data" / "cities" / city / "source" / "representatives" / "ward_councillors_2026_27.csv"
    )
    officers_path = (
        Path(args.officers)
        if args.officers
        else REPO / "data" / "cities" / city / "source" / "representatives" / "city_officers.json"
    )

    if not pdf.exists():
        sys.exit(f"Missing councillor PDF: {pdf}")

    ward_layer = WardRepresentativeLayerReader(wards)
    rows = parse_ahmedabad_councillor_rows(PdfTextExtractor().extract_text(pdf), ward_layer.ward_name_from_no)
    try:
        validate_councillor_rows(rows)
    except ValueError as exc:
        sys.exit(str(exc))

    if args.dry_run:
        print(f"parsed {len(rows)} councillor rows")
        print(f"first: {rows[0]['ward_name']} -> {rows[0]['councillor_name_gu']} {rows[0]['phones']}")
        print(f"last: {rows[-1]['ward_name']} -> {rows[-1]['councillor_name_gu']} {rows[-1]['phones']}")
        return

    officers = CITY_OFFICERS[city]
    CsvCouncillorWriter(out_csv).write_rows(rows)
    JsonRepresentativeOfficerWriter(officers_path).write_officers(city, officers)
    WardRepresentativeLayerWriter(wards).write_document(
        build_ward_representative_document(ward_layer.read_document(), rows, officers[0])
    )
    print(f"wrote {out_csv}")
    print(f"wrote {officers_path}")
    print(f"updated {wards}")


if __name__ == "__main__":
    main()
