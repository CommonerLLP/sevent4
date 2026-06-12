# Ahmedabad city finance — data provenance

This note documents the source and method behind the **City finance** page of the
Ahmedabad atlas (`public/cities/ahmedabad/finance/`).

## What this is

A reading of what the Ahmedabad Municipal Corporation (AMC) chooses to fund,
drawn directly from AMC budget books. The municipal budget is treated as an
accountability record: the bus undertaking (AMTS) allocation line is the same
money that runs the routes shown on the atlas map, which is why finance and
transit are presented as one story.

## Sources

| File | Coverage | Content |
|---|---|---|
| `data/cities/ahmedabad/source/budget/amc_budget_22yr.csv` | 2005–06 to 2026–27 (20 years; gaps at 2020–21, 2022–23, 2023–24) | Headline lines: AMTS (city bus), M.J. Library grant, property tax, total revenue budget. Each row carries a source page, a confidence rating, and the property-tax basis. |
| `data/cities/ahmedabad/source/budget/amc_civic_lines.json` | 2018–19 to 2023–24 | Detailed civic lines: AMTS, BRTS/Janmarg (AJL), school-board top-up, V.S. Hospital grant, M.J. Library grant, riverfront, parks — each with the exact budget-book sentence, page, and source PDF. |

Both files are extracted from AMC budget books (English editions). The raw PDFs
are **not** stored in this repository; they remain in the upstream working
archive. This repo carries only the parsed, human-verified figures.

## Method and caveats

- **Units.** Amounts are normalised to rupees **crore** (1 crore = 100 lakh).
  AMC mixes crore (narrative/resolutions) and lakh (budget-code tables).
- **Estimate basis.** Budget books carry several columns — prior-year *actual*,
  current-year *revised estimate*, budget-year *budget estimate*. Each headline
  figure prefers the self-labelled narrative allocation ("Rs. X has been
  allocated in [FY]"), the most legible anchor.
- **AMTS line.** The AMTS figure is the corporation's capital support to the bus
  undertaking ("Loan to AMTS"). It is **not** the AMTS operating deficit, which
  is a separate operational figure not isolated as a single budget line.
- **The two sources agree** on overlapping years (e.g. AMTS 2018–19 = ₹355 cr in
  both), so they are merged into one bus-funding series; only 2020–21 (a COVID
  gap in the set) is missing.
- **Confidence and blanks.** Figures are human-verified from the source PDFs and
  carry per-row confidence. Where a figure could not be cleanly isolated from a
  scanned table, the cell is left blank rather than guessed. Treat low-confidence
  and blank cells with caution. These are a research reading of public documents,
  not an official account.

## Regenerating the page

```bash
python3 -m sevent4.finance.build_budget_explorer \
  --city data/cities/ahmedabad/city.yaml \
  --out public/cities/ahmedabad/finance/index.html
```

The page is self-contained: charts are inline SVG (no external CDN), and the
data is read from the two source files above.
