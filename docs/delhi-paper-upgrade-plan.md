# Delhi Public Library paper — upgrade plan

Goal: bring the Delhi paper to the same standard as the rewritten Ahmedabad paper
(argument-first, Delhi-centred, Toronto demoted to a background yardstick, reproducible
figures, the livability-framework + Indian-scholarship framing).

_Started 2026-06-14 on `feat/delhi`._

## What exists

- **Paper (old structure):** `docs/delhi-toronto-library-comparison.qmd` — pre-restructure
  (Denominator, IFLA Frame, Finance, DPL Timeline, Toronto comparison, NCR sensitivity,
  data gaps, conclusions). No normative opening, Toronto co-billed, no figures.
- **Data (rich):** `data/cities/delhi/source/libraries/dpl_annual_metrics.csv` — DPL annual
  reports 2009-10 → 2023-24: members (adult/child), issues (circulation), reading-room
  attendance, collection, books added, and finance (grant, expenditure, unspent, returned)
  from 2021-22. Plus `dpl_library_locations.csv` (112 locations, lat/lon partly geocoded),
  `delhi_population_denominators.csv` (NCT ~19M, 2020), comparators under
  `data/comparators/delhi_toronto/`.

## Started this pass

- **`scripts/make_delhi_library_paper_figures.py`** + two reproducible figures:
  - `docs/figures/figD1_dpl_decline.png` — issues collapse **−77%** (peak 1,169,734 in
    2010-11 → 274,751 in 2023-24); members peak 189,235 in 2019-20, then fall.
  - `docs/figures/figD2_dpl_finance.png` — DPL carries large **unspent balances** and
    **returns grant to the Ministry** (e.g. ₹4.78 cr closing unspent on a ₹36 cr grant,
    2023-24). A different fiscal pathology than Ahmedabad's payroll-heavy starve.

## The Delhi story (distinct from Ahmedabad)

- **Steeper collapse:** issues −77% (vs Ahmedabad −55%), pre-COVID decline then a deeper
  COVID crash; books added fell from ~78,000/yr (2009-10) to ~3,100 (2023-24).
- **Funded but not spent:** DPL is a Govt-of-India body (Ministry of Culture), centrally
  funded, yet it under-spends and returns money — the opposite end of the same failure
  (Ahmedabad spends but on establishment, not books; Delhi doesn't spend at all).
- **Governance:** DPL is national/autonomous, not municipal — and Delhi's city governance
  is the NCT/MCD/NDMC special case (flag in the framing, do not treat as a normal municipality).

## To do (to reach Ahmedabad standard)

1. Restructure `delhi-...qmd` to argument-first, Delhi-centred: reuse the city-agnostic
   normative "case" section + measurement frame + livability-framework + Indian-scholarship
   passages from the Ahmedabad paper (`docs/ahmedabad-toronto-public-library-comparison.qmd`
   on `feat/ahmedabad-libraries`), swap in Delhi specifics, demote Toronto to one yardstick.
2. Embed figD1/figD2; add the DPL decade table.
3. **Geocode the remaining DPL locations** (geocode_cache has `needs_geocode` rows) → build
   the ward/area walk-access map (figD3) like Ahmedabad fig 1.
4. **Pull Delhi transit layers** (DMRC Metro, DTC/cluster bus) → build the transit-siting
   map (figD4): are DPL branches on the network?
5. Share the bibliography (`docs/library-comparator-references.bib`) — already holds the
   IFLA/Mattern/15-min/Indian-scholarship entries; point the Delhi qmd at it.
6. Author as Right 2 Read Campaign; no internal repo paths in the appendix.
