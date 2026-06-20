#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen


REPO = Path(__file__).resolve().parents[3]
DEFAULT_CACHE_DIR = Path("/private/tmp")
DEFAULT_OUT_DIR = REPO / "data" / "comparators" / "toronto" / "source" / "libraries"

CIRCULATION_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca/datastore/dump/18e9b8ba-b4b1-4a2d-8e56-0fffab64c525"
VISITS_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca/datastore/dump/e1a183c8-266f-4643-af92-c618c0764f13"
CARDS_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca/datastore/dump/4b7601eb-e753-4dce-92be-e90ae1ae24cd"
BRANCHES_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca/datastore/dump/7420a950-e62b-41da-826c-32d31c46e8f8"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Toronto Public Library comparator metrics.")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    circulation = csv_path(args.cache_dir, "tpl_circulation.csv", CIRCULATION_URL)
    visits = csv_path(args.cache_dir, "tpl_visits.csv", VISITS_URL)
    cards = csv_path(args.cache_dir, "tpl_cards.csv", CARDS_URL)
    branches = csv_path(args.cache_dir, "tpl_branches.csv", BRANCHES_URL)

    annual = annual_rows(circulation, visits, cards)
    branch_rows = read_csv(branches)
    physical_branches = sum(1 for row in branch_rows if row.get("PhysicalBranch") == "1")
    total_square_feet = sum(float(row["SquareFootage"] or 0) for row in branch_rows)
    write_csv(
        args.out_dir / "tpl_open_data_annual_metrics.csv",
        annual,
        ["year", "circulation", "branch_visits", "card_registrations", "branches_reporting_circulation", "branches_reporting_visits", "branches_reporting_registrations", "source_url", "notes"],
    )
    headline = headline_rows(physical_branches, total_square_feet)
    write_csv(
        args.out_dir / "tpl_headline_finance_metrics.csv",
        headline,
        ["year", "metric_group", "metric_name", "value", "unit", "source_url", "confidence", "notes"],
    )
    print(f"wrote {args.out_dir / 'tpl_open_data_annual_metrics.csv'} ({len(annual)} rows)")
    print(f"wrote {args.out_dir / 'tpl_headline_finance_metrics.csv'} ({len(headline)} rows)")


