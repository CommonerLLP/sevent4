"""Shared library-network helpers — now a thin re-export shim.

The pure helpers live in sevent4.domain.library_networks and the IO helpers in
sevent4.adapters.library_networks_filesystem. This module re-exports them so the
existing importers (scripts/recipes/ahmedabad/enrich_mj_library_sources.py,
tests/test_ahmedabad_libraries_data.py, and the library comparators) keep working
unchanged.
"""
from __future__ import annotations

from sevent4.adapters.library_networks_filesystem import (  # noqa: F401
    export_pdf_texts,
    fetch_bytes,
    parse_js_object,
    pdf_pages,
    read_csv,
    read_json,
    run_pdftotext,
    sha256,
    write_csv,
    write_json,
)
from sevent4.domain.library_networks import (  # noqa: F401
    PlainTextParser,
    as_float,
    natural_key,
    normalize_name,
    one_year,
    plain_text,
    proactive_disclosure_year,
    source_counts,
    year_from_text,
)
