#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "data" / "comparators" / "delhi_toronto"
DPL_ANNUAL = REPO / "data" / "cities" / "delhi" / "source" / "libraries" / "dpl_annual_metrics.csv"
DPL_ONLINE_SERIES = REPO / "data" / "cities" / "delhi" / "source" / "libraries" / "dpl_online_annual_time_series.csv"
DPL_LONG = REPO / "data" / "cities" / "delhi" / "source" / "libraries" / "dpl_metrics_long.csv"
DELHI_POP = REPO / "data" / "cities" / "delhi" / "source" / "demographics" / "delhi_population_denominators.csv"
TPL_HEADLINE = REPO / "data" / "comparators" / "toronto" / "source" / "libraries" / "tpl_headline_finance_metrics.csv"
TPL_OPEN_DATA = REPO / "data" / "comparators" / "toronto" / "source" / "libraries" / "tpl_open_data_annual_metrics.csv"
TORONTO_POP = REPO / "data" / "comparators" / "toronto" / "source" / "demographics" / "toronto_population_denominators.csv"
PPP = REPO / "data" / "reference" / "economics" / "worldbank_ppp_conversion_factors.csv"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dpl_annual = by_key(read_csv(DPL_ANNUAL), "year")["2023-24"]
    dpl = metric_map(read_csv(DPL_LONG))
    tpl = metric_map(read_csv(TPL_HEADLINE))
    delhi_population_rows = read_csv(DELHI_POP)
    delhi_population = primary_population(delhi_population_rows)
    toronto_population = primary_population(read_csv(TORONTO_POP))
    ppp = ppp_map(read_csv(PPP))

    dpl_expenditure = number(dpl["total_expenditure"])
    tpl_expenditure = number(tpl["gross_expenditure"])
    dpl_ppp_expenditure = dpl_expenditure / ppp["India"]
    tpl_ppp_expenditure = tpl_expenditure / ppp["Canada"]
    dpl_materials = number(dpl["books_and_reading_material_expense"])
    tpl_materials = number(tpl["library_materials"])
    dpl_materials_ppp = dpl_materials / ppp["India"]
    tpl_materials_ppp = tpl_materials / ppp["Canada"]

    comparison_rows = [
        row(
            "service_points_conservative",
            "IFLA service points, conservative",
            number(dpl["fixed_plus_mobile_buses"]),
            number(tpl["branches"]) + number(tpl["bookmobiles"]),
            "count",
            delhi_population,
            toronto_population,
            "DPL fixed library units plus mobile library buses; excludes mobile stops and book-reading centres.",
        ),
        row(
            "service_points_inclusive",
            "IFLA service points, inclusive DPL touchpoints",
            number(dpl["public_access_touchpoints_including_mobile_stops"]),
            number(tpl["branches"]) + number(tpl["bookmobiles"]),
            "count",
            delhi_population,
            toronto_population,
            "DPL fixed units, mobile buses, mobile service points, and book-reading centres.",
        ),
        row(
            "registered_users",
            "Registered users",
            number(dpl["registered_members"]),
            None,
            "count",
            delhi_population,
            toronto_population,
            "TPL current public page reports new card registrations and surveyed use, not total registered users.",
        ),
        row(
            "new_card_registrations",
            "New card registrations",
            None,
            number(tpl["card_registrations"]),
            "count",
            delhi_population,
            toronto_population,
            "Not directly comparable to DPL registered-member stock.",
        ),
        row(
            "physical_loans_or_borrowings",
            "Physical loans / borrowings",
            number(dpl["annual_issues"]),
            number(tpl["borrowings"]),
            "count",
            delhi_population,
            toronto_population,
            "DPL book issues compared with TPL total material borrowings; classification differs, but the gap is too large to be explained by scope alone.",
        ),
        row(
            "physical_visits_proxy",
            "Physical visits proxy",
            number(dpl["reading_room_attendance"]),
            number(tpl["branch_visits"]),
            "count",
            delhi_population,
            toronto_population,
            "DPL reports reading-room attendance, not all branch visits; this likely understates DPL visits.",
        ),
        row(
            "collection_items",
            "Collection items",
            number(dpl["collection_total"]),
            number(tpl["collection_items"]),
            "count",
            delhi_population,
            toronto_population,
            "TPL stores the public 'more than 10.5 million' value as a lower-bound 10.5m.",
        ),
        row(
            "annual_additions",
            "Annual collection additions",
            number(dpl["books_added_to_stock"]),
            None,
            "count",
            delhi_population,
            toronto_population,
            "TPL additions not captured in current source table.",
        ),
        row(
            "operating_expenditure_ppp",
            "Operating expenditure, PPP",
            dpl_ppp_expenditure,
            tpl_ppp_expenditure,
            "international_dollars",
            delhi_population,
            toronto_population,
            "Converted with World Bank PA.NUS.PPP; DPL 2023-24 INR and TPL 2026 CAD.",
        ),
        row(
            "materials_expenditure_ppp",
            "Library materials expenditure, PPP",
            dpl_materials_ppp,
            tpl_materials_ppp,
            "international_dollars",
            delhi_population,
            toronto_population,
            "DPL books and reading material expense compared with TPL library materials budget.",
        ),
    ]

    write_csv(
        OUT_DIR / "library_comparison_metrics.csv",
        comparison_rows,
        [
            "metric_id",
            "metric_label",
            "unit",
            "delhi_value",
            "toronto_value",
            "delhi_per_1m",
            "toronto_per_1m",
            "toronto_to_delhi_ratio_per_1m",
            "notes",
        ],
    )

    sensitivity_rows = ncr_sensitivity_rows(
        delhi_population_rows=delhi_population_rows,
        dpl=dpl,
        dpl_ppp_expenditure=dpl_ppp_expenditure,
    )
    write_csv(
        OUT_DIR / "delhi_ncr_sensitivity.csv",
        sensitivity_rows,
        [
            "area",
            "population",
            "role",
            "service_points_conservative_per_1m",
            "annual_issues_per_1m",
            "reading_room_attendance_per_1m",
            "ppp_spend_per_resident",
            "notes",
        ],
    )

    annual_rows = annual_usage_comparison_rows(
        dpl_rows=read_csv(DPL_ONLINE_SERIES),
        tpl_open_rows=read_csv(TPL_OPEN_DATA),
        tpl=tpl,
        delhi_population=delhi_population,
        toronto_population=toronto_population,
    )
    write_csv(
        OUT_DIR / "annual_usage_comparison.csv",
        annual_rows,
        [
            "dpl_fiscal_year",
            "comparison_year",
            "tpl_source_basis",
            "dpl_total_members",
            "dpl_total_issues",
            "dpl_reading_room_attendance",
            "dpl_collection_total",
            "dpl_books_added_to_stock",
            "tpl_circulation_or_borrowings",
            "tpl_branch_visits",
            "tpl_card_registrations",
            "dpl_issues_per_1m",
            "tpl_borrowings_per_1m",
            "tpl_to_dpl_borrowing_ratio_per_1m",
            "dpl_reading_attendance_per_1m",
            "tpl_branch_visits_per_1m",
            "tpl_to_dpl_visit_ratio_per_1m",
            "dpl_members_per_1m",
            "tpl_card_registrations_per_1m",
            "notes",
        ],
    )

    summary = build_summary(
        dpl_annual=dpl_annual,
        dpl=dpl,
        tpl=tpl,
        delhi_population=delhi_population,
        toronto_population=toronto_population,
        dpl_ppp_expenditure=dpl_ppp_expenditure,
        tpl_ppp_expenditure=tpl_ppp_expenditure,
        dpl_materials_ppp=dpl_materials_ppp,
        tpl_materials_ppp=tpl_materials_ppp,
    )
    (OUT_DIR / "library_comparison_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_DIR / 'library_comparison_metrics.csv'} ({len(comparison_rows)} rows)")
    print(f"wrote {OUT_DIR / 'delhi_ncr_sensitivity.csv'} ({len(sensitivity_rows)} rows)")
    print(f"wrote {OUT_DIR / 'annual_usage_comparison.csv'} ({len(annual_rows)} rows)")
    print(f"wrote {OUT_DIR / 'library_comparison_summary.json'}")


