#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_DIR = Path("/private/tmp/dpl-targeted-20260613")
DEFAULT_OUT_DIR = REPO / "data" / "cities" / "delhi" / "source" / "libraries"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Delhi Public Library finance/operations metrics.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_tsv(args.source_dir / "selected_finance_operations_links.tsv")
    write_manifest(args.source_dir, args.out_dir, manifest)

    source_by_stem = {
        Path(row["local_path"]).stem: row["url"]
        for row in manifest
        if row.get("url") and row.get("local_path")
    }
    annual_rows = extract_annual_rows(args.source_dir / "text", source_by_stem)
    write_csv(
        args.out_dir / "dpl_annual_metrics.csv",
        annual_rows,
        [
            "year",
            "source_file",
            "source_url",
            "adult_members",
            "child_members",
            "total_members",
            "adult_issues",
            "child_issues",
            "total_issues",
            "reading_room_attendance",
            "collection_total",
            "books_added_to_stock",
            "opening_unspent_rs",
            "grant_received_rs",
            "other_income_rs",
            "total_available_rs",
            "returned_to_ministry_rs",
            "total_expenditure_rs",
            "closing_unspent_rs",
            "confidence",
            "notes",
        ],
    )
    latest = one_year(annual_rows, "2023-24")
    long_rows = latest_long_metrics(latest)
    write_csv(
        args.out_dir / "dpl_metrics_long.csv",
        long_rows,
        [
            "library_system",
            "place",
            "year",
            "metric_group",
            "metric_name",
            "value",
            "unit",
            "source_url",
            "confidence",
            "notes",
        ],
    )
    print(f"wrote {args.out_dir / 'dpl_fetch_manifest.csv'} ({len(manifest)} rows)")
    print(f"wrote {args.out_dir / 'dpl_annual_metrics.csv'} ({len(annual_rows)} rows)")
    print(f"wrote {args.out_dir / 'dpl_metrics_long.csv'} ({len(long_rows)} rows)")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_manifest(source_dir: Path, out_dir: Path, manifest: list[dict[str, str]]) -> None:
    rows: list[dict[str, str]] = []
    for row in manifest:
        local = source_dir / row["local_path"].removeprefix("targeted/")
        valid_pdf = ""
        if local.exists() and local.suffix.lower() == ".pdf":
            valid_pdf = "1" if local.read_bytes()[:5] == b"%PDF-" else "0"
        rows.append(
            {
                "kind": row["kind"],
                "text": row["text"],
                "url": row["url"],
                "local_path": row["local_path"],
                "status": row["status"],
                "bytes": row["bytes"],
                "sha256": row["sha256"],
                "valid_pdf": valid_pdf,
                "repo_storage": "manifest_only",
                "notes": "Raw targeted source artifact retained outside git under /private/tmp unless promoted separately.",
            }
        )
    write_csv(
        out_dir / "dpl_fetch_manifest.csv",
        rows,
        ["kind", "text", "url", "local_path", "status", "bytes", "sha256", "valid_pdf", "repo_storage", "notes"],
    )


