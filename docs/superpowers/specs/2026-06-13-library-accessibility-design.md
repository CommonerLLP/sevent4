# Library Accessibility Comparator Design

Date: 2026-06-13

## Purpose

Build a reusable SevenT4 library accessibility pipeline that estimates how quickly a resident can reach a public library in Toronto, Delhi, and Ahmedabad. The same engine must support city diagnostics and pairwise comparisons:

- Delhi vs Toronto
- Ahmedabad vs Delhi
- Ahmedabad vs Toronto

The central measure is population-weighted travel time to the nearest public library, not raw branch counts or straight-line distance.

## Main Question

For each city:

1. Divide the service area into populated origin cells.
2. Estimate walk and transit travel time from each origin to public library branches.
3. Weight each origin by resident population.
4. Report the weighted median resident's access to a public library.

The headline metric is `p50_minutes_to_nearest_library`. Supporting metrics include `p75`, `p90`, percentage of residents within common thresholds, reachable branches within 30 minutes, and catchment population per branch.

## Data Inputs

Each city adapter writes or validates the same canonical source tables:

- `data/cities/<city>/source/libraries/library_locations.csv`
- `data/cities/<city>/source/transit/gtfs.zip`, when a usable GTFS feed exists
- `data/cities/<city>/source/transit/transit_lines.json`, when GTFS is absent or incomplete
- `data/cities/<city>/source/transit/transit_stops.json`
- `data/cities/<city>/source/demographics/population_origins.geojson`
- `data/cities/<city>/source/boundaries/service_area.geojson`

Current city status:

- Toronto: use Toronto Open Data TPL branch geodata and TTC transit feeds where available. The TPL branch dataset includes current branch location, size, and feature records and was listed as last updated 2026-05-13.
- Ahmedabad: use the existing MJ/AMC library location table and existing transit stop/line JSON already in SevenT4.
- Delhi: use existing DPL annual operations data plus DPL-published branch, zone, and mobile-service location pages. The work is to parse these pages into a canonical geotagged table, validate embedded Google Maps or short-link coordinates where available, geocode address-only mobile points, and keep fixed branches separate from mobile service points and deposit stations. DMRC and DTC/cluster bus data may require a mixed GTFS and OSM route fallback.

## Architecture

Shared engine:

- `scripts/recipes/accessibility/library_access.py`

City adapters:

- `scripts/recipes/toronto/build_library_access.py`
- `scripts/recipes/delhi/build_library_access.py`
- `scripts/recipes/ahmedabad/build_library_access.py`

Comparator builder:

- `scripts/recipes/comparators/build_library_access_comparison.py`

The shared engine owns validation, nearest-library calculations, confidence labels, threshold metrics, and output schemas. City adapters only fetch or normalize city-specific inputs. Reports consume generated CSV/JSON outputs and do not encode city-specific business logic.

## Routing Tiers

Tier A: GTFS plus OSM routing.

- Preferred for Toronto and any Indian city where the transit feed is complete enough.
- Models walk to stop, transit in vehicle, transfer/wait penalties, and walk from stop to branch.
- Intended long-term backend: OpenTripPlanner or an equivalent reproducible local routing engine.

Tier B: stop and corridor proxy.

- Used where official GTFS is unavailable or incomplete.
- Estimates access using walk distance to transit stops/corridors, nearest branch, and conservative transfer/headway assumptions.
- Must be labeled lower confidence and never mixed silently with Tier A.

Tier C: walk-only baseline.

- Always produced as a sanity check.
- Useful for showing whether the library network itself is dense enough, independent of public transit.

## Outputs

Per city:

- `data/cities/<city>/derived/library_access/origin_travel_times.csv`
- `data/cities/<city>/derived/library_access/library_access_summary.csv`
- `data/cities/<city>/derived/library_access/library_catchments.csv`
- `data/cities/<city>/derived/library_access/library_access_metadata.json`

Comparators:

- `data/comparators/library_access/delhi_toronto_access_comparison.csv`
- `data/comparators/library_access/ahmedabad_delhi_access_comparison.csv`
- `data/comparators/library_access/ahmedabad_toronto_access_comparison.csv`
- `data/comparators/library_access/library_access_summary.json`

Reports:

- `docs/library-accessibility-comparison.qmd`
- `docs/library-accessibility-comparison.pdf`
- `docs/library-accessibility-comparison.html`

## Standard Metrics

Core access metrics:

- `population`
- `branches`
- `branches_per_100k`
- `p50_minutes_to_nearest_library`
- `p75_minutes_to_nearest_library`
- `p90_minutes_to_nearest_library`
- `pct_population_within_10_min`
- `pct_population_within_15_min`
- `pct_population_within_20_min`
- `pct_population_within_30_min`
- `pct_population_within_45_min`
- `median_reachable_branches_30_min`
- `residents_per_branch`

Library capacity metrics, when available:

- `collection_per_resident`
- `annual_circulation_per_resident`
- `members_per_resident`
- `sqft_per_1000_residents`
- `seats_per_1000_residents`
- `staff_per_1000_residents`

## Confidence Labels

Every city output must include:

- `routing_tier`
- `transit_source`
- `library_location_source`
- `population_source`
- `service_area_source`
- `confidence`
- `notes`

This prevents a clean Toronto GTFS result from being falsely compared as equivalent to an OSM/corridor proxy in Delhi.

## Error Handling

The pipeline fails loudly when:

- A library location lacks latitude or longitude.
- An origin grid lacks population weights.
- A service area polygon is missing.
- A comparator mixes incompatible years without an explicit `year_alignment_note`.

The pipeline warns, but still emits lower-confidence outputs, when:

- Transit route geometry exists without schedules.
- Transit stops exist without headways.
- Library branch locations are geocoded rather than institution-published.

## Verification

Minimum checks:

- Unit tests for weighted quantiles and threshold shares.
- Schema tests for every canonical input and output table.
- Deterministic sample-city fixture with known nearest-library answers.
- Smoke run for Ahmedabad using existing in-repo locations and transit JSON.
- Toronto source fetch validation against Toronto Open Data package metadata.
- Delhi source validation that separates DPL locations, DMRC, and DTC/cluster bus inputs.

## Implementation Order

1. Build the shared access engine and tests.
2. Normalize Ahmedabad as the local proof of concept.
3. Normalize Toronto TPL branch locations and TTC transit inputs.
4. Normalize Delhi DPL locations and DMRC/DTC inputs.
5. Build pairwise comparator outputs.
6. Render the combined Quarto report.

## Sources To Track

- Toronto Public Library branch general information: https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/library-branch-general-information
- GTFS/OpenTripPlanner design basis: GTFS static transit feeds combined with OSM street networks are the standard basis for multimodal transit accessibility routing.
- Existing SevenT4 Ahmedabad sources under `data/cities/ahmedabad/source/libraries` and `data/cities/ahmedabad/source/transit`.
- Existing SevenT4 Delhi DPL operations sources under `data/cities/delhi/source/libraries`.
