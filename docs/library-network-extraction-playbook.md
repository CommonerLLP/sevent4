# Library Network Extraction Playbook

Use this pattern when SevenT4 adds a city library network dossier.

## Pattern

1. Preserve the official site/content index as structured JSON.
2. Build a PDF/link manifest with category, year, label, URL, and context.
3. Export every annual/proactive disclosure PDF to searchable text, retaining a
   text manifest with source URL, page count, hash, extraction method, and notes.
4. Curate numeric tables separately from raw text: membership, collections,
   circulation, income/grants, expenditure, capital, and additions.
5. Keep geospatial library inventories separate by source, then add a combined
   normalized index instead of collapsing conflicting lists.
6. Record confidence and correction notes for OCR/manual fixes.
7. Add tests that assert coverage: expected years, source counts, text files,
   derived metrics, and JSON/CSV consistency.

## Implemented

- Shared extraction utilities: `scripts/recipes/library_networks.py`.
- Ahmedabad: M.J. Library / AMC library layer, via
  `scripts/recipes/ahmedabad/extract_mj_library.py`.

## Next Comparable Target

- Delhi: Delhi Public Library should receive the same treatment when SevenT4
  reaches Delhi: official site capture, annual reports/proactive disclosures,
  PDF text exports, curated finance/membership/collection tables, geospatial
  branch inventory, and coverage tests.
