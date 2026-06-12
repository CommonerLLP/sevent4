# SevenT4 Roadmap

_Status: operating plan tied to the mission document. Last updated:
2026-06-08._

This roadmap translates [the mission and vision](mission-vision.md) into work.
The mission is stable: make urban power and responsibility visible. The roadmap
is allowed to change as data, bugs, city priorities, and organizing needs
change.

## Mission Outcomes

Every task should serve at least one outcome:

- `O1` Jurisdiction legibility: users can see which public boundaries and bodies
  govern a place.
- `O2` Devolution diagnosis: users can see where municipal responsibility,
  finance, staff, sanction, and data are split.
- `O3` Social geography: deprivation is shown as caste/class/settlement/labour
  geography, not neutral scarcity.
- `O4` Comparative city-region analysis: Indian city-regions can be compared
  without erasing their different constitutional forms.
- `O5` Street-ready claims: every major screen can produce a public question,
  demand, or petition target.
- `O6` State-first accountability: ordinary cities are modeled through state
  municipal law and state control before central schemes are analyzed.
- `O7` Agglomeration literacy: users can distinguish official data boundaries
  from the wider urban agglomeration or city-region they actually live in.

## Phase 1: Ahmedabad Baseline

Goal: make Ahmedabad a reliable seed city and proof of method.

Ahmedabad should demonstrate the full SevenT4 grammar: ward, Assembly
constituency, Parliamentary constituency, service layers, heat/deprivation
layers, representative mapping, finance context, and accountability language.

Key outputs:

- Geometry QA for ward, AC, and PC layers.
- Fix the known Ellis Bridge AC geometry exclusion.
- Representative and public-office crosswalk validation.
- Service-layer freshness checks for schools, health, toilets, libraries,
  transit, police, fire, parks, and public amenities.
- Budget and finance provenance for AMC.
- First "who answers?" panel that distinguishes municipal, state,
  parastatal, and representative responsibility.

## Phase 2: Governance Data Contract

Goal: define the reusable city-region schema before scaling.

Each city-region needs a contract that separates:

- state municipal law and state urban department control
- municipal boundaries
- ward boundaries
- Assembly constituencies
- Parliamentary constituencies
- development authorities
- parastatals
- utilities
- police and land control
- transport bodies
- finance channels
- elected representatives
- service layers
- deprivation and heat layers
- source provenance and date of collection
- official data boundary
- agglomeration boundary
- functional-region explanation

This contract must support normal municipal corporations and exceptional
city-regions such as Delhi NCR.

For normal cities, the state government is the primary constitutional gatekeeper
for urban devolution. MoHUA and Union schemes should be represented as funding,
reform, standards, data, and mission layers unless the city is in a Union
Territory or another direct Union-control context.

## Phase 3: Delhi NCR Special Model

Goal: build the most constitutionally fragmented city-region as a special case,
not as a normal city.

Delhi NCR should be modeled as a metropolitan economy split across multiple
state chains and authority systems.

Minimum accountability ladders:

- Union government, Lieutenant Governor, DDA, Delhi Police, central land and
  security powers.
- Delhi NCT elected government and departments.
- Municipal bodies, including MCD, NDMC, and Delhi Cantonment Board.
- NCR regional planning and cross-state institutions.
- Haryana sub-atlas: Gurugram and related NCR nodes.
- Uttar Pradesh sub-atlas: Noida, Greater Noida, Ghaziabad, and related NCR
  nodes.

The NCR model should become the template for other multi-authority
metropolitan regions, but it should not force simpler cities into unnecessary
complexity.

## Phase 4: National Atlas Expansion

Goal: scale from one seed city to a comparative atlas of city-regions.

Priority set:

| Priority | City-region | Governance reason |
| --- | --- | --- |
| 1 | Ahmedabad-Gandhinagar-Sanand-Kalol/Kadi-side expansion | Seed implementation, AUDA/GUDA planning region, industrial/peri-urban growth, and baseline governance model |
| 2 | Delhi NCR | Union Territory, elected legislature, Union control, NCR jurisdictions, Haryana and UP sub-atlases |
| 3 | Mumbai / MMR | Municipal corporation, state power, MMRDA, port/rail/land/flood risk, finance concentration |
| 4 | Bengaluru / Greater Bengaluru | GBA, BBMP transition, BMLTA, BDA, BMRCL, BWSSB, BMTC, BESCOM, state control, tech-capital growth |
| 5 | Hyderabad | GHMC, HMDA, state projects, IT corridor, peri-urban expansion |
| 6 | Chennai | GCC, CMDA, floods, transport, water, state agencies |
| 7 | Kolkata | KMC, KMDA, old infrastructure, metropolitan region, labour and settlement history |
| 8 | Pune / Pimpri-Chinchwad | Twin municipal corporations, PMRDA, industrial and IT growth |
| 9 | Surat | Strong municipal capacity, flood/health history, migrant labour, industrial geography |
| 10 | Jaipur | State capital, heritage/tourism economy, planned expansion, peri-urban stress |

Visakhapatnam remains a GDP-strict candidate and should be evaluated when the
project chooses between a political-economy top ten and a GDP-estimate top ten.

## Phase 5: Public Action Layer

Goal: turn the atlas from inspection into organized pressure.

Each ward, constituency, and city-region page should be able to produce:

- a plain-language accountability summary
- the responsible institutions and representatives
- the relevant constitutional, statutory, or administrative hook
- budget or service evidence
- missing-data evidence
- petition or hearing targets
- a printable/shareable demand note

The page should not tell users what to think. It should give them the evidence
needed to ask sharper public questions.

## Backlog