def build_summary(
    *,
    dpl_annual: dict[str, str],
    dpl: dict[str, str],
    tpl: dict[str, str],
    delhi_population: int,
    toronto_population: int,
    dpl_ppp_expenditure: float,
    tpl_ppp_expenditure: float,
    dpl_materials_ppp: float,
    tpl_materials_ppp: float,
) -> dict[str, float | int | str]:
    grant = number(dpl["grant_received"])
    other_income = number(dpl["other_income"])
    total_expenditure = number(dpl["total_expenditure"])
    closing_unspent = number(dpl["closing_unspent_balance"])
    dpl_loans = number(dpl["annual_issues"])
    tpl_borrowings = number(tpl["borrowings"])
    dpl_collection = number(dpl["collection_total"])
    tpl_collection = number(tpl["collection_items"])
    dpl_materials = number(dpl["books_and_reading_material_expense"])
    tpl_materials = number(tpl["library_materials"])
    staff_sanctioned = number(dpl["staff_sanctioned"])
    staff_vacant = number(dpl["staff_vacant"])
    return {
        "delhi_population_primary": delhi_population,
        "toronto_population_primary": toronto_population,
        "dpl_grant_inflow_share_pct": pct(grant, grant + other_income),
        "dpl_other_income_share_pct": pct(other_income, grant + other_income),
        "dpl_materials_expenditure_share_pct": pct(dpl_materials, total_expenditure),
        "tpl_materials_expenditure_share_pct": pct(tpl_materials, number(tpl["gross_expenditure"])),
        "dpl_closing_unspent_share_of_expenditure_pct": pct(closing_unspent, total_expenditure),
        "dpl_unspent_to_materials_multiple": safe_div(closing_unspent, dpl_materials),
        "dpl_staff_vacancy_pct": pct(staff_vacant, staff_sanctioned),
        "dpl_collection_refresh_pct": pct(number(dpl["books_added_to_stock"]), dpl_collection),
        "dpl_loans_per_collection_item": safe_div(dpl_loans, dpl_collection),
        "tpl_borrowings_per_collection_item": safe_div(tpl_borrowings, tpl_collection),
        "dpl_ppp_expenditure_m": dpl_ppp_expenditure / 1_000_000,
        "tpl_ppp_expenditure_m": tpl_ppp_expenditure / 1_000_000,
        "dpl_ppp_spend_per_resident": safe_div(dpl_ppp_expenditure, delhi_population),
        "tpl_ppp_spend_per_resident": safe_div(tpl_ppp_expenditure, toronto_population),
        "spend_per_resident_ratio_tpl_to_dpl": safe_div(
            safe_div(tpl_ppp_expenditure, toronto_population),
            safe_div(dpl_ppp_expenditure, delhi_population),
        ),
        "dpl_ppp_spend_per_loan": safe_div(dpl_ppp_expenditure, dpl_loans),
        "tpl_ppp_spend_per_borrowing": safe_div(tpl_ppp_expenditure, tpl_borrowings),
        "dpl_ppp_materials_per_resident": safe_div(dpl_materials_ppp, delhi_population),
        "tpl_ppp_materials_per_resident": safe_div(tpl_materials_ppp, toronto_population),
        "materials_per_resident_ratio_tpl_to_dpl": safe_div(
            safe_div(tpl_materials_ppp, toronto_population),
            safe_div(dpl_materials_ppp, delhi_population),
        ),
        "dpl_latest_source_url": dpl_annual["source_url"],
    }


