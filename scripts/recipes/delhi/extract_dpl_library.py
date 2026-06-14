#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
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
    location_rows = extract_dpl_locations(args.source_dir / "html", source_by_stem)
    write_csv(
        args.out_dir / "dpl_library_locations.csv",
        location_rows,
        DPL_LOCATION_FIELDS,
    )
    geocode_dir = REPO / "data" / "cities" / "delhi" / "source" / "geocoding"
    geocode_dir.mkdir(parents=True, exist_ok=True)
    cache_rows = geocode_cache_rows(location_rows)
    write_csv(
        geocode_dir / "geocode_cache.csv",
        cache_rows,
        GEOCODE_CACHE_FIELDS,
    )
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
    population = primary_delhi_population()
    ten_year_rows = ten_year_time_series(annual_rows, population)
    online_rows = online_annual_time_series(annual_rows, population)
    write_csv(
        args.out_dir / "dpl_ten_year_time_series.csv",
        ten_year_rows,
        [
            "year",
            "fiscal_start_year",
            "fiscal_end_year",
            "observation_status",
            "source_url",
            "total_members",
            "total_issues",
            "reading_room_attendance",
            "collection_total",
            "books_added_to_stock",
            "total_expenditure_rs",
            "population_denominator",
            "members_per_1m",
            "issues_per_1m",
            "reading_room_attendance_per_1m",
            "collection_refresh_pct",
            "issues_per_collection_item",
            "notes",
        ],
    )
    write_csv(
        args.out_dir / "dpl_online_annual_time_series.csv",
        online_rows,
        [
            "year",
            "fiscal_start_year",
            "fiscal_end_year",
            "observation_status",
            "source_url",
            "total_members",
            "total_issues",
            "reading_room_attendance",
            "collection_total",
            "books_added_to_stock",
            "total_expenditure_rs",
            "population_denominator",
            "members_per_1m",
            "issues_per_1m",
            "reading_room_attendance_per_1m",
            "collection_refresh_pct",
            "issues_per_collection_item",
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
    print(f"wrote {args.out_dir / 'dpl_ten_year_time_series.csv'} ({len(ten_year_rows)} rows)")
    print(f"wrote {args.out_dir / 'dpl_online_annual_time_series.csv'} ({len(online_rows)} rows)")
    print(f"wrote {args.out_dir / 'dpl_metrics_long.csv'} ({len(long_rows)} rows)")
    print(f"wrote {args.out_dir / 'dpl_library_locations.csv'} ({len(location_rows)} rows)")
    print(f"wrote {geocode_dir / 'geocode_cache.csv'} ({len(cache_rows)} rows)")


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


DPL_LOCATION_FIELDS = [
    "source_record_id",
    "source_file",
    "source_url",
    "library_id",
    "name",
    "normalized_name",
    "location_type",
    "zone",
    "address",
    "latitude",
    "longitude",
    "coordinate_source",
    "map_url",
    "geocode_status",
    "confidence",
    "notes",
]

GEOCODE_CACHE_FIELDS = [
    "source_record_id",
    "source_file",
    "library_id",
    "name",
    "address",
    "geocode_provider",
    "geocode_query",
    "geocode_result_label",
    "latitude",
    "longitude",
    "confidence",
    "review_status",
    "notes",
]


def extract_dpl_locations(html_dir: Path, source_by_stem: dict[str, str] | None = None) -> list[dict[str, str]]:
    source_by_stem = source_by_stem or {}
    rows: list[dict[str, str]] = []
    for path in sorted(html_dir.glob("operations__*_zone.html")):
        html_text = path.read_text(encoding="utf-8", errors="ignore")
        rows.extend(parse_dpl_zone_locations(path, html_text, source_by_stem.get(path.stem, "")))

    mobile_path = html_dir / "operations__schedule_and_points_of_mobile_van.html"
    rows.extend(parse_dpl_mobile_points(mobile_path, source_by_stem.get(mobile_path.stem, "")))

    for index, row in enumerate(rows, start=1):
        row["source_record_id"] = f"dpl_location_{index:04d}"
        row["library_id"] = stable_location_id(row["name"], index)
    return rows


def parse_dpl_zone_locations(path: Path, page_html: str, source_url: str = "") -> list[dict[str, str]]:
    zone = path.stem.removeprefix("operations__").removesuffix("_zone").replace("_", " ")
    page_title = page_library_title(page_html) or f"{zone.title()} Library"
    page_coordinates = first_embed_coordinates(page_html)
    current_name = ""
    current_raw_name = ""
    rows: list[dict[str, str]] = []

    for cells in table_rows(page_html):
        if len(cells) == 1:
            raw_header = cells[0]["text"]
            header = clean_location_name(raw_header)
            if header and "opening hours" not in header.lower() and "branches and" not in header.lower():
                current_name = header
                current_raw_name = raw_header
            continue
        if len(cells) < 2 or "address" not in cells[0]["text"].lower():
            continue

        raw_name = current_name or page_title
        name = clean_location_name(raw_name)
        address = clean_address(cells[1]["text"])
        if not address:
            continue
        map_url = next((link for link in cells[1]["links"] if "map" in link.lower() or "goo.gl" in link.lower()), "")
        coordinates, coordinate_source = coordinates_from_url(map_url)
        if not coordinates and not rows and page_coordinates:
            coordinates = page_coordinates
            coordinate_source = "google_maps_embed"
        latitude, longitude = coordinates if coordinates else ("", "")

        rows.append(
            location_row(
                source_file=path.name,
                source_url=source_url,
                name=name,
                location_type=location_type(current_raw_name or raw_name),
                zone=zone,
                address=address,
                latitude=latitude,
                longitude=longitude,
                coordinate_source=coordinate_source,
                map_url=map_url,
                notes="DPL-published fixed location parsed from zone page.",
            )
        )
    return rows


def parse_dpl_mobile_points(path: Path, source_url: str = "") -> list[dict[str, str]]:
    if not path.exists():
        return []
    page_html = path.read_text(encoding="utf-8", errors="ignore")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in re.findall(r"<(?:p|td)\b[^>]*>(.*?)</(?:p|td)>", page_html, re.I | re.S):
        address = clean_address(html_text(raw))
        if not mobile_address_candidate(address):
            continue
        key = normalize_name(address)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            location_row(
                source_file=path.name,
                source_url=source_url,
                name=f"Mobile Service Point {len(rows) + 1:03d}",
                location_type="mobile_service_point",
                zone="mobile",
                address=address,
                latitude="",
                longitude="",
                coordinate_source="",
                map_url="",
                notes="DPL-published mobile service point address; coordinate requires geocoding.",
            )
        )
    return rows


def location_row(
    *,
    source_file: str,
    source_url: str,
    name: str,
    location_type: str,
    zone: str,
    address: str,
    latitude: str,
    longitude: str,
    coordinate_source: str,
    map_url: str,
    notes: str,
) -> dict[str, str]:
    return {
        "source_record_id": "",
        "source_file": source_file,
        "source_url": source_url,
        "library_id": "",
        "name": name,
        "normalized_name": normalize_name(name),
        "location_type": location_type,
        "zone": zone,
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "coordinate_source": coordinate_source,
        "map_url": map_url,
        "geocode_status": "verified_coordinates" if latitude and longitude else "needs_geocode",
        "confidence": "high" if latitude and longitude else "medium",
        "notes": notes,
    }


def geocode_cache_rows(location_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in location_rows:
        if row["latitude"] and row["longitude"]:
            continue
        rows.append(
            {
                "source_record_id": row["source_record_id"],
                "source_file": row["source_file"],
                "library_id": row["library_id"],
                "name": row["name"],
                "address": row["address"],
                "geocode_provider": "",
                "geocode_query": geocode_query(row["address"]),
                "geocode_result_label": "",
                "latitude": "",
                "longitude": "",
                "confidence": "",
                "review_status": "needs_geocode",
                "notes": "Address is DPL-published; coordinates are pending reproducible geocoding/review.",
            }
        )
    return rows


def table_rows(page_html: str) -> list[list[dict[str, object]]]:
    parsed_rows: list[list[dict[str, object]]] = []
    for raw_row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", page_html, re.I | re.S):
        cells = []
        for raw_cell in re.findall(r"<td\b[^>]*>(.*?)</td>", raw_row, re.I | re.S):
            cells.append(
                {
                    "text": html_text(raw_cell),
                    "links": re.findall(r"""href=["']([^"']+)["']""", raw_cell, re.I),
                }
            )
        if cells:
            parsed_rows.append(cells)
    return parsed_rows


def page_library_title(page_html: str) -> str:
    matches = re.findall(r"<strong\b[^>]*>([^<]*Library[^<]*)</strong>", page_html, re.I)
    for match in matches:
        text = clean_location_name(html_text(match))
        if text and "Delhi Public Library" not in text:
            return text
    return ""


def first_embed_coordinates(page_html: str) -> tuple[str, str] | None:
    for src in re.findall(r"""<iframe\b[^>]*\bsrc=["']([^"']+)["']""", page_html, re.I):
        coordinates, _ = coordinates_from_url(html.unescape(src))
        if coordinates:
            return coordinates
    return None


def coordinates_from_url(url: str) -> tuple[tuple[str, str] | None, str]:
    if not url:
        return None, ""
    decoded = html.unescape(url)
    embed = re.search(r"!2d(-?\d+(?:\.\d+)?)!3d(-?\d+(?:\.\d+)?)", decoded)
    if embed:
        return (embed.group(2), embed.group(1)), "google_maps_embed"
    place = re.search(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", decoded)
    if place:
        return (place.group(1), place.group(2)), "google_maps_url"
    query = re.search(r"[?&]q=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", decoded)
    if query:
        return (query.group(1), query.group(2)), "google_maps_query"
    return None, ""


def html_text(raw: str) -> str:
    raw = re.sub(r"<script\b.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<br\s*/?>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return " ".join(html.unescape(raw).split())


def clean_location_name(value: str) -> str:
    value = html_text(value)
    value = re.sub(r"\s*\((?:Zonal|Sub-Branch|Branch|Community|R\.?\s*C\.?|Resettlement).*?\)", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" -")
    return value


def clean_address(value: str) -> str:
    value = html_text(value)
    value = re.sub(r"\bClick for location\b", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" ,;-")
    return value


def location_type(raw_name: str) -> str:
    lower = raw_name.lower()
    if "zonal" in lower or "zone library" in lower:
        return "zonal_library"
    if "sub-branch" in lower or "sub branch" in lower:
        return "sub_branch_library"
    if "resettlement" in lower:
        return "resettlement_colony_library"
    if "community" in lower:
        return "community_library"
    if "branch" in lower:
        return "branch_library"
    return "fixed_library"


def mobile_address_candidate(value: str) -> bool:
    lower = value.lower()
    if len(value) < 20 or len(value) > 220:
        return False
    if "delhi" not in lower and "new delhi" not in lower:
        return False
    rejected = [
        "delhi public library home",
        "search library catalogue",
        "schedule and points",
        "mobile library service",
        "minister",
        "copyright",
        "facebook",
        "national library",
        "central reference library",
    ]
    return not any(term in lower for term in rejected)


def geocode_query(address: str) -> str:
    if re.search(r"\b(delhi|new delhi)\b", address, re.I):
        return f"{address}, India"
    return f"{address}, Delhi, India"


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def stable_location_id(name: str, index: int) -> str:
    normalized = normalize_name(name).replace(" ", "_")
    return f"dpl_{normalized or 'location'}_{index:04d}"


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
        attendance = reading_room_attendance(text)
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
        if issue_subtotals_do_not_reconcile(row):
            row["adult_issues"] = ""
            row["child_issues"] = ""
            row["notes"] += " Adult/child issue subtotals do not reconcile with reported total issues; total issues retained."
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
        for line in chunk.splitlines():
            if not re.match(r"(?i)^\W*total\b", line.strip()):
                continue
            numbers = [parse_int(value) for value in re.findall(r"\d[\d,]*", line)]
            if len(numbers) < 6:
                continue
            values = numbers[:6]
            if values[0] + values[1] == values[2]:
                return tuple(values)  # type: ignore[return-value]
        return None
    values = tuple(parse_int(value) for value in matches[-1])
    if values[0] + values[1] == values[2]:
        return values  # type: ignore[return-value]
    return None


def membership_summary(text: str) -> tuple[int | None, int | None, int | None, int | None] | None:
    member = re.search(
        r"Total Membership[^\n:]*?\([^\n]*?Adult[-\s]*([0-9, ]+)[^\n]*?Children[-\s]*([0-9, ]+)\)[^:\n]*:\s*([0-9, ]+)",
        text,
        re.I,
    )
    issued = re.search(r"No\. of Books issued[^\n]*?[:>]\s*([0-9, ]+)", text, re.I)
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
    if match:
        return parse_collection_number(match.group(1))
    match = re.search(r"Net Book Stock\s+\D*([0-9][0-9,\s]+)", text, re.I)
    if match:
        return parse_collection_number(match.group(1))
    lower = text.lower()
    start = lower.find("analysis of net book stock")
    if start != -1:
        chunk = text[start : start + 5000]
        for line in chunk.splitlines():
            if "total" not in line.lower():
                continue
            candidates = [parse_collection_number(value) for value in re.findall(r"\d[\d,]*", line)]
            candidates = [value for value in candidates if value > 100_000]
            if candidates:
                return candidates[-1]
    return None


def parse_collection_number(value: str) -> int:
    tokens = re.findall(r"\d[\d,]*", value)
    token = max(tokens, key=len) if tokens else value
    parsed = parse_int(token)
    if 10_000_000 <= parsed < 30_000_000 and parsed % 10 == 0:
        return parsed // 10
    return parsed


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


def reading_room_attendance(text: str) -> int | None:
    attendance = first_number_after(text, r"Attendance of readers in Reading Rooms\s*:?\s*-?\s*")
    if attendance and attendance >= 10_000:
        return attendance
    match = re.search(r"During the year under report\s+([0-9,]+)\s+persons availed this facility", text, re.I)
    return parse_int(match.group(1)) if match else attendance


def parse_int(value: str) -> int:
    value = re.sub(r"\.\d+\b", "", value)
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else 0


def issue_subtotals_do_not_reconcile(row: dict[str, str]) -> bool:
    if not row["adult_issues"] or not row["child_issues"] or not row["total_issues"]:
        return False
    return int(row["adult_issues"]) + int(row["child_issues"]) != int(row["total_issues"])


def one_year(rows: list[dict[str, str]], year: str) -> dict[str, str]:
    for row in rows:
        if row["year"] == year:
            return row
    raise KeyError(year)


def ten_year_time_series(annual_rows: list[dict[str, str]], population: int) -> list[dict[str, str]]:
    return bounded_time_series(annual_rows, population, 2014, 2023)


def online_annual_time_series(annual_rows: list[dict[str, str]], population: int) -> list[dict[str, str]]:
    return bounded_time_series(annual_rows, population, 2009, 2023)


def bounded_time_series(
    annual_rows: list[dict[str, str]],
    population: int,
    first_start_year: int,
    last_start_year: int,
) -> list[dict[str, str]]:
    by_year = {row["year"]: row for row in annual_rows}
    rows: list[dict[str, str]] = []
    for start_year in range(first_start_year, last_start_year + 1):
        year = f"{start_year}-{str(start_year + 1)[-2:]}"
        source = by_year.get(year)
        if not source:
            rows.append(
                {
                    "year": year,
                    "fiscal_start_year": str(start_year),
                    "fiscal_end_year": str(start_year + 1),
                    "observation_status": "missing_source_not_extracted",
                    "source_url": "",
                    "total_members": "",
                    "total_issues": "",
                    "reading_room_attendance": "",
                    "collection_total": "",
                    "books_added_to_stock": "",
                    "total_expenditure_rs": "",
                    "population_denominator": str(population),
                    "members_per_1m": "",
                    "issues_per_1m": "",
                    "reading_room_attendance_per_1m": "",
                    "collection_refresh_pct": "",
                    "issues_per_collection_item": "",
                    "notes": "No parsed annual-report row in the targeted DPL source package.",
                }
            )
            continue
        total_members = optional_int(source["total_members"])
        total_issues = optional_int(source["total_issues"])
        attendance = optional_int(source["reading_room_attendance"])
        collection = optional_int(source["collection_total"])
        additions = optional_int(source["books_added_to_stock"])
        rows.append(
            {
                "year": year,
                "fiscal_start_year": str(start_year),
                "fiscal_end_year": str(start_year + 1),
                "observation_status": "observed",
                "source_url": source["source_url"],
                "total_members": source["total_members"],
                "total_issues": source["total_issues"],
                "reading_room_attendance": source["reading_room_attendance"],
                "collection_total": source["collection_total"],
                "books_added_to_stock": source["books_added_to_stock"],
                "total_expenditure_rs": source["total_expenditure_rs"],
                "population_denominator": str(population),
                "members_per_1m": ratio_per_1m(total_members, population),
                "issues_per_1m": ratio_per_1m(total_issues, population),
                "reading_room_attendance_per_1m": ratio_per_1m(attendance, population),
                "collection_refresh_pct": pct(additions, collection),
                "issues_per_collection_item": ratio(total_issues, collection),
                "notes": source["notes"],
            }
        )
    return rows


def primary_delhi_population() -> int:
    path = REPO / "data" / "cities" / "delhi" / "source" / "demographics" / "delhi_population_denominators.csv"
    if not path.exists():
        return 19_000_000
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["role"] == "primary_service_area_denominator":
                return int(row["population"])
    return 19_000_000


def optional_int(value: str) -> int | None:
    return int(value) if value else None


def ratio_per_1m(value: int | None, population: int) -> str:
    if value is None:
        return ""
    return f"{value / population * 1_000_000:.1f}"


def pct(numerator: int | None, denominator: int | None) -> str:
    value = ratio(numerator, denominator)
    return "" if value == "" else f"{float(value) * 100:.3f}"


def ratio(numerator: int | None, denominator: int | None) -> str:
    if numerator is None or denominator in (None, 0):
        return ""
    return f"{numerator / denominator:.6f}"


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
