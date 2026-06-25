#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

from sevent4.adapters.library_access_filesystem import read_csv, write_csv
from sevent4.application.library_access import build_toronto_library_headline_rows


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
    return build_toronto_library_headline_rows(physical_branches, total_square_feet)


if __name__ == "__main__":
    main()
