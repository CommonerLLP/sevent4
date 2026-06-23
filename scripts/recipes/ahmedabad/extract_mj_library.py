#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urljoin

from sevent4.application.acquisition import (
    classify_mj_library_pdf,
    mj_library_proactive_disclosure_year,
    mj_library_year_from_text,
)
from scripts.recipes.library_networks import (
    as_float,
    export_pdf_texts,
    fetch_bytes,
    normalize_name,
    one_year,
    parse_js_object,
    plain_text,
    proactive_disclosure_year,
    read_csv,
    read_json,
    sha256,
    source_counts,
    write_csv,
    write_json,
    year_from_text,
)


REPO = Path(__file__).resolve().parents[3]
BASE_URL = "https://www.mjlibrary.in/"
CONTENT_JS_URL = urljoin(BASE_URL, "assets/frontend/en-lang/content.js")
DEFAULT_OUT_DIR = REPO / "data" / "cities" / "ahmedabad" / "source" / "libraries"
DEFAULT_CACHE_DIR = Path("/private/tmp/mj_disclosures")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract official M.J. Library source artifacts.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--content-js", type=Path, help="Use an already downloaded content.js file.")
    parser.add_argument("--no-download", action="store_true", help="Use cached disclosure PDFs only.")
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    content_js = args.content_js or args.cache_dir / "content.js"
    if not args.content_js:
        content_js.write_bytes(fetch_bytes(CONTENT_JS_URL, user_agent="The Unelected City M.J. Library extractor"))

    content = parse_js_object(content_js, "content")
    site_payload = {
        "source_url": CONTENT_JS_URL,
        "sha256": sha256(content_js),
        "entry_count": len(content),
        "content": content,
    }
    write_json(out_dir / "mj_library_site_content.json", site_payload)

    pdf_rows = extract_pdf_links(content)
    write_csv(
        out_dir / "mj_library_pdf_index.csv",
        pdf_rows,
        [
            "category",
            "year",
            "content_key",
            "language",
            "label",
            "url",
            "context_text",
        ],
    )

    disclosure_rows = export_pdf_texts(
        pdf_rows,
        args.cache_dir,
        out_dir / "disclosures_text",
        REPO,
        category="proactive_disclosure",
        no_download=args.no_download,
        user_agent="The Unelected City M.J. Library extractor",
    )
    write_csv(
        out_dir / "mj_library_disclosure_text_index.csv",
        disclosure_rows,
        [
            "year",
            "source_url",
            "text_path",
            "pdf_sha256",
            "pages",
            "text_chars",
            "text_lines",
            "extraction_method",
            "confidence",
            "notes",
        ],
    )

    location_rows = library_location_rows()
    write_csv(
        out_dir / "ahmedabad_library_locations.csv",
        location_rows,
        [
            "source_file",
            "source_record_id",
            "source_category",
            "name",
            "normalized_name",
            "description",
            "latitude",
            "longitude",
        ],
    )

    write_network_json(out_dir, pdf_rows, disclosure_rows, location_rows)

    print(f"wrote {out_dir / 'mj_library_site_content.json'}")
    print(f"wrote {out_dir / 'mj_library_pdf_index.csv'} ({len(pdf_rows)} PDF links)")
    print(f"wrote {out_dir / 'mj_library_disclosure_text_index.csv'} ({len(disclosure_rows)} disclosures)")
    print(f"wrote {out_dir / 'ahmedabad_library_locations.csv'} ({len(location_rows)} rows)")
    print(f"wrote {out_dir / 'mj_library_network.json'}")

