# Contributing Ahmedabad data back to OpenCity

_Drafted 2026-06-11. A parked decision, not an action plan — written down so the thread survives._

## The asymmetry

We came to `data.opencity.in` (CKAN 2.11.4; 1,053 datasets, 8,056 resources, ~30 GB) to *pull*
data into the atlas. For most cities that's the right direction — Bengaluru alone has 528 datasets,
Chennai 130, Mumbai 66. But **for Ahmedabad the relationship is inverted: there is almost nothing
there to consume, and we hold the missing primary source.**

OpenCity's entire Ahmedabad holding lives under the `amdavad-municipal-corporation-amc` org —
**4 datasets, 16 resources, 13 of them PDFs:**

| Dataset | Resources | Format |
|---|---|---|
| Amdavad Municipal Corporation Wards Map 2024 | 2 (same file twice) | KML |
| Ahmedabad Climate Action Plan | 2 | PDF |
| Ahmedabad Heat Action Plans (2015–2019) | 10 | PDF |
| Gujarat Socio-Economic Review 2022-23 | 2 | PDF + ZIP |

De-duplicated, it is really three things: one ward boundary map and a shelf of policy PDFs. There
is **zero machine-readable tabular or operational spatial data** for the city.

By contrast, what sevent4 holds for Ahmedabad (counts as of 2026-06-11):

| Layer | sevent4 | OpenCity AMC |
|---|--:|--:|
| Machine-readable spatial features | ~16,800 (20 GeoJSON layers) | 0 |
| Transit stops | 6,599 | — |
| Transit corridors (AMTS/BRTS) | 447 / 45 | — |
| Metro segments | 187 | — |
| Health facilities | 955 | — |
| Schools / universities | 74 / 47 | — |
| Libraries | 62 | — |
| Toilets | 49 | — |
| Police / fire | 31 / 6 | — |
| Road features | 6,255 | — |
| Land-use polygons | 1,789 | — |
| Wards (boundary + heat) | 48 + 48 | 1 KML map |
| AMC budget timeseries | 22 years | — |
| AMC budget-code ledger | 1,210 rows | — |
| Road-resurfacing contractor panel | 1,683 work-orders / 7 yrs | — |
| MLA/MP representation | 32 rows | — |

The decisive point for a contribution: **most of what we hold is the structured form of AMC's own
documents** — budget books, DLP road registers, ward maps, GTFS. The provenance is the city's; the
cleaning, parsing, and ward-keying are ours. That makes it the most defensible possible contribution
back to AMC's own org on the portal.

## What to contribute, tiered by risk

### Tier 1 — contribute first (clean, public-source, no exposure)
Derived entirely from public AMC / GTFS / survey sources; nothing that names a private party adversarially.

- **AMC budget timeseries** (`amc_budget_22yr.csv`) + the budget-code ledger (`code_rows_raw.csv`),
  with the documented correction that there is no genuine 2021-22 budget book (the PDF is a
  byte-identical duplicate of 2020-21).
- **Transit layers** — stops, AMTS/BRTS corridors, metro lines/segments (GTFS-derived).
- **Service-point layers** — health, schools, universities, libraries, toilets, police, fire.
- **Ward layers** — `wards.geojson` (boundaries) and `ward_heat.geojson` (the per-ward heat
  composite), which is strictly richer than the lone KML they host.
- **Land-use and road network** GeoJSON.

Each goes up as CSV/GeoJSON with a short data dictionary and an explicit source line
("derived from AMC <document>, parsed by sevent4, <date>").

### Tier 2 — contribute deliberately, with framing intact
- **Road-resurfacing panel** (`roads_resurfaced_rows.csv`, `panel_7yr_summary.json`) and the
  **contractor registry** (`contractor_registry.json`). This is original and valuable, but it is the
  one body of data carrying a live political reading. The discipline established in
  `docs/the-road-money.md` and `notes/STATE_OF_BRAIN.md` must travel with it:
  **concentration is provable; partisan ownership is not.** We tested the firm→BJP link (electoral
  bonds; director × councillor roster, both terms) and it came back negative, so we do not assert it.
  - If contributed, the dataset description must carry the structural (tier-A) finding only, with the
    §6 "no firm-level claim" guardrail verbatim. Publishing a named-contractor table onto a
    third-party portal is a different and larger exposure than holding it in our own evidence base —
    so this is a deliberate, reviewed step, not a bulk upload.

### Tier 0 — do not contribute
- Anything still HITL / unverified (firm and ward transliterations from the registers; residual
  generic-firm CIN decoding) until cleaned.
- Working notes, close-readings, and the analytical essays — those are ours, not portal data.

## Open questions to resolve before uploading

1. **Licensing.** What licence does OpenCity attach to contributed datasets, and is it compatible
   with our sources? (AMC documents are public-record; our derived layers we can release openly —
   but confirm the portal's expected terms rather than assume.) _Do not web-search without Aakash's OK._
2. **Attribution / org.** Should these land under the existing `amdavad-municipal-corporation-amc`
   org (we'd be enriching the city's own org) or a `sevent4` / Commoner contributor identity?
   The former is more defensible (city provenance); the latter is more honest about who did the work.
   Likely answer: AMC org as *source*, sevent4 credited as the processor in each dataset's description.
3. **Account / API write access.** CKAN ingestion needs an authenticated account + API key with
   create rights on the target org. Confirm whether OpenCity grants contributor accounts and on what
   terms before building any uploader.
4. **Maintenance commitment.** A contributed dataset implies some freshness expectation. Decide which
   layers we'll keep current (budget is annual; GTFS changes; service points drift) vs. which we
   publish as a dated snapshot only.

## If/when we proceed

The CKAN write path mirrors the read path we already use: `package_create` to register a dataset
under the org, then `resource_create` (multipart) per file. A thin uploader reading a contribution
manifest (dataset title, org, source line, licence, files) would do it. **Not built — gated on the
licensing + account questions above.**

## Provenance of this note

Catalogue crawled via `scripts/recipes/opencity_catalogue.py`; full manifest at
`/Volumes/m1-storage/sevent4-data/opencity/_catalogue/opencity_catalogue.json`. Feature/row counts
from `data/cities/ahmedabad/layers/*.geojson` and `…/source/budget/*.csv` on 2026-06-11.