def extract_annual_rows(text_dir: Path, source_by_stem: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(text_dir.glob("annual__*.txt")):
        if "account" in path.name.lower():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        year = report_year(path.name, text)
        if not year:
            continue
        table = membership_table(text)
        summary = membership_summary(text)
        attendance = first_number_after(text, r"Attendance of readers in Reading Rooms\s*:?\s*-?\s*")
        collection = collection_total(text)
        books_added = first_number_after(text, r"Books added to Stock\s*:?\s*")
        finance = finance_total_row(text)
        row = {
            "year": year,
            "source_file": path.name,
            "source_url": source_by_stem.get(path.stem, ""),
            "adult_members": "",
            "child_members": "",
            "total_members": "",
            "adult_issues": "",
            "child_issues": "",
            "total_issues": "",
            "reading_room_attendance": str(attendance or ""),
            "collection_total": str(collection or ""),
            "books_added_to_stock": str(books_added or ""),
            "opening_unspent_rs": "",
            "grant_received_rs": "",
            "other_income_rs": "",
            "total_available_rs": "",
            "returned_to_ministry_rs": "",
            "total_expenditure_rs": "",
            "closing_unspent_rs": "",
            "confidence": "medium",
            "notes": "",
        }
        if table:
            (
                row["adult_members"],
                row["child_members"],
                row["total_members"],
                row["adult_issues"],
                row["child_issues"],
                row["total_issues"],
            ) = [str(value) for value in table]
            row["confidence"] = "high"
            row["notes"] = "Membership and issue metrics parsed from reconciled unit total table."
        elif summary:
            row["adult_members"], row["child_members"], row["total_members"], row["total_issues"] = [
                str(value or "") for value in summary
            ]
            row["notes"] = "Membership and issue metrics parsed from summary line; no unit total table found."
        if finance:
            (
                row["opening_unspent_rs"],
                row["grant_received_rs"],
                row["other_income_rs"],
                row["total_available_rs"],
                row["returned_to_ministry_rs"],
                row["total_expenditure_rs"],
                row["closing_unspent_rs"],
            ) = [str(value) for value in finance]
        if year == "2023-24":
            row["notes"] += " 2023-24 summary line has inconsistent adult/child subtotals; reconciled unit table used."
        if not any(row.get(key) for key in ("total_members", "total_issues", "collection_total", "total_expenditure_rs")):
            continue
        rows.append(row)
    return sorted(rows, key=lambda row: row["year"])


def report_year(filename: str, text: str) -> str:
    haystack = f"{filename}\n{text[:2500]}"
    match = re.search(r"(20\d{2})\s*[-–_]\s*(20\d{2}|\d{2})", haystack)
    if not match:
        return ""
    start = match.group(1)
    end = match.group(2)[-2:]
    return f"{start}-{end}"


def membership_table(text: str) -> tuple[int, int, int, int, int, int] | None:
    lower = text.lower()
    start = lower.find("statement showing membership")
    if start == -1:
        start = lower.find("details of membership")
    if start == -1:
        return None
    chunk = text[start : start + 3000]
    matches = re.findall(
        r"(?im)^\s*Total\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
        chunk,
    )
    if not matches:
        return None
    return tuple(parse_int(value) for value in matches[-1])  # type: ignore[return-value]


def membership_summary(text: str) -> tuple[int | None, int | None, int | None, int | None] | None:
    member = re.search(
        r"Total Membership[^\n:]*?\([^\n]*?Adult[-\s]*([0-9, ]+)[^\n]*?Children[-\s]*([0-9, ]+)\)[^:\n]*:\s*([0-9, ]+)",
        text,
        re.I,
    )
    issued = re.search(r"No\. of Books issued[^\n:]*:\s*([0-9, ]+)", text, re.I)
    if not member:
        return None
    return (
        parse_int(member.group(1)),
        parse_int(member.group(2)),
        parse_int(member.group(3)),
        parse_int(issued.group(1)) if issued else None,
    )


def collection_total(text: str) -> int | None:
    match = re.search(r"book collection(?: \(Net Book Stock\))?.{0,220}?was\s+([0-9,]+)", text, re.I | re.S)
    return parse_int(match.group(1)) if match else None


def finance_total_row(text: str) -> tuple[int, int, int, int, int, int, int] | None:
    lower = text.lower()
    start = lower.find("unspent balance")
    if start == -1:
        return None
    chunk = text[start : start + 2500]
    matches = re.findall(
        r"TOTAL\s+([0-9,./-]+)\s+([0-9,./-]+)\s+([0-9,./-]+)\s+([0-9,./-]+)\s+([0-9,./-]+)\s+([0-9,./-]+)\s+([0-9,./-]+)",
        chunk,
        re.I,
    )
    if not matches:
        return None
    return tuple(parse_int(value) for value in matches[-1])  # type: ignore[return-value]


def first_number_after(text: str, prefix_pattern: str) -> int | None:
    match = re.search(prefix_pattern + r"([0-9, ]+)", text, re.I)
    return parse_int(match.group(1)) if match else None


def parse_int(value: str) -> int:
    value = re.sub(r"\.\d+\b", "", value)
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else 0


def one_year(rows: list[dict[str, str]], year: str) -> dict[str, str]:
    for row in rows:
        if row["year"] == year:
            return row
    raise KeyError(year)


def latest_long_metrics(latest: dict[str, str]) -> list[dict[str, str]]:
    source_url = latest["source_url"]
    rows: list[dict[str, str]] = []

    def add(group: str, name: str, value: int | float | str, unit: str, confidence: str = "high", notes: str = "") -> None:
        rows.append(
            {
                "library_system": "Delhi Public Library",
                "place": "NCT of Delhi",
                "year": "2023-24",
                "metric_group": group,
                "metric_name": name,
                "value": str(value),
                "unit": unit,
                "source_url": source_url,
                "confidence": confidence,
                "notes": notes,
            }
        )

    for key, name in [
        ("collection_total", "collection_total"),
        ("books_added_to_stock", "books_added_to_stock"),
        ("total_members", "registered_members"),
        ("adult_members", "adult_members"),
        ("child_members", "child_members"),
        ("total_issues", "annual_issues"),
        ("adult_issues", "adult_issues"),
        ("child_issues", "child_issues"),
        ("reading_room_attendance", "reading_room_attendance"),
        ("grant_received_rs", "grant_received"),
        ("other_income_rs", "other_income"),
        ("total_expenditure_rs", "total_expenditure"),
        ("closing_unspent_rs", "closing_unspent_balance"),
    ]:
        if latest.get(key):
            add("reported", name, latest[key], "INR" if key.endswith("_rs") else "count")

    service_counts = {
        "central_library": 1,
        "zonal_libraries": 1,
        "branch_libraries": 3,
        "sub_branch_libraries": 18,
        "community_libraries": 1,
        "resettlement_colony_libraries": 7,
        "braille_libraries": 1,
        "mobile_library_buses": 8,
        "mobile_service_points": 101,
        "book_reading_centres": 30,
        "fixed_library_units": 32,
        "fixed_plus_mobile_buses": 40,
        "public_access_touchpoints_including_mobile_stops": 163,
    }
    for name, value in service_counts.items():
        add("network", name, value, "count", notes="Service composition from DPL annual report 2023-24.")

    staff_counts = {
        "staff_sanctioned": 274,
        "staff_filled": 138,
        "staff_vacant": 136,
        "professional_staff_sanctioned": 199,
        "non_professional_staff_sanctioned": 75,
        "professional_staff_filled": 97,
        "non_professional_staff_filled": 41,
        "professional_staff_vacant": 102,
        "non_professional_staff_vacant": 34,
    }
    for name, value in staff_counts.items():
        add("staffing", name, value, "count", notes="Sanctioned/filled/vacant post table from DPL annual report 2023-24.")

    finance_items = {
        "books_and_reading_material_expense": 1756817,
        "book_purchase_expense": 1304894,
        "periodicals_newspapers_expense": 311143,
        "binding_expense": 127670,
        "membership_drive_expense": 13570,
    }
    for name, value in finance_items.items():
        add("finance_detail", name, value, "INR", notes="Financial expenditure at a glance from DPL annual report 2023-24.")
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
