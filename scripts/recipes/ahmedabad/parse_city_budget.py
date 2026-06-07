#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]

# Ahmedabad is the first city parser. Other cities should add their local
# language/table labels here as their public budget formats are studied.
DEFAULT_CITY = "ahmedabad"

GUJARATI_DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")

LABELS_BY_CITY = {
    "ahmedabad": {
        "revenue_exp": r"રેવન્યુ\s*ખર્ચ.*કુલ|મહેસૂલી\s*ખર્ચ.*કુલ",
        "capital_transfer": r"કેપીટલ\s*એકાઉન્ટ.*ટ્રાન્સફર|કેપીટલ\s*એકા.*ટ્રાન",
        "capital_exp": r"કેપીટલ\s*ખર્ચ.*કુલ|મૂડી\s*ખર્ચ.*કુલ",
        "loan_charges": r"લોન\s*ચાર્જ",
        "grand_total": r"એકંદરે?\s*કુલ",
    }
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse OCR-derived city budget summary candidates.")
    parser.add_argument("--city", default=DEFAULT_CITY, help="City id. Ahmedabad parser labels are implemented first.")
    parser.add_argument("--ocr-dir", help="Directory containing OCR text files.")
    parser.add_argument("--out", help="Output CSV path.")
    args = parser.parse_args()

    city = args.city.lower()
    labels = LABELS_BY_CITY.get(city)
    if not labels:
        sys.exit(f"No budget parser labels for city={city!r}. Add LABELS_BY_CITY rules first.")

    ocr_dir = Path(args.ocr_dir) if args.ocr_dir else REPO / "data" / "cities" / city / "source" / "budget" / "ocr_capex_opex"
    out = Path(args.out) if args.out else REPO / "data" / "cities" / city / "layers" / "budget_capex_opex.csv"
    if not ocr_dir.exists():
        sys.exit(f"No OCR directory found: {ocr_dir}")

    rows = []
    for path in sorted(ocr_dir.glob("*.txt")):
        if path.name.startswith("_"):
            continue
        year = path.stem
        record = parse_ocr_file(path, labels)
        row = {"year": year}
        for key in labels:
            value = record.get(key)
            row[f"{key}_candidates"] = "|".join(str(num) for num in value["numbers"]) if value else ""
            row[f"{key}_raw"] = value["raw"] if value else ""
        rows.append(row)
        found = [key for key in labels if key in record]
        print(f"{year}: found {len(found)}/{len(labels)} labels -> {', '.join(found)}")

    columns = ["year"]
    columns.extend(f"{key}_candidates" for key in labels)
    columns.extend(f"{key}_raw" for key in labels)

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out} ({len(rows)} years). OCR-derived; verify before using as final finance data.")


def parse_ocr_file(path: Path, labels: dict[str, str]) -> dict[str, dict[str, object]]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    record: dict[str, dict[str, object]] = {}
    for key, pattern in labels.items():
        for line in lines:
            if re.search(pattern, line):
                values = numbers(line)
                if values:
                    record[key] = {"numbers": values, "raw": line.strip()[:180]}
                    break
    return record


def numbers(line: str) -> list[float]:
    line = line.translate(GUJARATI_DIGITS)
    tokens = re.findall(r"-?\d[\d,]*\.?\d*", line)
    values = []
    for token in tokens:
        try:
            value = float(token.replace(",", ""))
        except ValueError:
            continue
        if value != 0:
            values.append(value)
    return values


if __name__ == "__main__":
    main()
