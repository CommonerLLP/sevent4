from __future__ import annotations

from sevent4.domain.dpl_hierarchy import hierarchy_rows, summarize_hierarchy


def build_dpl_service_hierarchy(source_rows, geocoded_rows) -> tuple[list[dict], dict]:
    detail = hierarchy_rows(source_rows, geocoded_rows)
    return detail, summarize_hierarchy(detail)
