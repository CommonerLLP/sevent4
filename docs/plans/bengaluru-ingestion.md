# Plan — Bengaluru ingestion (OpenCity → sevent4 atlas)

_Drafted 2026-06-11. Pilot for the multi-city OpenCity harvest. Bengaluru first because it is the
richest and the only city with all three representative cuts already on the portal._

## Why Bengaluru is the pilot

- **528 datasets, 210 with structured (CSV/GeoJSON/KML/XLSX) data** — by far the deepest city on OpenCity.
- **All three cuts present on-portal** (ward + AC + PC), so no external boundary detour is needed to
  prove the slice-by spine. The other three cities will need ECI/DataMeet for AC/PC.
- It is the atlas's sharpest *who-decides* case already in `CITY_META`: **no elected council since
  Sept 2020**, BBMP dissolved into the **Greater Bengaluru Authority** (5 corporations, 369 wards) under
  an IAS Chief Commissioner; first elections only by Aug 2026 — an ~11-year democratic gap.
- **BBMP Work Orders by Ward (2013–2022)** + **Work Orders & Bill Payment** are a ready-made parallel to
  the Ahmedabad road-money investigation — ward-level public-works contracts with the money trail.

## The architecture we plug into (already exists)

`scripts/recipes/build_city.py --city bengaluru` already exists and turns
`data/cities/bengaluru/source/` into `layers/` + `layer_manifest.json` + `city.yaml` + console.
Bengaluru is already registered in `CITY_META`. The builder's **source contract**:

| Builder expects | Required? | OpenCity source |
|---|---|---|
| `source/boundaries/wards.geojson` | **yes** | GBA Wards Delimitation 2025 (KML) / BBMP Wards Delimitation 2023 (KML) |
| `source/boundaries/acs.geojson` | **yes** (crashes without) | ECI "Karnataka and Bengaluru Assembly Constituency Maps" (KML) |
| `source/boundaries/pcs.geojson` | **yes** (crashes without) | ECI "Karnataka and Bengaluru Parliamentary Constituency Maps" (KML) |
| `source/boundaries/districts.geojson` | optional | Bengaluru Urban district (Census/DataMeet) |
| `source/corporation/councillors.csv` | optional | **n/a — no elected council; the absence IS the finding** |
| `source/osm/<layer>.geojson` | optional | the function layers below (KML/CSV → GeoJSON) |

So ingestion = **acquire + convert into `source/`, then run the existing builder.** No new pipeline.

## The cut-geometry spine (ward / assembly / parliament)

The non-negotiable requirement: every Bengaluru indicator must be sliceable by ward, AC, and PC.

- **Ward** — *decision needed (see below): GBA-2025 369-ward vs BBMP-2023 198-ward.*
- **Assembly (AC)** — ECI Karnataka+BLR AC KML → clip to the city envelope.
- **Parliament (PC)** — ECI Karnataka+BLR PC KML → clip to the city envelope.

All three are KML on OpenCity → convert to GeoJSON (ogr2ogr / fiona), normalise field names to the
builder's expectations (`ac_name`/`AC_NAME`, `pc_name`/`PC_NAME`, ward number key), write to
`source/boundaries/`. This alone satisfies "cut the geo by ward, by assembly, by parliament."

## Function / axis layers — proposed pass-1 set (all structured, all BBMP/state-published)

| Axis | Layer | OpenCity dataset | Format |
|---|---|---|---|
| pays | BBMP Budget (annual) | BBMP Budget + 2023-24/24-25/25-26 | XLSX |
| pays | Ward public-works ledger | **BBMP Work Orders by Ward 2013-2022** | CSV |
| pays | Bill payments (money trail) | BBMP Work Orders and Bill Payment | CSV |
| pays | MLA local-area funds | Bengaluru MLA-LAD Funds | CSV |
| function (water) | Water supply + sewerage lines | BWSSB Water Supply / Sewerage Lines | KML |
| function (water) | Stormwater drains | Bengaluru Stormwater Drains Maps | KML |
| function (water) | Lakes + who maintains them | Bengaluru Lakes Data / Lakes and Their Maintainers | CSV |
| function (SWM) | Solid waste | BBMP Solid Waste Management Data | CSV/KML |
| function (transport) | Bus stops + routes by ward | BMTC Bus Stops and Routes by Ward | CSV/KML |
| function (health) | Births & deaths; hospitals; PHCs | Annual Births/Deaths; Hospitals; PHCs | CSV/KML |
| function (env) | Air quality (hourly) | Bengaluru Hourly Air Quality (KSPCB) | CSV |
| function (env) | Tree census; parks; streetlights | Tree Census; BBMP Parks; Zone-wise Streetlights | KML |

