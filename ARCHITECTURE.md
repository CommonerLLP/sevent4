# Architecture

This root document is the public entrypoint for the architecture contract.

- Canonical architecture doctrine: `docsx/architecture.md`
- Current system snapshot: `docsx/system-architecture-2026-06-22.md`
- Source policy and readiness grades: `docsx/source-policy-and-readiness.md`

The short version: The Unelected City uses a ports-and-adapters architecture.
Domain modules own city and evidence logic; application modules coordinate
ports; adapters own filesystem, public-source, browser, geospatial, HTML, and
network details; recipes remain thin CLI adapters.

The hexagonal refactor gate is closed for the declared scope and is guarded by
`tests/test_hexagonal_architecture.py`.
