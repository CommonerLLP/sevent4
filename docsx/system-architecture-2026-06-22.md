# SevenT4 System Architecture

Generated: 2026-06-22

## Purpose

SevenT4 is a city-intelligence engine and Progressive Web App for political
education around the 74th Constitutional Amendment. The product outcome is not
only map exploration. It is civic literacy: residents should learn where they
live politically, who governs each civic problem, and why municipal power,
finance, and accountability must move from state/parastatal/Union control to
elected city institutions where the Constitution intended that shift.

## Architecture Rule

SevenT4 uses ports and adapters, not MVC, as the governing architecture.

- `sevent4.domain` owns facts, evidence, claims, and city-domain contracts.
- `sevent4.application` owns use cases: build a board roster, validate a public
  route graph, assemble a public-surface document.
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
- `sevent4.ports.acquisition`
- `sevent4.ports.evidence`
- `sevent4.ports.publication`
- `sevent4.application.why_air`
- `sevent4.application.public_site`
- `sevent4.adapters.filesystem`

Compatibility surfaces remain:

- `sevent4.contracts` re-exports the evidence contracts and filesystem helpers
  for existing tests and pages.
- `scripts/recipes/build_why_air_table.py` is now a thin CLI adapter over the
  WHY/air application service.

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