def csv_path(cache_dir: Path, name: str, url: str) -> Path:
    path = cache_dir / name
    if path.exists():
        return path
    path.write_bytes(fetch_bytes(url))
    return path


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "The Unelected City Toronto library comparator"})
    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except Exception:
        curl = shutil.which("curl")
        if not curl:
            raise
        result = subprocess.run([curl, "-L", "--fail", "--silent", "--show-error", url], capture_output=True, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8", errors="ignore"))
        return result.stdout


def annual_rows(circulation_path: Path, visits_path: Path, cards_path: Path) -> list[dict[str, str]]:
    circulation, circulation_branches = annual_sum(circulation_path, "Circulation")
    visits, visit_branches = annual_sum(visits_path, "Visits")
    cards, card_branches = annual_sum(cards_path, "Registrations")
    years = sorted(set(circulation) | set(visits) | set(cards))
    rows = []
    for year in years:
        rows.append(
            {
                "year": str(year),
                "circulation": str(circulation.get(year, "")),
                "branch_visits": str(visits.get(year, "")),
                "card_registrations": str(cards.get(year, "")),
                "branches_reporting_circulation": str(len(circulation_branches.get(year, set()))),
                "branches_reporting_visits": str(len(visit_branches.get(year, set()))),
                "branches_reporting_registrations": str(len(card_branches.get(year, set()))),
                "source_url": "https://tpl.ca/about-the-library/open-data/",
                "notes": "Aggregated from City of Toronto Open Data TPL annual by-branch CSVs.",
            }
        )
    return rows


def annual_sum(path: Path, value_col: str) -> tuple[dict[int, int], dict[int, set[str]]]:
    totals: dict[int, int] = {}
    branches: dict[int, set[str]] = {}
    for row in read_csv(path):
        year = int(row["Year"])
        value = int(float(row.get(value_col) or 0))
        totals[year] = totals.get(year, 0) + value
        branches.setdefault(year, set()).add(row.get("BranchCode", ""))
    return totals, branches


def headline_rows(physical_branches: int, total_square_feet: float) -> list[dict[str, str]]:
    about = "https://tpl.ca/about-the-library/"
    finance = "https://tpl.ca/about-the-library/library-finance/"
    open_data = "https://tpl.ca/about-the-library/open-data/"
    rows = [
        ("2024", "network", "branches", physical_branches, "count", open_data, "high", "PhysicalBranch=1 rows in TPL branch general information open data."),
        ("2024", "network", "bookmobiles", 2, "count", about, "high", "TPL About page reports two bookmobiles."),
        ("2024", "network", "collection_items", 10_500_000, "count", about, "medium", "TPL About page reports more than 10.5 million items; stored as 10.5m lower-bound value."),
        ("2024", "network", "branch_square_feet", int(total_square_feet), "square_feet", open_data, "high", "Sum of SquareFootage in TPL branch general information open data."),
        ("2024", "usage", "total_visits_branch_and_online", 45_000_000, "count", about, "medium", "TPL About page reports nearly 45 million visits; stored as 45m rounded value."),
        ("2024", "usage", "branch_visits", 13_400_000, "count", about, "medium", "TPL About page reports 13.4 million branch visits."),
        ("2024", "usage", "online_visits", 31_500_000, "count", about, "medium", "TPL About page reports 31.5 million visits to online platforms."),
        ("2024", "usage", "borrowings", 28_000_000, "count", about, "medium", "TPL About page reports materials borrowed 28 million times."),
        ("2024", "usage", "card_registrations", 235_270, "count", about, "high", "TPL About page reports 235,270 people registered for a library card."),
        ("2024", "technology", "wireless_sessions", 6_000_000, "count", about, "medium", "TPL About page reports nearly six million wireless sessions."),
        ("2024", "technology", "public_computer_workstation_hours", 1_200_000, "hours", about, "medium", "TPL About page reports more than 1.2 million workstation session hours."),
        ("2024", "programs", "in_person_programs", 38_000, "count", about, "medium", "TPL About page reports over 38,000 in-person programs."),
        ("2024", "programs", "in_person_program_attendance", 750_000, "count", about, "medium", "TPL About page reports more than 750,000 in-person program participants."),
        ("2026", "finance", "gross_expenditure", 296_057_196, "CAD", finance, "high", "TPL 2026 operating budget reports gross expenditure."),
        ("2026", "finance", "staffing_salaries_benefits", 217_954_794, "CAD", finance, "high", "TPL 2026 gross expenditure split."),
        ("2026", "finance", "library_materials", 23_082_883, "CAD", finance, "high", "TPL 2026 gross expenditure split."),
        ("2026", "finance", "operations_administration", 55_019_519, "CAD", finance, "high", "TPL 2026 gross expenditure split."),
        ("2026", "finance", "city_funding_property_taxes", 274_378_001, "CAD", finance, "high", "TPL 2026 revenue split."),
        ("2026", "finance", "revenues_fines_fees", 4_298_350, "CAD", finance, "high", "TPL 2026 revenue split."),
        ("2026", "finance", "other_sources", 17_380_845, "CAD", finance, "high", "TPL 2026 revenue split."),
        ("2026", "capital", "capital_budget_total", 72_776_219, "CAD", finance, "high", "TPL 2026 capital budget funding sources."),
        ("2026", "capital", "capital_debt", 51_087_186, "CAD", finance, "high", "TPL 2026 capital budget funding sources."),
    ]
    return [
        {
            "year": str(year),
            "metric_group": group,
            "metric_name": name,
            "value": str(value),
            "unit": unit,
            "source_url": source,
            "confidence": confidence,
            "notes": notes,
        }
        for year, group, name, value, unit, source, confidence, notes in rows
    ]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
