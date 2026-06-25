# Public Readiness Audit - 2026-06-25

Status: ready for public repository visibility, with evidence limits disclosed.

## Verdict

The repo can be made public as a code repository and checked-in static atlas.
This does not certify every selectable city as publication-grade evidence.
Selectable, console-built, sourced, and publication-grade remain separate
states.

## Architecture

Hexagonal refactor status: closed.

The declared refactor gate is complete in the current tree: root public docs
point to the canonical architecture docs, and the current boundary is guarded
by `tests/test_hexagonal_architecture.py`.

## Contacts

Public-functionary contacts are allowed.

Councillor, commissioner, and public-office contact details from official
public rosters may be displayed with source attribution. OSM-derived contact
fields for non-official service layers remain open-data attributes, not
authoritative contact evidence, unless separately audited.

## Evidence Limits

The atlas is public-ready as an honest static surface. It is not claiming that
all city layers carry the same evidence weight:

- Ahmedabad remains the strongest seed case.
- Kanpur remains limited by partial ward geometry.
- Several cities still have missing or partial finance grades.
- OSM fallback service layers support context and mapping claims, not absence
  or deprivation claims by themselves.

## Verification Gates

Required before publication:

- `python3 -m unittest discover -s tests`
- `python3 -m sevent4.qa.browser_smoke`
- targeted review of any public-surface docs changed in the release branch

GitHub authentication must be valid before opening or merging a public-release
PR.
