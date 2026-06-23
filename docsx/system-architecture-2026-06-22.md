# SevenT4 System Architecture

Generated: 2026-06-23

## Purpose

SevenT4 is a city-intelligence engine and Progressive Web App for political
education around the 74th Constitutional Amendment. The product outcome is not
only map exploration. It is civic literacy: residents should learn where they
live politically, who governs each civic problem, and why municipal power,
finance, and accountability must move from state/parastatal/Union control to
elected city institutions where the Constitution intended that shift.

## Architecture Rule

SevenT4 uses ports and adapters, not MVC, as the governing architecture.

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
retrieval should flow to `partial-recall`. Generic public-finance parsing should
flow to `public-finance`. SevenT4 keeps city interpretation, evidence contracts,
public education flows, and topic-specific normalizers.

## Current Operational Boundaries

Implemented package boundaries:

- `sevent4.domain.evidence`
- `sevent4.domain.pollution`
- `sevent4.ports.acquisition`
- `sevent4.ports.evidence`
- `sevent4.ports.finance`
- `sevent4.ports.jurisdiction`
- `sevent4.ports.library_access`
- `sevent4.ports.metrics`
- `sevent4.ports.publication`
- `sevent4.ports.representatives`
- `sevent4.ports.transit`
- `sevent4.application.city_console`
- `sevent4.application.acquisition`
- `sevent4.application.finance`
- `sevent4.application.jurisdiction`
- `sevent4.application.library_access`
- `sevent4.application.metrics`
- `sevent4.application.why_air`
- `sevent4.application.public_site`
- `sevent4.application.representatives`
- `sevent4.application.transit`
- `sevent4.adapters.acquisition_filesystem`
- `sevent4.adapters.finance_filesystem`
- `sevent4.adapters.filesystem`
- `sevent4.adapters.jurisdiction_geospatial`
- `sevent4.adapters.library_access_filesystem`
- `sevent4.adapters.metrics_filesystem`
- `sevent4.adapters.representatives_filesystem`
- `sevent4.adapters.transit_filesystem`

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
- `sevent4.transit.gtfs_corridors` is now a thin CLI adapter over the transit
  application service. The filesystem adapter loads GTFS CSV tables before the
  application builds route-corridor GeoJSON.
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
- Is this generic fiscal parsing? Move or backflow to `public-finance`.
- Is this SevenT4-specific interpretation or pedagogy? Keep it here behind a
  port.

Legacy scripts are permitted only as adapters. When a legacy script changes,
move any reusable logic into `sevent4.application` or the appropriate shared
repo before adding new behavior.
