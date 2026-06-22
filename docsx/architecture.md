# SevenT4 System Architecture

Status: binding target architecture for The Unelected City.
Last updated: 2026-06-22T19:30:29Z.

## Purpose

SevenT4 exists to help people become politically literate about Indian city
power and to move from private frustration to public action.

The product has two equal identities:

1. **City intelligence engine**: a reproducible evidence system for Indian
   city governance, finance, services, labour, land, mobility, environment,
   and accountability.
2. **Public education Progressive Web App**: a fast, usable public surface
   that teaches residents how their city is governed, who controls each
   decision, where money and authority sit, and what political demand follows.

Neither identity is subordinate to the other. A beautiful public page without a
reproducible evidence chain is propaganda risk. A rigorous engine without a
teachable public surface is inert research. SevenT4 must be both.

## Intended Political Outcome

The intended outcome of the SevenT4 political education program is that the
spirit and letter of the Constitution (Seventy-fourth Amendment) Act, 1992 are
executed and in place.

That means the campaign is not merely asking for better dashboards, better
service delivery, cleaner budgets, or more responsive officials. Those are
intermediate gains. The constitutional outcome is that municipalities become
real institutions of self-government, with the powers, authority,
responsibilities, finance, staff, planning capacity, data, and public
accountability needed to govern urban life.

SevenT4 therefore treats Article 243W, the Twelfth Schedule, ward committees,
metropolitan planning, district planning, municipal finance, state finance
commissions, elections, representative accountability, and actual state-level
devolution orders as one connected implementation problem.

The campaign outcome is:

```text
Residents understand what the 74th Amendment promised.
Residents see where their city violates or evades that promise.
Residents can name the authority, budget, staff, law, and elected chain involved.
Residents can organize demands that force States and institutions to execute
the constitutional transfer of urban power.
```

## Core Political Goal

SevenT4 should make Indian urban governance legible enough that residents,
workers, tenants, students, organizers, journalists, lawyers, and ward-level
political actors can ask sharper constitutional and political questions:

- Who controls this service?
- Who funds it?
- Who staffs it?
- Which elected body can challenge it?
- Which non-elected authority is insulated from public pressure?
- What fact can be put on a poster, petition, meeting agenda, hearing note, or
  court affidavit?
- Which part of the 74th Amendment promise is being denied here?
- What transfer of power, money, staff, data, or sanction would make the
  municipality a real institution of self-government?

The codebase exists to support this political education goal. Engineering
quality is not separate from politics here: reproducible evidence is what keeps
the public argument honest.

## Constitutional Implementation Frame

SevenT4's top-level object is not a map layer, a page, or a dataset. It is a
constitutional implementation gap.

Each domain is read through the 74th Amendment question:

```text
What did Part IXA and the Twelfth Schedule place within the horizon of
municipal self-government, and where does the real power sit now?
```

For each city and domain, SevenT4 should model:

- **Function**: which Twelfth Schedule function or related urban power is at
  stake.
- **Formal assignment**: what the Constitution, state municipal law, rules,
  notifications, schemes, and orders say.
- **Actual controller**: which department, parastatal, authority, board,
  utility, police unit, SPV, contractor, court process, or state office controls
  the decision in practice.
- **Money**: who raises, allocates, withholds, parks, or spends the funds.
- **Staff**: who has sanctioned posts, filled posts, vacancies, outsourced
  staff, inspectors, engineers, planners, enforcement officers, and field
  capacity.
- **Data**: who holds the records and whether the public can inspect them.
- **Sanction**: who can permit, inspect, stop, penalize, approve, acquire,
  demolish, prosecute, or withhold.
- **Elected chain**: ward councillor, municipal body, MLA, state minister, MP,
  and Union role where applicable.
- **Public action hook**: petition, ward committee, council question, assembly
  question, RTI, public hearing, budget demand, court/tribunal route, campaign
  demand, or electoral question.

This is the constitutional data model. Domain facts exist to populate it.

## Architectural Doctrine

SevenT4 follows a ports-and-adapters architecture, also known as hexagonal
architecture.

The rule is simple:

```text
Core facts and domain logic must not depend on how sources are fetched,
how PDFs are parsed, how pages are rendered, or which agent/browser/tool
performed the work.
```