def row(
    metric_id: str,
    label: str,
    delhi_value: float | None,
    toronto_value: float | None,
    unit: str,
    delhi_population: int,
    toronto_population: int,
    notes: str,
) -> dict[str, str]:
    delhi_per_1m = per_1m(delhi_value, delhi_population)
    toronto_per_1m = per_1m(toronto_value, toronto_population)
    ratio = safe_div(toronto_per_1m, delhi_per_1m)
    return {
        "metric_id": metric_id,
        "metric_label": label,
        "unit": unit,
        "delhi_value": fmt(delhi_value),
        "toronto_value": fmt(toronto_value),
        "delhi_per_1m": fmt(delhi_per_1m),
        "toronto_per_1m": fmt(toronto_per_1m),
        "toronto_to_delhi_ratio_per_1m": fmt(ratio),
        "notes": notes,
    }


def ncr_sensitivity_rows(
    *,
    delhi_population_rows: list[dict[str, str]],
    dpl: dict[str, str],
    dpl_ppp_expenditure: float,
) -> list[dict[str, str]]:
    rows = []
    for source in delhi_population_rows:
        if not source["role"].startswith("sensitivity_"):
            continue
        population = int(source["population"])
        rows.append(
            {
                "area": source["area"],
                "population": source["population"],
                "role": source["role"],
                "service_points_conservative_per_1m": fmt(per_1m(number(dpl["fixed_plus_mobile_buses"]), population)),
                "annual_issues_per_1m": fmt(per_1m(number(dpl["annual_issues"]), population)),
                "reading_room_attendance_per_1m": fmt(per_1m(number(dpl["reading_room_attendance"]), population)),
                "ppp_spend_per_resident": fmt(safe_div(dpl_ppp_expenditure, population)),
                "notes": "Shadow-catchment sensitivity only; DPL service jurisdiction is treated as NCT for the primary comparator.",
            }
        )
    return rows


