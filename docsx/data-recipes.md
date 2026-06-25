# Data recipes

The atlas ships processed Ahmedabad layers so the console runs immediately. The
public recipes under `scripts/recipes/ahmedabad/` document how to rebuild key
pieces of that seed from public sources.

## Ahmedabad budget

AMC publishes budgets, balance sheets, and finance context as PDFs:

```text
https://ahmedabadcity.gov.in/SP/Budget
https://ahmedabadcity.gov.in/SP/BalanceSheet
https://ahmedabadcity.gov.in/SP/AboutAMCFinance
```

The recipe is city-generic by filename but Ahmedabad-specific by default:

```bash
.venv/bin/python scripts/recipes/ahmedabad/fetch_city_budget.py
.venv/bin/python scripts/recipes/ahmedabad/fetch_city_budget.py --kind balance-sheet
.venv/bin/python scripts/recipes/ahmedabad/fetch_city_representatives.py
.venv/bin/python scripts/recipes/ahmedabad/parse_city_representatives.py
.venv/bin/python scripts/recipes/ahmedabad/ocr_city_budget.py
.venv/bin/python scripts/recipes/ahmedabad/parse_city_budget.py
```

That shape is intentional. Other cities publish budgets through different
websites, portals, PDF naming schemes, or spreadsheets, so each city needs its
own fetch adapter. Once PDFs are present under
`data/cities/<city>/source/budget/pdfs/`, the OCR and parse scripts can be
extended city by city.

Ahmedabad representative, officer, civic-center, and department source notes are
tracked in `data/cities/ahmedabad/source/public_sources.json`.
