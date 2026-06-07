# Ahmedabad Data Recipes

These scripts document how the Ahmedabad seed data can be regenerated from
public sources.

The filenames are city-generic on purpose. Ahmedabad is the first implemented
city adapter; other cities will need their own source discovery and parsing
rules over time.

```bash
python3 scripts/recipes/ahmedabad/fetch_city_budget.py
python3 scripts/recipes/ahmedabad/fetch_city_budget.py --kind balance-sheet
python3 scripts/recipes/ahmedabad/fetch_city_representatives.py
python3 scripts/recipes/ahmedabad/parse_city_representatives.py
python3 scripts/recipes/ahmedabad/ocr_city_budget.py
python3 scripts/recipes/ahmedabad/parse_city_budget.py
python3 scripts/recipes/ahmedabad/build_gtfs_corridors.py
python3 scripts/recipes/ahmedabad/build_ward_service_access.py
python3 scripts/recipes/ahmedabad/build_heat_layer.py
```

Budget OCR requires command-line tools:

- `pdfinfo`, `pdftotext`, and `pdftoppm` from Poppler
- `tesseract` with Gujarati and English language data

The heat recipe requires the optional heat dependencies:

```bash
python3 -m pip install -e '.[heat]'
```

Current budget paths:

```text
data/cities/ahmedabad/source/budget/pdfs/
data/cities/ahmedabad/source/budget/ocr_capex_opex/
data/cities/ahmedabad/layers/budget_capex_opex.csv
```

Current Ahmedabad public source index:

```text
data/cities/ahmedabad/source/public_sources.json
```

For a city without a budget fetch adapter, place PDF files in
`data/cities/<city>/source/budget/pdfs/`, then run `ocr_city_budget.py` and
`parse_city_budget.py` with `--city <city>` after adding parser labels.