def extract_pdf_links(content: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    anchor_re = re.compile(r"""<a\b[^>]*href=["']([^"']+\.pdf)["'][^>]*>(.*?)</a>""", re.I | re.S)
    for key, value in content.items():
        for lang in ("eng", "guj"):
            raw = str(value.get(lang, ""))
            if ".pdf" not in raw.lower():
                continue
            for match in anchor_re.finditer(raw):
                href, label = match.groups()
                prefix = raw[max(0, match.start() - 180) : match.start()]
                context = plain_text(f"{prefix} {label}")
                url = urljoin(BASE_URL, html.unescape(href))
                label_text = plain_text(label) or Path(unquote(url)).name
                proactive_year = proactive_disclosure_year(prefix)
                year = proactive_year or year_from_text(f"{label_text} {url}") or ""
                category = classify_pdf(context, url, year, bool(proactive_year))
                dedupe = (url, lang, key)
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                rows.append(
                    {
                        "category": category,
                        "year": year,
                        "content_key": key,
                        "language": lang,
                        "label": label_text,
                        "url": url,
                        "context_text": context[:500],
                    }
                )
    return sorted(rows, key=lambda row: (row["category"], row["year"], row["url"], row["language"]))

def library_location_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    amc_path = REPO / "data" / "cities" / "ahmedabad" / "source" / "amc" / "Library.geojson"
    amc = json.loads(amc_path.read_text(encoding="utf-8"))
    for index, feature in enumerate(amc.get("features", []), start=1):
        coords = feature.get("geometry", {}).get("coordinates", [])
        props = feature.get("properties", {})
        name = str(props.get("Name") or "")
        rows.append(
            {
                "source_file": str(amc_path.relative_to(REPO)),
                "source_record_id": str(index),
                "source_category": "amc_library_geojson",
                "name": name,
                "normalized_name": normalize_name(name),
                "description": str(props.get("description") or ""),
                "latitude": str(coords[1]) if len(coords) > 1 else "",
                "longitude": str(coords[0]) if coords else "",
            }
        )

    civic_path = REPO / "data" / "cities" / "ahmedabad" / "source" / "services" / "civic.json"
    civic = json.loads(civic_path.read_text(encoding="utf-8"))
    for index, item in enumerate(civic.get("library", []), start=1):
        name = str(item.get("name") or "")
        rows.append(
            {
                "source_file": str(civic_path.relative_to(REPO)),
                "source_record_id": str(index),
                "source_category": "civic_json_library",
                "name": name,
                "normalized_name": normalize_name(name),
                "description": "",
                "latitude": str(item.get("lat", "")),
                "longitude": str(item.get("lon", "")),
            }
        )
    return rows


def write_network_json(
    out_dir: Path,
    pdf_rows: list[dict[str, str]],
    disclosure_rows: list[dict[str, str]],
    location_rows: list[dict[str, str]],
) -> None:
    annual_stats = read_csv(out_dir / "mj_library_annual_stats.csv")
    finance = read_csv(out_dir / "mj_library_finance.csv")
    membership = read_csv(out_dir / "mj_library_membership.csv")

    derived_2025 = derived_2025_26(annual_stats, finance)
    payload = {
        "schema": "sevent4.ahmedabad.mj_library_network.v1",
        "source": {
            "official_site": BASE_URL,
            "site_content": str((out_dir / "mj_library_site_content.json").relative_to(REPO)),
            "pdf_index": str((out_dir / "mj_library_pdf_index.csv").relative_to(REPO)),
            "disclosure_text_index": str((out_dir / "mj_library_disclosure_text_index.csv").relative_to(REPO)),
            "disclosure_text_dir": str((out_dir / "disclosures_text").relative_to(REPO)),
            "notes": [
                "Official M.J. Library site content is preserved as JSON.",
                "Official proactive disclosures are preserved as pdftotext exports, with curated numeric tables in CSV.",
                "Library income is not assumed to be user fees only; it is treated as an upper bound for own-fee/self-income coverage.",
            ],
        },
        "coverage": {
            "official_site_content_entries": len(read_json(out_dir / "mj_library_site_content.json")["content"]),
            "official_pdf_links": len(pdf_rows),
            "proactive_disclosures": len(disclosure_rows),
            "proactive_disclosure_years": [row["year"] for row in disclosure_rows],
            "ahmedabad_library_location_rows": len(location_rows),
            "ahmedabad_library_location_sources": source_counts(location_rows),
        },
        "annual_stats": annual_stats,
        "membership": membership,
        "finance": finance,
        "derived_2025_26": derived_2025,
    }
    write_json(out_dir / "mj_library_network.json", payload)


def derived_2025_26(annual_stats: list[dict[str, str]], finance: list[dict[str, str]]) -> dict[str, float | int]:
    stat = one_year(annual_stats, "2025-26")
    fin = one_year(finance, "2025-26")
    ward_population = 7078533
    members = as_float(stat["network_total_with_gyanvihar"])
    circulation = as_float(stat["circulation_total"])
    total_budget = as_float(fin["total_budget_cr"])
    own_income = as_float(fin["library_income_cr"])
    books = as_float(fin["books_cr"])
    reading_material = as_float(fin["reading_material_cr"])
    capital = as_float(fin["capital_cr"])
    new_plans = as_float(fin["new_plans_cr"])
    recurring = total_budget - capital - new_plans
    estimated_core_fee_lakh = 17.335
    return {
        "ward_population_2020": ward_population,
        "membership_penetration_pct_of_ward_population_2020": round(members / ward_population * 100, 3),
        "registered_members_per_resident_ratio": round(ward_population / members, 1),
        "circulation_per_member": round(circulation / members, 2),
        "library_income_share_pct": as_float(fin["library_income_share_pct"]),
        "amc_grant_share_pct": as_float(fin["amc_grant_share_pct"]),
        "own_income_covers_books_pct": round(own_income / books * 100, 1),
        "own_income_covers_reading_material_pct": round(own_income / reading_material * 100, 1),
        "own_income_covers_recurring_ops_excluding_capital_new_plans_pct": round(own_income / recurring * 100, 2),
        "estimated_core_membership_fee_revenue_lakh_upper_bound": estimated_core_fee_lakh,
        "estimated_core_membership_fee_revenue_pct_of_total_budget": round((estimated_core_fee_lakh / 100) / total_budget * 100, 3),
        "estimated_core_membership_fee_revenue_pct_of_library_income": round((estimated_core_fee_lakh / 100) / own_income * 100, 1),
    }


def classify_pdf(context: str, url: str, year: str, proactive_context: bool = False) -> str:
    return classify_mj_library_pdf(context, url, year, proactive_context)


def year_from_text(text: str) -> str | None:
    return mj_library_year_from_text(text)


def proactive_disclosure_year(prefix: str) -> str | None:
    return mj_library_proactive_disclosure_year(prefix)


def plain_text(raw: str) -> str:
    parser = PlainTextParser()
    parser.feed(raw.replace("\\", " "))
    return html.unescape(parser.text())


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def natural_key(value: str) -> list[int | str]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def one_year(rows: list[dict[str, str]], year: str) -> dict[str, str]:
    for row in rows:
        if row.get("year") == year:
            return row
    raise KeyError(year)


def as_float(value: str) -> float:
    return float(value)


def source_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = row["source_category"]
        counts[key] = counts.get(key, 0) + 1
    return counts


if __name__ == "__main__":
    main()