def annual_usage_comparison_rows(
    *,
    dpl_rows: list[dict[str, str]],
    tpl_open_rows: list[dict[str, str]],
    tpl: dict[str, str],
    delhi_population: int,
    toronto_population: int,
) -> list[dict[str, str]]:
    tpl_by_year = {int(row["year"]): row for row in tpl_open_rows}
    rows = []
    for dpl in dpl_rows:
        comparison_year = int(dpl["fiscal_end_year"])
        tpl_row = tpl_by_year.get(comparison_year)
        basis = "tpl_open_data"
        tpl_circulation = tpl_branch_visits = tpl_cards = None
        notes = "DPL fiscal year is compared to the TPL calendar year matching the fiscal end year."
        if tpl_row:
            tpl_circulation = optional_number(tpl_row["circulation"])
            tpl_branch_visits = optional_number(tpl_row["branch_visits"])
            tpl_cards = optional_number(tpl_row["card_registrations"])
        elif comparison_year == 2024:
            basis = "tpl_2024_headline"
            tpl_circulation = optional_number(tpl["borrowings"])
            tpl_branch_visits = optional_number(tpl["branch_visits"])
            tpl_cards = optional_number(tpl["card_registrations"])
            notes = "DPL 2023-24 is compared to TPL 2024 headline public metrics."
        else:
            basis = "no_tpl_source"
            notes = "No TPL annual open-data row is available for this comparison year."

        dpl_issues = optional_number(dpl["total_issues"])
        dpl_attendance = optional_number(dpl["reading_room_attendance"])
        dpl_members = optional_number(dpl["total_members"])
        dpl_issues_per_1m = per_1m(dpl_issues, delhi_population)
        tpl_borrowings_per_1m = per_1m(tpl_circulation, toronto_population)
        dpl_attendance_per_1m = per_1m(dpl_attendance, delhi_population)
        tpl_visits_per_1m = per_1m(tpl_branch_visits, toronto_population)
        rows.append(
            {
                "dpl_fiscal_year": dpl["year"],
                "comparison_year": str(comparison_year),
                "tpl_source_basis": basis,
                "dpl_total_members": dpl["total_members"],
                "dpl_total_issues": dpl["total_issues"],
                "dpl_reading_room_attendance": dpl["reading_room_attendance"],
                "dpl_collection_total": dpl["collection_total"],
                "dpl_books_added_to_stock": dpl["books_added_to_stock"],
                "tpl_circulation_or_borrowings": fmt(tpl_circulation),
                "tpl_branch_visits": fmt(tpl_branch_visits),
                "tpl_card_registrations": fmt(tpl_cards),
                "dpl_issues_per_1m": fmt(dpl_issues_per_1m),
                "tpl_borrowings_per_1m": fmt(tpl_borrowings_per_1m),
                "tpl_to_dpl_borrowing_ratio_per_1m": fmt(safe_div(tpl_borrowings_per_1m, dpl_issues_per_1m)),
                "dpl_reading_attendance_per_1m": fmt(dpl_attendance_per_1m),
                "tpl_branch_visits_per_1m": fmt(tpl_visits_per_1m),
                "tpl_to_dpl_visit_ratio_per_1m": fmt(safe_div(tpl_visits_per_1m, dpl_attendance_per_1m)),
                "dpl_members_per_1m": fmt(per_1m(dpl_members, delhi_population)),
                "tpl_card_registrations_per_1m": fmt(per_1m(tpl_cards, toronto_population)),
                "notes": notes,
            }
        )
    return rows


def metric_map(rows: list[dict[str, str]]) -> dict[str, str]:
    return {row["metric_name"]: row["value"] for row in rows}


def primary_population(rows: list[dict[str, str]]) -> int:
    for row in rows:
        if row["role"] == "primary_service_area_denominator":
            return int(row["population"])
    raise KeyError("primary_service_area_denominator")


def ppp_map(rows: list[dict[str, str]]) -> dict[str, float]:
    return {row["country"]: float(row["value"]) for row in rows}


def by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def number(value: str) -> float:
    return float(value)


def optional_number(value: str) -> float | None:
    return float(value) if value else None


def per_1m(value: float | None, population: int) -> float | None:
    if value is None:
        return None
    return value / population * 1_000_000


def pct(numerator: float, denominator: float) -> float | None:
    result = safe_div(numerator, denominator)
    return None if result is None else result * 100


def safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    if abs(value) >= 100:
        return f"{value:.1f}"
    if abs(value) >= 10:
        return f"{value:.2f}"
    if abs(value) >= 1:
        return f"{value:.3f}"
    return f"{value:.6f}"


if __name__ == "__main__":
    main()
