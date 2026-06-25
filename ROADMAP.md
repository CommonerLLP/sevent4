# Roadmap

## Current Gate

Publication readiness is the current gate.

The hexagonal refactor gate is closed for the declared scope: the package has
explicit `domain`, `ports`, `application`, and `adapters` layers, and
`tests/test_hexagonal_architecture.py` guards the boundary.

## Public Repository Visibility

The repo can be made public as a code and static-atlas repository when:

- the full unit suite passes;
- the browser-smoke gate passes for the checked-in public bundle;
- public docs describe source confidence honestly;
- official public-functionary contacts are treated as allowed public records;
- non-official OSM-derived contact fields remain subject to source audit;
- root control docs point readers to the canonical architecture docs.

## Evidence Work After Public Visibility

Public visibility does not mean every city claim is publication-grade. Next
evidence work remains city-by-city:

- normalize source-profile and evidence-contract boundaries;
- verify finance and walkability claims against source records;
- keep limitations visible where source confidence is mixed, partial, or OSM
  fallback;
- move reusable parsing, acquisition, or retrieval capability upstream when it
  generalizes beyond this repo.
