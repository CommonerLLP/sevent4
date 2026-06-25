#!/usr/bin/env python3
"""Build Bengaluru BBMP ward work-order finance tables.

Thin CLI wrapper: aggregation lives in sevent4.domain.bengaluru_finance,
dispatch in sevent4.application.bengaluru_finance, and CSV/JSON filesystem IO
in sevent4.adapters.bengaluru_finance_filesystem.
"""
from __future__ import annotations

import sevent4.adapters.bengaluru_finance_filesystem as finance_store
from sevent4.application.bengaluru_finance import build_finance_layer, build_yearly_table_from_store
from sevent4.domain.bengaluru_finance import (  # noqa: F401
    build_yearly_geojson,
    nk,
    norm_ward,
    num,
    order_year,
    ward_from_filename,
)


def build_yearly_table(raw_dir=finance_store.RAW, min_year: int = 2013, max_year: int = 2022) -> list[dict]:
    return build_yearly_table_from_store(finance_store, raw_dir, min_year, max_year)


def main() -> None:
    result = build_finance_layer(finance_store, finance_store.RAW, finance_store.FINANCE_OUT, finance_store.BOUNDARY)
    print(
        f"wards in ledger: {result['ledger_rows']}  | total Nett: Rs {result['total_nett_cr']:,.0f} cr "
        f"| works: {result['works']:,}"
    )
    print(
        f"BBMP-2023 boundary names: {result['boundary_names']} | "
        f"name-matched to ledger wards: {result['matched']}/{result['ledger_rows']}"
    )
    print(f"wrote {finance_store.FINANCE_OUT / 'ward_workorders.json'}")
    print(f"wrote {finance_store.FINANCE_OUT / 'ward_workorders_yearly.json'}")
    print("\nTop 5 wards by spend:")
    for row in result["top_rows"]:
        contractor = row["top_contractors"][0]["name"][:22] if row["top_contractors"] else "-"
        print(f"  {row['ward_name'][:24]:26} Rs {row['total_nett_cr']:7,.1f} cr  {row['work_count']:4} works  top: {contractor}")


if __name__ == "__main__":
    main()
