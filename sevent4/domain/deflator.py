"""Pure nominal-to-real rupee conversion (REQ-0011, consumed from public-finance).

No filesystem IO lives here — the adapter loads the vendored CPI series and
passes it in as a plain dict; every function here is a pure computation over
that dict. sevent4 does not derive its own CPI series or deflate() logic; the
series and its methodology are public-finance's (owner_repo: public-finance),
vendored at references/deflator/cpi_combined_fy2005_06_to_latest.json (tracked,
not under data/, since a build must work from a fresh clone).
"""
from __future__ import annotations

import re

_FY_PATTERN = re.compile(r"^(\d{4})-(\d{2})$")


def index_for(series: dict[str, float], fiscal_year: str) -> float:
    match = _FY_PATTERN.match(fiscal_year)
    if not match or int(match.group(2)) != (int(match.group(1)) + 1) % 100:
        raise ValueError(
            f"Fiscal year must be 'YYYY-YY' (April-March, e.g. '2023-24'), got {fiscal_year!r}"
        )
    if fiscal_year not in series:
        years = sorted(series)
        raise ValueError(
            f"No confirmed deflator value for {fiscal_year}: series covers "
            f"{years[0]} to {years[-1]}"
        )
    return series[fiscal_year]


def deflate(series: dict[str, float], amount: float, from_year: str, to_year: str) -> float:
    """Convert a nominal rupee amount of fiscal year `from_year` into constant
    rupees of fiscal year `to_year`. Units pass through unchanged."""
    return amount * index_for(series, to_year) / index_for(series, from_year)


def latest_confirmed_year(series: dict[str, float]) -> str:
    return sorted(series)[-1]