The core should know about cities, wards, institutions, facts, claims, sources,
units, dates, uncertainty, and public surfaces. It should not know whether a
record arrived through curl, Brave, the India fetch box, Google Drive, RTI,
OpenCity, a Drupal site, a PDF parser, an MCP tool, or a human audit.

Adapters are replaceable. Facts are not.

## CommonerLLP Layering

SevenT4 does not own every layer. It sits inside the CommonerLLP toolchain:

```text
commoner-probe
  public-record acquisition, HTTP discipline, manifests, raw files, run logs

partial-recall
  text/PDF extraction, corpus adapters, chunking, search, retrieval

budget-crawler
  public finance, budget books, RBI/OBI/NHA/OOPE/fiscal parsers

sevent4
  Indian city domain models, normalized city facts, political interpretation,
  generated public PWA surfaces, browser QA
```

If a capability is reusable across repos, it belongs upstream. SevenT4 should
not grow its own generic crawler, generic PDF extractor, search stack, or
budget parser.

The design pattern to copy is `commoner-probe`:

```text
public disclosure portals
  -> manifest.jsonl        source metadata and provenance
  -> files/PDFs            raw source artifacts
  -> extracted records     structured text or records
  -> analysis              downstream interpretation
  -> public surface        generated education/action view
```

SevenT4 extends this pattern from parliamentary questions and committee reports
to Indian city domains: traffic, parking, roads, air, water, sanitation,
libraries, public health, construction labour, municipal finance, land,
transport, flooding, and representative accountability.

The city intelligence engine must therefore answer two questions for every
domain:

1. What is happening materially in the city?
2. What does that reveal about the non-implementation, partial implementation,
   or evasion of the 74th Amendment?

## Hexagonal Shape

SevenT4's target shape:

```text
                         Public PWA
                            ^
                            |
                 public view generators
                            ^
                            |
source adapters -> raw artifacts -> extractors -> fact store -> claims
                            ^                         |
                            |                         v
                    run logs/checksums          domain analysis
```

### Core Domain

The core domain is made of stable concepts:

- `ConstitutionalMandate`
- `TwelfthScheduleFunction`
- `DevolutionInstrument`
- `ImplementationGap`
- `CityRegion`
- `Boundary`
- `Ward`
- `AssemblyConstituency`
- `ParliamentaryConstituency`
- `Institution`
- `AuthorityRelationship`
- `FunctionAssignment`
- `FinanceAssignment`
- `StaffingAssignment`
- `SanctionAssignment`
- `SourceProfile`
- `RawArtifact`
- `ExtractedRecord`
- `Fact`
- `Claim`
- `PublicSurface`
- `QaResult`

Domain-specific fact families extend the common fact contract:

- `DevolutionTransferFact`
- `WardCommitteeFact`
- `MunicipalElectionFact`
- `StateFinanceCommissionFact`
- `AirBoardCapacityFact`
- `MunicipalBudgetFact`
- `RoadContractFact`
- `ParkingAssetFact`
- `TrafficEnforcementFact`
- `TransitAccessFact`
- `WaterSupplyFact`
- `SanitationFact`
- `FloodRiskFact`
- `LibraryAccessFact`
- `BOCWRegistrationFact`
- `ConstructionLabourBenefitFact`
- `RepresentativeFact`

### Ports

Ports are interfaces the core expects. They should be named by capability, not
by institution:

- `SourceProfileLoader`
- `SourceFetcher`
- `RawArtifactStore`
- `ManifestWriter`
- `TextExtractor`
- `RecordExtractor`
- `FactExtractor`
- `FactStore`
- `ClaimBuilder`
- `ConstitutionalGapAnalyzer`
- `ViewModelBuilder`
- `PublicSurfaceRenderer`
- `BrowserQaRunner`
- `RunLogWriter`

### Adapters

Adapters implement ports for concrete technologies or source quirks:

- `HttpFetcher`
- `IndiaSocksTransport`
- `BrowserRenderedFetcher`
- `DrupalListingParser`
- `GoogleDriveFileFetcher`
- `PdfTextExtractor`
- `OcrTextExtractor`
- `OpenCityCatalogueAdapter`
- `NevaPortalAdapter`
- `SansadAdapter`
- `LocalJsonFactStore`
- `StaticPwaRenderer`
- `BraveBrowserQaAdapter`
- `GitHubPullRequestAdapter`

Adapters may know about KSPCB, AMC, BBMP, MCD, BOCW, or a state portal only at
the boundary. Core fact and claim code must not.

## Naming Rules

Use stable source IDs:

```text
<country>-<state-or-region>-<institution>-<source-family>
```

Examples:

```text
in-ka-kspcb-annual-reports
in-tn-tnpcb-annual-reports
in-gj-gpcb-annual-reports
in-gj-amc-budget-books
in-gj-amc-road-workorders
in-ka-bbmp-budget-books
in-dl-mcd-parking-contracts
in-ka-bocw-annual-reports
```

Transport is separate from source identity:

```text
direct-http
india-fetch-box-socks
browser-rendered
google-drive-download
manual-rti-upload
```

Wrong:

```text
KspcbWebsiteFetcher
IndiaKarnatakaPollutionControlBoardWebsiteFetcher
```

Better:

```text
source_profile: in-ka-kspcb-annual-reports
transport: india-fetch-box-socks
listing_adapter: drupal-listing
document_adapter: pdf-download
fact_extractor: pollution-board-annual-report
```

Institution-specific adapters are allowed only for genuine portal quirks, and
must stay at the edge.

## Source Profile Contract

Every source family should be represented as configuration before it becomes
code.

Target shape:

```yaml
id: in-ka-kspcb-annual-reports
country: IN
state: KA
publisher: Karnataka State Pollution Control Board
short_name: KSPCB
domain: air
source_type: annual_report_index
base_url: https://kspcb.karnataka.gov.in/annual-reports
platform: drupal
transport_policy: india_socks_if_direct_timeout
expected_artifacts:
  - listing_html
  - annual_report_pdf
fact_families:
  - pollution_board_finance
  - pollution_board_labs
  - pollution_board_enforcement
  - pollution_board_staffing
```

The source profile is part of the evidence apparatus. It must be hashed or
otherwise versioned in run logs, following `commoner-probe`'s topic/runlog
model.

## Fact Contract

Every public fact should be representable as structured data:

```json
{
  "fact_id": "in-ka-kspcb-2023-24-budget-total-receipts",
  "domain": "air",
  "city_id": "bengaluru",
  "institution_id": "in-ka-kspcb",
  "metric": "budget_total_receipts",
  "value": 348.70,
  "unit": "INR_crore",
  "period": "2023-24",
  "scope": "state",
  "source_id": "in-ka-kspcb-annual-reports",
  "raw_artifact_id": "sha256:...",
  "extracted_record_id": "sha256:...",
  "confidence": "high",
  "status": "found",
  "unit_check": "34869.93 lakh / 100 = 348.6993 crore",
  "retrieved_at": "2026-06-22T18:40:14Z"
}
```

The fact layer must preserve:

- metric
- value
- unit
- period
- geography/scope
- institution
- source
- raw artifact
- extraction method
- confidence
- unit conversion
- retrieval date
- uncertainty or missingness

No public number should exist only in HTML prose.

Every fact that supports a public campaign claim should also carry its
constitutional relevance when applicable:

```json
{
  "twelfth_schedule_function": "roads_and_bridges",
  "devolution_dimension": "finance",
  "implementation_question": "Is the municipality controlling the funds and execution for this function?",
  "actual_controller": "state_or_parastatal_or_municipal_body",
  "municipal_self_government_effect": "strengthens | weakens | bypasses | unknown"
}
```

This prevents SevenT4 from becoming a generic urban dashboard. Every fact must
be available to the constitutional argument.

## Claim Contract

A claim is not the same thing as a fact. A fact is source-grounded. A claim is
the public or analytical sentence built from one or more facts.

Target claim shape:

```json
{
  "claim_id": "why-air-kspcb-cash-vs-spend-2023-24",
  "surface": "why/air",
  "claim_text": "KSPCB opened 2023-24 with Rs 1,292 crore in cash, took in Rs 349 crore, spent Rs 79 crore, and earned Rs 67 crore from interest.",
  "fact_ids": [
    "in-ka-kspcb-2023-24-opening-balance",
    "in-ka-kspcb-2023-24-budget-total-receipts",
    "in-ka-kspcb-2023-24-budget-total-expenditure",
    "in-ka-kspcb-2023-24-interest-income"
  ],
  "rendered_at": "2026-06-22T18:40:14Z"
}
```

Public pages should render claims from structured claim records wherever
possible. If prose must be hand-written, every embedded number must be covered
by a claim test that links it back to fact IDs.

## Public Education PWA Layer

SevenT4 is a Progressive Web App, not just a data repository.

The PWA must support:

- fast first load on low-end phones
- offline or degraded access for core educational pages where practical
- installable app metadata through `site.webmanifest`
- stable URLs for sharing in organizing contexts
- accessible, responsive layouts
- dark and light modes
- printable/shareable public action views
- browser QA for every public surface that changes

Public surfaces are adapters over the fact and claim layer:

- city consoles
- WHY chapters
- findings pages
- devolution scorecards
- "whose city" explainers
- action notes
- ward/constituency accountability panels

The PWA layer is allowed to be persuasive, narrative, and pedagogical. It is
not allowed to invent or manually drift numbers.

The public education program should be built as a ladder:

```text
1. Recognition
   "This city problem is political, not private inconvenience."

2. Constitutional literacy
   "The 74th Amendment promised institutions of urban self-government."

3. Power mapping
   "Here is who actually controls this function, money, staff, data, and sanction."

4. Evidence
   "Here is the public record proving the gap."

5. Demand
   "Here is the transfer, disclosure, staffing, budget, or accountability demand."

6. Collective action
   "Here is how this becomes a ward question, council issue, assembly question,
   public hearing intervention, RTI campaign, legal record, or election demand."
```

Every public surface should know which rung of this ladder it serves.

## 74th Amendment Implementation Engine

The core analytical engine should be organized around implementation, not only
description.

For each city-domain pair, produce an implementation record:

```json
{
  "city_id": "bengaluru",
  "domain": "air",
  "twelfth_schedule_functions": ["public_health", "urban_forestry_environment"],
  "formal_municipal_role": "limited_or_absent",
  "actual_controllers": ["in-ka-kspcb", "state_environment_department"],
  "finance_location": "state_board",
  "staff_location": "state_board",
  "data_location": "state_board",
  "sanction_location": "state_board",
  "elected_accountability_chain": ["ward_councillor", "mla", "state_environment_minister"],
  "implementation_gap": "municipality bears urban health consequences but does not control pollution-board staffing, finance, inspection, or enforcement",
  "public_demand": "publish board capacity and require elected state accountability for staffing, inspections, and enforcement in the city"
}
```

This record is what converts city intelligence into political education.

The implementation engine should support comparisons:

- function transferred vs retained
- budget assigned vs unfunded mandate
- staff assigned vs vacant/outsourced
- data public vs opaque
- sanction local vs state/parastatal
- ward committee active vs absent
- metropolitan planning democratic vs technocratic
- municipality as self-government vs municipality as implementation clerk

## Domain Pipelines

Every city domain should follow the same pipeline:

```text
source profile
  -> raw archive
  -> manifest/run log
  -> extracted records
  -> normalized facts
  -> claims
  -> generated view model
  -> public PWA surface
  -> tests and browser QA
```

### Air and Pollution Boards

Inputs:

- CPCB and SPCB/PCC sources
- annual reports
- parliamentary answers
- court/NGT/CAG records
- AQI/station data

Facts:

- sanctioned posts
- vacancies
- working strength
- labs
- budgets
- inspections
- samples
- consents
- closure orders
- prosecutions

Views:

- board vacancy table
- finance strip
- city air panel
- public question: who answers for the air?
- 74th Amendment gap: urban public health consequences without municipal
  control over pollution-board staff, finance, inspection, and sanction

### Roads

Inputs:

- work orders
- resurfacing registers
- tender/procurement portals
- budget books
- DLP records
- contractor registers where public

Facts:

