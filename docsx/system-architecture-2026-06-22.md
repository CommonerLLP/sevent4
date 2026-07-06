# The Unelected City System Architecture

Generated: 2026-06-25

## Purpose

The Unelected City is a city-intelligence engine and Progressive Web App for political
education around the 74th Constitutional Amendment. The product outcome is not
only map exploration. It is civic literacy: residents should learn where they
live politically, who governs each civic problem, and why municipal power,
finance, and accountability must move from state/parastatal/Union control to
elected city institutions where the Constitution intended that shift.

## Architecture Rule

The Unelected City uses ports and adapters, not MVC, as the governing architecture.

- `sevent4.domain` owns facts, evidence, claims, pollution-board records, and
  city-domain contracts.
- `sevent4.application` owns use cases: build a board roster, validate a public
  route graph, assemble a devolution scorecard, or produce another
  public-surface document.
- `sevent4.ports` owns protocols that application services depend on.
- `sevent4.adapters` owns filesystem, HTML, JSON, browser, public-source, and
  future shared-infra integrations.
- `scripts/recipes` are CLI adapters and legacy acquisition recipes. They must
  shrink over time rather than accumulate business logic.
- `public/` is a generated/static public surface. It must not become the source
  of truth for facts.

## Evidence Pipeline

The normalized pipeline is:

1. **Source profile**: name the institution/source family, not an implementation
   class. Example: `in-ka-kspcb-annual-reports`, not `KspcbWebsiteFetcher`.
2. **Acquisition adapter**: fetch or receive the public record through direct
   HTTP, browser rendering, Google Drive, india-fetch egress, or RTI upload.
3. **Evidence contract**: normalize facts into `SourceProfile`, `FactRecord`,
   `ClaimRecord`, and `EvidenceBundle`.
4. **Application use case**: combine validated facts into a public document or
   civic teaching surface.
5. **Public adapter**: write JSON/HTML/assets and validate internal links and
   rendered claim IDs.

Generic acquisition and provenance should flow to `commoner-probe`. Generic
text/PDF extraction, indexing, search, embeddings, FTS, vector storage, and MCP
retrieval should flow to `partial-recall`. Generic public finance parsing should
flow to `budget-crawler`. The Unelected City keeps city interpretation, evidence
contracts, public education flows, and topic-specific normalizers.

## Current Operational Boundaries

Implemented package boundaries:

- `sevent4.domain.ahmedabad_library_paper_figures`
- `sevent4.domain.amc_budget`
- `sevent4.domain.bengaluru_finance`
- `sevent4.domain.bengaluru_opencity`
- `sevent4.domain.bengaluru_ward_analysis`
- `sevent4.domain.budget`
- `sevent4.domain.chennai_finance`
- `sevent4.domain.chennai_opencity_water`
- `sevent4.domain.delhi_acquire`
- `sevent4.domain.delhi_air_quality`
- `sevent4.domain.delhi_dpl_extract`
- `sevent4.domain.delhi_finance`
- `sevent4.domain.delhi_library_paper_figures`
- `sevent4.domain.delhi_library_spatial`
- `sevent4.domain.delhi_opencity`
- `sevent4.domain.dpl_geocode`
- `sevent4.domain.dpl_hierarchy`
- `sevent4.domain.evidence`
- `sevent4.domain.finance_flow`
- `sevent4.domain.gujarat_transport`
- `sevent4.domain.heat`
- `sevent4.domain.kanpur_wards`
- `sevent4.domain.library_exclusion`
- `sevent4.domain.library_networks`
- `sevent4.domain.mj_library`
- `sevent4.domain.opencity_catalogue`
- `sevent4.domain.pollution`
- `sevent4.domain.rbi_finance`
- `sevent4.domain.roads`
- `sevent4.domain.suburban_rail`
- `sevent4.ports.acquisition`
- `sevent4.ports.budget`
- `sevent4.ports.city_build`
- `sevent4.ports.delhi_acquire`
- `sevent4.ports.evidence`
- `sevent4.ports.finance`
- `sevent4.ports.heat`
- `sevent4.ports.jurisdiction`
- `sevent4.ports.kanpur`
- `sevent4.ports.library_access`
- `sevent4.ports.metrics`
- `sevent4.ports.officials`
- `sevent4.ports.publication`
- `sevent4.ports.rbi_finance`
- `sevent4.ports.representatives`
- `sevent4.ports.roads`
- `sevent4.ports.sources`
- `sevent4.ports.transit`
- `sevent4.application.acquisition`
- `sevent4.application.ahmedabad_library_paper_figures`
- `sevent4.application.amc_budget`
- `sevent4.application.bengaluru_finance`
- `sevent4.application.bengaluru_opencity`
- `sevent4.application.bengaluru_ward_analysis`
- `sevent4.application.budget`
- `sevent4.application.chennai_finance`
- `sevent4.application.chennai_opencity_water`
- `sevent4.application.city_build`
- `sevent4.application.city_console`
- `sevent4.application.comparators`
- `sevent4.application.delhi_acquire`
- `sevent4.application.delhi_air_quality`
- `sevent4.application.delhi_dpl_extract`
- `sevent4.application.delhi_finance`
- `sevent4.application.delhi_library_paper_figures`
- `sevent4.application.delhi_library_spatial`
- `sevent4.application.delhi_opencity`
- `sevent4.application.dpl_geocode`
- `sevent4.application.dpl_hierarchy`
- `sevent4.application.finance`
- `sevent4.application.gujarat_transport`
- `sevent4.application.heat`
- `sevent4.application.jurisdiction`
- `sevent4.application.kanpur`
- `sevent4.application.library_access`
- `sevent4.application.library_exclusion`
- `sevent4.application.metrics`
- `sevent4.application.mj_library`
- `sevent4.application.officials`
- `sevent4.application.public_site`
- `sevent4.application.rbi_finance`
- `sevent4.application.representatives`
- `sevent4.application.roads`
- `sevent4.application.sources`
- `sevent4.application.transit`
- `sevent4.application.why_air`
- `sevent4.adapters.acquisition_filesystem`
- `sevent4.adapters.ahmedabad_library_paper_figures_geospatial`
- `sevent4.adapters.amc_budget_filesystem`
- `sevent4.adapters.bengaluru_finance_filesystem`
- `sevent4.adapters.bengaluru_opencity_filesystem`
- `sevent4.adapters.bengaluru_ward_analysis_geospatial`
- `sevent4.adapters.budget_filesystem`
- `sevent4.adapters.budget_http`
- `sevent4.adapters.budget_ocr`
- `sevent4.adapters.chennai_finance_filesystem`
- `sevent4.adapters.chennai_opencity_water_filesystem`
- `sevent4.adapters.city_build_filesystem`
- `sevent4.adapters.comparators_filesystem`
- `sevent4.adapters.delhi_acquire_filesystem`
- `sevent4.adapters.delhi_air_quality_filesystem`
- `sevent4.adapters.delhi_dpl_extract_filesystem`
- `sevent4.adapters.delhi_finance_filesystem`
- `sevent4.adapters.delhi_library_paper_figures_matplotlib`
- `sevent4.adapters.delhi_library_spatial_geospatial`
- `sevent4.adapters.delhi_opencity_geospatial`
- `sevent4.adapters.dpl_geocode_net`
- `sevent4.adapters.dpl_hierarchy_filesystem`
- `sevent4.adapters.gujarat_transport_filesystem`
- `sevent4.adapters.heat_filesystem`
- `sevent4.adapters.heat_planetary`
- `sevent4.adapters.jurisdiction_geospatial`
- `sevent4.adapters.kanpur_filesystem`
- `sevent4.adapters.library_access_filesystem`
- `sevent4.adapters.library_exclusion_filesystem`
- `sevent4.adapters.library_networks_filesystem`
- `sevent4.adapters.metrics_filesystem`
- `sevent4.adapters.mj_library_filesystem`
- `sevent4.adapters.officials_filesystem`
- `sevent4.adapters.rbi_finance_filesystem`
- `sevent4.adapters.representatives_filesystem`
- `sevent4.adapters.roads_filesystem`
- `sevent4.adapters.sources_filesystem`
- `sevent4.adapters.transit_filesystem`
- `sevent4.adapters.finance_filesystem`
- `sevent4.adapters.filesystem`

