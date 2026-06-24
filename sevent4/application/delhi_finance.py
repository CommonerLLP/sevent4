from __future__ import annotations

from sevent4.domain.delhi_finance import finance_meta, ndmc_row, parse_gnctd_rows, parse_mcd_rows


def parse_delhi_finance(source) -> tuple[list[dict], dict]:
    """Parse the three Delhi civic budgets via the source into one finance series
    plus the output meta. `source` provides gnctd/mcd/ndmc docs + the vision overlay."""
    rows = parse_gnctd_rows(source.gnctd_docs(), source.vision_overlay())
    rows += parse_mcd_rows(source.mcd_docs())
    ndmc = source.ndmc_doc()
    if ndmc:
        rows.append(ndmc_row(*ndmc))
    return rows, finance_meta(rows)