| ID | Type | Workstream | Task | Mission tie | Output | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `DOC-001` | Doc | Doctrine | Maintain mission/vision as the stable project frame | `O1`-`O5` | `docs/mission-vision.md` | In progress |
| `DOC-002` | Doc | Doctrine | Keep roadmap and Gantt aligned with mission outcomes | `O1`-`O5` | `docs/roadmap.md`, `docs/gantt.md` | In progress |
| `BUG-AHD-001` | Bug | Ahmedabad | Fix Ellis Bridge AC geometry exclusion | `O1` | AC crosswalk includes a validated Ellis Bridge decision | Planned |
| `QA-AHD-001` | QA | Ahmedabad | Validate ward, AC, PC, and crosswalk feature counts | `O1` | QA notes and repeatable check command | Planned |
| `DATA-AHD-001` | Data | Ahmedabad | Add source freshness and provenance panel for all layers | `O1`, `O2` | Layer metadata exposed in console | Planned |
| `DATA-AHD-002` | Data | Ahmedabad | Validate councillor, MLA, MP, and public-office crosswalks | `O1`, `O5` | Representative table with dates and sources | Planned |
| `BUD-AHD-001` | Data | Finance | Build AMC budget ingest and parser plan | `O2`, `O5` | Budget source table and parser requirements | Planned |
| `FEAT-ACC-001` | Feature | Accountability UX | Build "who answers?" panel for selected ward/AC/PC | `O1`, `O2`, `O5` | UI panel linking place to institutions | Planned |
| `FEAT-ACC-002` | Feature | Accountability UX | Add devolution-gap labels for municipal vs state/parastatal power | `O2`, `O5`, `O6` | Visible gap markers in console | Planned |
| `FEAT-ACT-001` | Feature | Public action | Generate ward-level demand note from selected issue | `O5` | Printable/shareable Markdown or HTML note | Planned |
| `FEAT-ACT-002` | Feature | Public action | Add print/share public action view | `O5` | Public-facing action page for meetings, petitions, and campaigns | Planned |
| `DATA-SOC-001` | Data | Social geography | Identify available caste/class/settlement/labour proxies by city | `O3` | Source matrix and ethical-use notes | Planned |
| `CITY-001` | Data | City contract | Define reusable city-region config schema | `O1`, `O4` | Schema doc and sample config | Planned |
| `CITY-002` | Data | City contract | Model authority, fiscal, and finance-channel relationships | `O1`, `O2`, `O4` | Authority and finance-channel schema | Planned |
| `CITY-003` | Data | City contract | Define layer provenance model and collection-date requirements | `O1`, `O2` | Provenance schema and validation checklist | Planned |
| `CITY-004` | Data | City contract | Add state-first urban governance fields for state municipal law, state urban departments, and devolution orders | `O1`, `O2`, `O6` | State-first accountability schema | Planned |
| `CITY-005` | Data | City contract | Add official-boundary vs agglomeration-boundary model | `O1`, `O4`, `O7` | Boundary model and source warning fields | Planned |
| `CITY-NCR-001` | Research | Delhi NCR | Map NCR accountability ladders and special constitutional status | `O1`, `O2`, `O4` | NCR governance model note | Planned |
| `CITY-NCR-002` | Data | Delhi NCR | Scope Delhi NCT, MCD, NDMC, DCB, DDA, police, and NCRPB data | `O1`, `O2` | Source inventory | Planned |
| `CITY-NCR-003` | Data | Delhi NCR | Scope Gurugram as Haryana NCR sub-atlas | `O1`, `O4` | Gurugram authority and layer inventory | Planned |
| `CITY-NCR-004` | Data | Delhi NCR | Scope Noida/Greater Noida as UP NCR sub-atlas | `O1`, `O4` | Noida authority and layer inventory | Planned |
| `CITY-NCR-005` | Research | Delhi NCR | Write NCR law, finance, politics, culture, economy, and society explainer | `O2`, `O4`, `O7` | Website-ready NCR agglomeration explainer | Planned |
| `CITY-MMR-001` | Research | Mumbai / MMR | Map MCGM, MMRDA, state, rail, port, police, and land authorities | `O1`, `O2`, `O4` | MMR governance model note | Planned |
| `CITY-BLR-001` | Research | Bengaluru | Map BBMP, BDA, BWSSB, BMRCL, police, and state departments | `O1`, `O2`, `O4` | Bengaluru governance model note | Planned |
| `CITY-BLR-002` | Research | Bengaluru | Pull and analyze GBA, BBMP transition, multiple corporation, and ward committee material | `O1`, `O2`, `O6`, `O7` | Greater Bengaluru governance dossier | Planned |
| `CITY-BLR-003` | Research | Bengaluru | Pull and analyze BMLTA, NUTP 2006, UMTA, and coordinated transport governance material | `O1`, `O2`, `O4`, `O7` | Bengaluru transport-governance dossier | Planned |
| `CITY-SOUTH-001` | Research | South pilots | Scope Hyderabad and Chennai governance models | `O1`, `O2`, `O4` | Hyderabad and Chennai source inventories | Planned |
| `CITY-REST-001` | Research | National pilots | Scope Kolkata, Pune, Surat, and Jaipur governance models | `O1`, `O2`, `O4` | Four-city source inventory | Planned |
| `FEAT-EXP-001` | Feature | Public explanation | Add website explainer for official limits vs lived agglomeration | `O4`, `O7` | Boundary explainer component/page | Planned |
| `REF-001` | Research | Corpus | Build source index for Ambedkar, CAD, decentralization, federalism, and local-state studies | `O1`-`O5` | Bibliographic source spine | Planned |
| `REF-002` | Research | Corpus | Build official policy corpus for MoHUA, RBI, Planning Commission, NITI Aayog, Finance Commissions, World Bank, and IMF | `O1`, `O2`, `O4` | Institutional source index with local/Zotero paths | Planned |
| `REF-003` | Research | Corpus | Build Part IXA, state municipal acts, and city-specific legal source spine | `O1`, `O2`, `O5` | Municipal-law source index | Planned |

## Definition Of Done

A city-region is not ready for public release until:

- boundaries load without geometry errors
- every layer has source provenance and collection date
- every service metric identifies the responsible institution where possible
- representative data has a source and refresh date
- the page distinguishes municipal, state, Union, parastatal, and special-body
  authority
- social geography is handled explicitly and ethically
- the page can produce at least one public accountability question
- known missing data is displayed as missing, not silently ignored
- official data boundaries are distinguished from the wider lived
  agglomeration or city-region

## Operating Rule

Do not add a feature because it looks impressive. Add it because it helps a
resident, organizer, researcher, journalist, or public lawyer answer:

Who has the power, who has the money, who has the file, who has the vote, and
why are they not answerable here?