- ward
- road segment
- year
- contractor
- amount
- recurrence
- defect liability period
- penalty/recovery head
- engineering division

Views:

- recurrence maps
- contractor concentration
- ward-level road-money questions
- 74th Amendment gap: roads and bridges are municipal functions, but budgets,
  procurement, engineering control, defect liability, and penalties may be
  opaque or insulated from ward-level accountability

### Traffic and Transport

Inputs:

- traffic police challans
- crash reports
- signal contracts
- bus/metro/GTFS feeds
- road inventory
- parking enforcement
- mobility authority records

Facts:

- enforcement volume
- crash location/type
- signal/vendor contract
- bus speed/service frequency
- jurisdiction split
- transport-body responsibility

Views:

- mobility control map
- traffic enforcement accountability
- public demand note for street safety
- 74th Amendment gap: streets, roads, planning, public amenities, police,
  transport agencies, and metropolitan authorities split everyday mobility
  across elected and unelected chains

### Parking

Inputs:

- municipal parking contracts
- fee schedules
- tender documents
- road/land ownership records
- enforcement notices
- court orders

Facts:

- parking asset
- capacity
- operator
- fee
- land owner
- ward
- revenue
- enforcement power
- contract period

Views:

- who controls street space
- public land/private revenue explanation
- ward parking accountability panel
- 74th Amendment gap: land use, roads, public amenities, municipal revenue,
  police enforcement, and private operation combine in ways residents rarely
  see or vote on

### Construction Labour and BOCW

Inputs:

- BOCW board annual reports
- labour department records
- registration/benefit data
- cess collection and expenditure
- court/CAG records

Facts:

- registrations
- active workers
- benefits paid
- cess collected
- cess spent
- gender/city breakdown
- board staffing

Views:

- construction labour exclusion
- worker benefit gap
- city-building labour accountability
- 74th Amendment gap: the workers who build the city are governed through
  labour boards, welfare cess, contractors, and state machinery outside normal
  municipal citizenship

## Campaign Outputs

SevenT4 should generate not only pages but campaign-ready artifacts:

- ward-level accountability notes
- city-domain explainers
- public meeting handouts
- RTI templates
- assembly/council question prompts
- petition skeletons
- budget hearing notes
- printable posters with one verified claim
- classroom/workshop modules on the 74th Amendment
- share cards linking a city problem to a constitutional function

These outputs must be generated from claims and facts, not copied by hand.

## Reproducibility Rules

Every domain should eventually provide:

```bash
make acquire-<domain>
make extract-<domain>
make facts-<domain>
make build-<surface>
make test-<surface>
make qa-<surface>
```

For example:

```bash
make acquire-air
make extract-air
make facts-air
make build-why-air
make test-why-air
make qa-why-air
```

Current SevenT4 is not fully there. The architecture target is:

```text
raw source + source profile + extractor + fact schema + view generator
  = reproducible public claim
```

Manual HTML edits that repeat numbers are technical debt unless backed by
claim tests.

## Agentic Engineering Rules

SevenT4 should be agent-native but not agent-chaotic.

Modern agentic engineering gives us useful primitives:

- tools
- resources
- prompts
- sessions
- handoffs
- guardrails
- tracing
- sandboxed workspaces
- human-in-the-loop checkpoints

These map cleanly onto SevenT4:

```text
Tools      -> acquisition, extraction, build, test, browser QA
Resources  -> source profiles, schemas, manifests, facts, docs
Prompts    -> domain-specific research and QA instructions
Sessions   -> reproducible run logs and handoffs
Handoffs   -> branch/PR boundaries and agent coordination
Guardrails -> source hierarchy, no-secret checks, claim tests, browser QA
Tracing    -> run logs, artifact manifests, commit/PR links
```

Agents may execute work, but the architecture must be deterministic enough that
a human or a different agent can reproduce the result.

This doctrine is vendor-neutral. SevenT4 should be able to use Codex, Claude,
Gemini, Cursor, Grok/xAI, DeepSeek-compatible APIs, or future agents because
the repo exposes stable ports, manifests, facts, tests, and QA gates. The agent
is an operator, not the architecture.

The cross-vendor design lessons are:

