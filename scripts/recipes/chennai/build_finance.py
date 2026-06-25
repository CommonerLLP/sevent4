#!/usr/bin/env python3
"""Build Chennai's GCC finance layer from OpenCity source records."""
from __future__ import annotations

import sevent4.adapters.chennai_finance_filesystem as finance_store
from sevent4.application.chennai_finance import acquire_finance_resources, build_finance_layer
from sevent4.domain.chennai_finance import (
    ACTUALS_COL,
    VINTAGE,
    build_budget_summary,
    build_zone_capex,
    num,
    zone_roman,
)


def acquire() -> list[dict]:
    return acquire_finance_resources(finance_store)


def main() -> None:
    result = build_finance_layer(finance_store)
    if result["capex_lakh"]:
        print(
            f"[zone_finance] {result['zones']} zones · capex Rs {result['capex_lakh'] / 100:.0f} cr "
            f"(2013-14 actuals) · state-grant share {result['state_grant_pct']:.0f}%"
        )
    else:
        print("[zone_finance] no capex")
    if result["budget_written"]:
        print("[budget] wrote source/finance/chennai_budget.json")
    print("[provenance] wrote source/finance/sources.json")


if __name__ == "__main__":
    main()