Compatibility surfaces remain:

- `sevent4.contracts` re-exports the evidence contracts and filesystem helpers
  for existing tests and pages.
- `scripts/recipes/delhi/build_atlas_source_inventory.py` is now a thin CLI
  adapter over the acquisition application service. The filesystem adapter
  reads the OpenCity catalogue JSON and writes inventory CSVs plus the manifest,
  while the application service owns city filtering, axis classification,
  shortlisting, and row shaping.
- `scripts/recipes/scope_opencity_for_atlas.py` is now a thin CLI adapter over
  the acquisition application service. The application layer owns OpenCity
  atlas-axis classification, representative-cut geometry detection, structured
  resource ranking, and markdown note construction.
- `scripts/recipes/delhi/acquire_finance.py` still owns live curl/download
  behavior, but finance document manifest and run-log record shaping now route
  through the acquisition application service and shared acquisition document
  record.
- `scripts/recipes/libraries/source_archive.py` still owns curl, PDF text
  extraction, OCR invocation, and archive-file I/O. Shared acquisition
  application code now owns Google Drive download URL normalization, sparse-text
  OCR detection, and DPL staffing-row parsing.
- `scripts/research/run_dpl_parliament_probe.py` still owns commoner-probe
  loading and probe execution. Shared acquisition application code now owns the
  DPL parliament-topic filter and Sansad session-range parsing.
- `scripts/recipes/ahmedabad/extract_mj_library.py` still owns site-content
  fetching, PDF text export, location-file reads, and network JSON writes.
  Shared acquisition application code now owns M.J. Library PDF classification
  and disclosure-year parsing.
- Library access recipes now route distance/access math, city summary shaping,
  pairwise comparison rows, and IFLA service-detail audit rows through the
  library-access application service. Toronto comparator headline row shaping
  also lives in the application layer. Filesystem adapters load source CSV rows
  and write summary CSV outputs; the recipe scripts remain CLI adapters.
- `scripts/recipes/build_devolution_scorecard.py` is now a thin CLI adapter
  over the public-site application service. The application layer owns
  service-provider scoring, registry alignment, preserved special-case rows,
  and governance-update shaping; the filesystem adapter owns service-map,
  registry, scorecard, and governance JSON I/O.
- Jurisdiction crosswalk recipes are now thin CLI adapters over the jurisdiction
  application service. The application layer owns crosswalk document shaping,
  field cleaning, sort order, thresholds, and summary counts; the geospatial
  adapter owns GeoPandas/YAML reads, spatial joins/intersections, and JSON
  writes for both generic representative-point crosswalks and Ahmedabad overlap
  crosswalks.
- The city-console CLI now loads `city.yaml` and `layer_manifest.json` through
  a filesystem input adapter and publishes through a public-surface adapter; the
  application service depends on the `sevent4.ports.publication` contracts.
- `scripts/recipes/build_why_air_table.py` is now a thin CLI adapter over the
  WHY/air application service. The filesystem adapter parses
  `capacity.json` into `sevent4.domain.pollution` records before the
  application builds public rows.
- Budget explorer and money-flow CLIs now route through the finance application
  service. Filesystem adapters load city and budget inputs, while the
  application depends on `sevent4.ports.finance` rather than concrete files.
- `sevent4.metrics.ward_service_access` is now a thin CLI adapter over the
  metrics application service. The filesystem adapter loads ward, service, and
  GTFS stop layers before the application computes ward service-access rows.
- Ahmedabad heat recipes now route through the heat application service. Domain
  code owns QA masking, brightness conversion, ward LST summaries, and
  layer-manifest entries; adapters own Planetary Computer access, raster
  sampling, file writes, and manifest JSON I/O.
- Ahmedabad ward transit-frequency and service-access composite recipes now
  route through the metrics application service. The filesystem adapter loads
  GTFS CSV tables, ward/AC GeoJSON, and jurisdiction-crosswalk records, while
  the application owns stop-to-ward assignment, frequency fields, composite
  ward scoring, and AC rollups.