- **Anthropic**: prefer simple, composable workflows before autonomous agents;
  use agents only when open-ended work truly needs model-directed tool use; make
  agent plans/tool use transparent; invest in agent-computer interfaces as
  seriously as human-computer interfaces.
- **Claude Code**: repo-level manifests, explicit permissions, hooks, skills,
  isolated workspaces, and project memory are part of the software interface.
  They must be maintained like code, not treated as chat preferences.
- **Cursor**: project, team, user, remote, and `AGENTS.md` rules; checkpoints;
  queued follow-ups; cloud-agent environments; hooks; MCP; and review artifacts
  show that agentic coding requires layered codebase instructions, rollback
  checkpoints, reproducible environments, policy hooks, and evidence artifacts.
- **Google ADK / Vertex agent practice**: agent systems need local development,
  production deployment paths, context management, tool-call handling,
  observability, traces, failure handling, and resumability.
- **OpenAI Agents SDK**: agents, tools, handoffs, guardrails, sessions, tracing,
  and sandboxed workspaces are useful runtime primitives when the task requires
  multi-step execution.
- **Grok / xAI API**: function calling, built-in web/X/code/RAG tools, Remote
  MCP tools, and multi-agent models reinforce a strict boundary: the model or
  provider may orchestrate tool use, but SevenT4 must own tool schemas,
  allowed-tool limits, provenance checks, and returned evidence.
- **DeepSeek API pattern**: function/tool calling reinforces the same boundary:
  the model proposes a tool call, but the system owns the actual function,
  schema, execution, and returned evidence.
- **MCP**: tools, resources, and prompts should be discoverable through a
  standard protocol, with data/tool concerns separated from transport.

SevenT4's conclusion from all of these is conservative:

```text
Use the simplest deterministic workflow that can prove the claim.
Escalate to agents only when the workflow needs judgment, exploration, or
multi-step adaptation.
When agents are used, constrain them with ports, source profiles, tests,
browser QA, run logs, and PR boundaries.
```

Agent rules:

- Agents must read coordination and architecture before substantive edits.
- Agent instructions should be layered by repo and subdirectory where needed;
  more specific rules override general rules.
- Agents must not bypass source profiles and fact schemas for one-off prose.
- Agents must not build generic infrastructure in SevenT4 when it belongs in
  `commoner-probe`, `partial-recall`, or `budget-crawler`.
- Agents must expose missing capabilities instead of silently working around
  them.
- Agent checkpoints are not Git history. Durable review still happens through
  commits, PRs, tests, run logs, and browser QA artifacts.
- Cloud or remote agents need explicit environment definitions, secrets policy,
  outbound-network policy, hooks, logs, and reviewable artifacts.
- Agents must use named branches and PRs.
- Agents must run tests and browser QA for public surfaces.
- Agents must not publish internal file paths or private analytical state in
  public PR bodies.

## Browser QA Rules

Tests are necessary but not sufficient for PWA work.

Any change to a public surface should be checked in a browser. At minimum:

- page loads at the local preview URL
- changed text is visible
- no obvious overlap or clipping
- light/dark mode still works where relevant
- mobile width is checked for changed components
- screenshots or notes are recorded for the PR/session

For generated data surfaces, browser QA should verify both:

1. the JSON/data file contains the expected facts;
2. the rendered page exposes the expected public teaching claim.

## Directory Responsibilities

Target responsibilities:

```text
data/
  gitignored source data, raw artifacts, extracted records, local fact layers

sevent4/
  reusable city-domain logic and package entry points

scripts/recipes/
  reproducible acquisition/build recipes that orchestrate package code

scripts/research/
  exploratory scripts; promote to recipes or package modules before reuse

public/
  generated or hand-authored PWA surfaces; public-facing only

docs/
  local-only working doctrine, research notes, and plans

docsx/
  tracked technical, policy, source, and architecture contracts

tests/
  unit, contract, claim, docs-sync, and artifact consistency tests
```

Long-term, public surfaces should be increasingly generated from facts and
claims rather than hand-maintained.

## Prohibited Patterns

Do not:

- type a new public number directly into HTML without a source-backed fact row
- build a repo-local crawler when `commoner-probe` should own it
- build a repo-local text/PDF extraction stack when `partial-recall` should own it
- build a repo-local budget parser when `budget-crawler` should own it
- name adapters after temporary infrastructure such as the India fetch box
- conflate transport with source identity
- treat Google Maps as an analytical data source
- treat OSM absence as real-world absence
- ship a public surface without browser QA
- let claims drift from facts
- let agent session memory be the only record of why a number is public

## Current Gap

SevenT4 already has pieces of this architecture:

- package entry points in `sevent4/`
- city data contracts in `docsx/`
- source policy in `docsx/source-policy-and-readiness.md`
- generated public JSON for several surfaces
- tests over city readiness, pollution capacity, finance parsing, and hygiene
- a PWA manifest
- shared theme and masthead assets

But the repo still has too much hand-wired public narrative. Some pages repeat
numbers in HTML after those numbers already exist in structured data. That is
not acceptable as the long-term standard.

The next architecture hardening work should:

1. define source-profile files for active domains;
2. define fact and claim JSONL contracts;
3. define `ConstitutionalMandate`, `TwelfthScheduleFunction`, and
   `ImplementationGap` schemas;
4. convert WHY/air finance prose into generated claim/view-model output;
5. add claim tests that scan public pages for numbers and map them to facts;
6. add browser QA scripts for changed PWA routes;
7. generate at least one campaign-ready 74th Amendment action artifact per
   public domain surface;
8. move reusable acquisition/extraction work upstream to the correct CommonerLLP
   repo.

## Reference Anchors

- `commoner-probe` design: public disclosure portals -> manifest -> files/PDFs
  -> extracted records -> analysis.
- Anthropic, "Building effective agents": start simple; prefer composable
  workflows; distinguish workflows from autonomous agents; maintain
  transparency; design and test tools carefully.
  https://www.anthropic.com/engineering/building-effective-agents
- Anthropic Claude Code docs: project memory, permissions, hooks, skills,
  sandboxing, and repo-level instructions are part of the agentic coding
  surface.
  https://code.claude.com/docs/en/best-practices
- Cursor Rules: persistent project, team, user, remote, and `AGENTS.md`
  instructions, including nested rules and precedence, are part of the coding
  interface.
  https://cursor.com/docs/rules
- Cursor Agent Overview: autonomous coding agents need explicit tools,
  checkpoints, queued follow-ups, browser access, file editing, shell execution,
  and question-asking primitives.
  https://cursor.com/docs/agent/overview
- Cursor Cloud Agents: remote coding agents need reproducible environments,
  secrets policy, network controls, MCP, hooks, artifacts, and PR-oriented
  delivery.
  https://cursor.com/docs/cloud-agent
- Google Agent Development Kit: agent frameworks should support managed,
  repeatable tasks, context handling, tool calls, parallel jobs, failures,
  resumability, local development, deployment, traces, and security.
  https://adk.dev/
- Model Context Protocol architecture: data layer and transport layer are
  separate; tools/resources/prompts are discoverable primitives.
  https://modelcontextprotocol.io/docs/learn/architecture
- OpenAI Agents SDK architecture: agents, tools, handoffs, guardrails,
  sessions, tracing, and sandboxed workspaces are the relevant agentic
  primitives.
  https://openai.github.io/openai-agents-python/
- xAI Grok Function Calling: the model requests a tool call, the application
  executes the function, and the result is returned to the model.
  https://docs.x.ai/developers/tools/function-calling
- xAI Remote MCP Tools: MCP servers can be attached as remote tools, with
  explicit server labels, optional allowed-tool filters, and authentication.
  https://docs.x.ai/developers/tools/remote-mcp
- xAI Multi Agent: provider-managed multi-agent execution makes hidden
  orchestration possible, so SevenT4 needs explicit evidence and artifact
  boundaries before trusting outputs.
  https://docs.x.ai/developers/model-capabilities/text/multi-agent
- DeepSeek API function calling: provider-neutral tool calling still requires
  the application to own function schemas, execution, and returned tool
  evidence.
  https://api-docs.deepseek.com/guides/function_calling
- Twelve-Factor App principles: declarative setup, explicit dependencies,
  build/release/run separation, attached services, logs as event streams.
  https://12factor.net/
