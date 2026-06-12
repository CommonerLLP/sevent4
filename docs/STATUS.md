# SevenT4 — STATUS

_The cockpit. Rewritten by `/pm` (`.claude/skills/pm`). A one-screen snapshot of the atlas.
Last recomputed: **2026-06-11**._

## City-build funnel

**12 rostered · 12 consoles built · 12 cut-complete (ward + AC + PC) · 1 OpenCity-sourced.**
Stage discipline: _rostered → scaffolded → console-built → cut-complete → sourced → published._

| City | layers | ward·AC·PC | console | provenance | notes |
|---|--:|:--:|:--:|:--:|---|
| ahmedabad | 20 | ✓✓✓ | pub | — | seed city; road-money + heat + transit |
| **bengaluru** | **16** | ✓✓✓ | pub | **sources.json** | **first OpenCity build; four-axis reconciled** |
| chennai | 15 | ✓✓✓ | pub | — | |
| hyderabad | 14 | ✓✓✓ | pub | — | |
| jaipur | 14 | ✓✓✓ | pub | — | |
| kochi | 13 | ✓✓✓ | pub | — | |
| kolkata | 14 | ✓✓✓ | pub | — | |
| bhubaneswar | 12 | ✓✓✓ | pub | — | |
| kanpur | 12 | ✓✓✓ | pub | — | |
| mumbai | 12 | ✓✓✓ | pub | — | |
| pune | 12 | ✓✓✓ | pub | — | |
| visakhapatnam | 12 | ✓✓✓ | pub | — | |
| nagpur | 0 | — | — | — | backburner (Tier-B); not built |

**Cut spine: complete across all 12 built cities** — every city sliceable by ward / assembly / parliament.

## Bengaluru — the OpenCity pilot (this session)

- **Boundary spine:** GBA-369 wards (display) + BBMP-225 (canonical/historical) + 28 ACs + 5 PCs. All from
  OpenCity (BBMP/GBA/ECI KML). Per-ward census (SC/ST) rides on the BBMP-225 layer.
- **Finance (who-pays):** `ward_workorders` — **₹9,078 cr across 49,915 work orders (2013–22)**, named work +
  contractor + budget head per ward. 320 raw CSVs archived on `m1-storage`. KRIDL (state PSU) is the largest
  single payee — flagged, "investigate later."
- **Heat:** `ward_heat` LST wired (prior-session 30m build), area-weighted onto canonical wards.
- **Four-axis layer:** `ward_analysis` — caste · representation · spend · heat on ONE geometry (BBMP-225).
  Cross-axis correlations all weak (|r| ≤ 0.28) — reported honestly, no manufactured headline.

## Provenance debt (public-repo obligation)

**Only Bengaluru carries a `sources.json`.** The other 11 cities' layers are on the public console with no
machine-readable provenance file. This is a debt to close (own-built layers need their recipe named; any
third-party-sourced layer needs its citation). Priority: back-fill Ahmedabad first (the seed city).

## Stale / gaps (refresh + fix priorities)

- **Bengaluru: 60/225 wards grey on spend** — 198-ward (2013–22 ledger) ↔ 225-ward (2023 boundary) name gap.
  Fix: true 198-ward boundary or a name-crosswalk.
- **Bengaluru function layers (pass-2):** water/SWM/transport/health/env scoped in `docs/opencity-atlas-scope.md`,
  not yet pulled.
- **nagpur:** 0 layers — build or formally defer.
- **Devolution / decided-by scores** not computed for Bengaluru (Mumbai has 83%/71%; wire the matrix).

## Live ops

- `:8899` — Bengaluru preview server **alive** (`lsof -ti:8899 | xargs kill` to stop).
- `m1-storage` — **mounted**; OpenCity raw archives live there; in-repo `data/sources/` is gitignored.

## Roadmap-vs-actual (`docs/roadmap.md`)

- **Phase 1 (Ahmedabad baseline):** met as seed — full grammar (cuts, services, heat, finance, accountability).
- **Now:** multi-city expansion + the OpenCity harvest. Bengaluru is the proof that OpenCity → atlas works.
- Outcomes served this session: **O1** (jurisdiction legibility — cuts), **O2** (devolution — who-decides
  power-map), **O3** (social geography — SC/ST ward layer), **O4** (comparative — Mumbai vs Bengaluru).

## The commit gap — SevenT4's standing risk

> **~3,920 untracked + 11 modified on `feat/amc-finance-and-transit`. Nothing committed.**

A single PR of ~3,900 files is unreviewable. **Action: staged commits** (recipes+docs / built layers /
city scaffold). `data/sources/` + `notes/` + `memory/` correctly gitignored; pre-commit hook installed.

## On track?

**Yes on method, no on hygiene.** The atlas grammar works and Bengaluru proves the OpenCity pipeline. The one
thing that decides near-term health: **commit the work in reviewable slices and close the provenance debt** —
an uncommitted, partly-unsourced public repo is the real exposure, not the data.