(Tree census KML and ward-wise street map are large; ingest geometry-simplified or ward-aggregated.)

## Provenance & credit (built in, not bolted on)

- `data/cities/bengaluru/source/CREDITS.md` — human-readable: every layer → publisher → OpenCity URL.
- `data/cities/bengaluru/source/sources.json` — machine-readable: `{layer, dataset_url, publisher_org,
  opencity_dataset, license, last_modified, retrieved}` per ingested file.
- On the console: each layer's popup/metadata cites _publisher → OpenCity → sevent4 (processed)_.
- Licence is an **open question per dataset** — record what OpenCity states; do not assume CC-BY.

## Staged execution (nothing fetched until you approve the pull)

1. **Boundary spine first — ✅ DONE 2026-06-11.** Acquired + converted all 4 boundary KMLs via
   `scripts/recipes/bengaluru/acquire_boundaries.py`: GBA-369 wards (`wards.geojson`, +per-ward census
   TOT_P/SC/ST fields), BBMP-198/225 historical (`wards_bbmp198.geojson`, +AC/PC linkage IDs), 28 ACs,
   5 PCs. Ran `build_city.py` + console; all three cut layers render, geometry validated to the
   Bengaluru envelope. Provenance in `source/boundaries/{sources.json,CREDITS.md}`. Console at
   `public/cities/bengaluru/index.html`. **Note:** `wards_bbmp198.geojson` is in `source/` but not yet
   wired as a console layer (the builder reads one `wards.geojson`) — pass-2/historical-join task.
2. **Finance layer** — BBMP Budget (XLSX) + the two work-order CSVs → the `who-pays` panel; this is the
   atlas's spine and the highest-value content.
3. **Function layers** — water/sewerage/SWM/transport/health/env, ward-aggregated where the raw is heavy.
4. **Provenance pass** — write CREDITS.md + sources.json; wire citations into the manifest.
5. **Publish** — copy `data/cities/bengaluru/` → `public/cities/bengaluru/`; add to `registry.json`
   (already present) + `scorecard.json`.
6. **Commit** — branch + PR per org policy. Downloads land on the **external volume** (currently
   unmounted — remount `m1-storage` before pulling); the in-repo `data/` stays gitignored.

## Decisions — LOCKED 2026-06-11

1. **Ward vintage → BOTH.** GBA-2025 (369 wards) as the default display layer (current unelected-GBA
   governance); BBMP-2023 (198 wards) as the historical join layer for the 2013-2022 work-orders and
   councillor history. The 369-vs-198 mismatch is itself part of the story.
2. **Pass-1 scope → SPINE + FINANCE ONLY.** Boundary cuts (ward×2 / AC / PC) + BBMP Budget (XLSX) +
   the two work-order CSVs. Function layers (water/SWM/transport/health/env) deferred to a reviewed
   pass-2. Stop and review after pass-1.
3. **Work-orders → LAYER NOW, INVESTIGATE LATER.** Ingest BBMP Work Orders by Ward (2013-2022) as a
   ward-level spend layer this pass; a road-money-style concentration analysis is a separate later
   effort (same discipline: concentration provable, partisan ownership only if documented).

## Blocker status

- **`m1-storage` unmounted — but pass-1 does NOT need it.** The pass-1 source files (a handful of ward/
  AC/PC KMLs + a few budget XLSX + two work-order CSVs) are small (tens of MB), so they land directly in
  the in-repo **gitignored** `data/cities/bengaluru/source/` — no external volume required. Only a full
  multi-GB mirror needs `m1-storage` remounted. So pass-1 is unblocked.
```