- Ahmedabad representative fetch and parse recipes now route through the
  representatives application service. The application layer owns source
  manifest row shaping, Gujarati councillor text parsing, validation, officer
  records, and ward-layer representative fields; the filesystem adapter owns
  document download, `pdftotext`, CSV/JSON writes, and ward GeoJSON reads/writes.
- `scripts/recipes/build_city.py` is now a thin CLI adapter over the city-build
  application service. The application layer owns ward/AC/PC normalization,
  councillor merging, city metadata shaping, governance JSON shaping, and layer
  manifest construction; the filesystem adapter owns source GeoJSON/CSV/JSON
  reads plus generated layer, manifest, governance, and `city.yaml` writes.
- `sevent4.transit.gtfs_corridors` is now a thin CLI adapter over the transit
  application service. The filesystem adapter loads GTFS CSV tables before the
  application builds route-corridor GeoJSON.
- Ahmedabad budget recipes (`fetch_city_budget`, `ocr_city_budget`,
  `parse_city_budget`) are now thin CLI adapters over the budget application
  service. `sevent4.domain.budget` owns Gujarati-digit number parsing, OCR
  summary-label matching, finance-book link identity, dense-page selection, and
  the per-city source/label registries; the application owns finance-link
  discovery, manifest/row shaping, and OCR-parse orchestration; `budget_http`
  owns HTTP/curl fetching, `budget_ocr` owns the poppler/tesseract toolchain, and
  `budget_filesystem` owns OCR text reads, CSV/manifest/PDF writes.
- `scripts/recipes/delhi/extract_dpl_library.py` is now a thin CLI adapter over
  the Delhi DPL extraction application service. Domain code owns annual metric,
  location, geocode-cache, and long-table shaping; the filesystem adapter owns
  CSV/JSON reads and writes.
- Bengaluru OpenCity finance, boundary, jurisdiction, and ward-reconciliation
  recipes now route through Bengaluru application services. Domain modules own
  work-order aggregation, OpenCity resource planning, curated-layer records, and
  ward-analysis property shaping; filesystem/geospatial adapters own downloads,
  hashing, GeoPandas joins, and JSON/GeoJSON output.
- Chennai GCC finance and OpenCity water/flood recipes now route through
  Chennai application services. Domain modules own finance CSV parsing,
  zone-layer shaping, water resource selection, and curated-layer records; the
  adapters own OpenCity requests, CSV files, KML/KMZ conversion, and layer
  reports.
- Ahmedabad and Delhi library-paper figure scripts are thin CLI adapters. The
  application layer owns figure-build orchestration and scalar stats; plotting,
  geospatial reads, Matplotlib backend setup, and figure writes live in adapter
  modules.
- `sevent4.qa.browser_smoke` is the browser-smoke QA adapter. It serves the
  checked-in static bundle locally and uses the Playwright CLI to screenshot
  `/index.html`, `/public/index.html`, and the Ahmedabad console route across
  mobile, tablet, and desktop viewports.

## Public Education Surface

The homepage is a civic pedagogy game before it is a map launcher. The first
interaction asks where the resident lives and tests local political knowledge:
ward, councillor, MLA, MP, last local election, whether they voted, and which
institution controls a given problem. The tone must reveal the knowledge gap
without shaming the resident. The political conclusion is direct: neutrality is
already a political position; city residents need politicization around local
power, not only state and national voting.

The macro site-map must remain connected:

- home
- whose-city game
- city consoles
- WHY chapters
- findings
- devolution/about surfaces

This is enforced by the public route-graph application service and tests.

## Migration Standard

Every new feature must answer:

- Is this reusable acquisition/provenance? Move or backflow to `commoner-probe`.
- Is this generic extraction/search/retrieval? Move or backflow to
  `partial-recall`.
- Is this generic fiscal parsing? Move or backflow to `budget-crawler`.
- Is this project-specific interpretation or pedagogy? Keep it here behind a port.

Legacy scripts are permitted only as adapters. When a legacy script changes,
move any reusable logic into `sevent4.application` or the appropriate shared
repo before adding new behavior.
