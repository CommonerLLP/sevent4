# Ahmedabad: service access, who is starved, and who actually decides

A findings note for the SevenT4 atlas. It reports what the data shows about civic
service deprivation across Ahmedabad's 48 municipal wards — measured properly, per
resident — and locates the decision power that produces it. Every claim is tagged
with the data it rests on and its confidence. This is a research reading of public
records, not an audit finding.

The frame is the 74th Amendment and Article 243W: city dysfunction becomes visible
when responsibility is scattered across councillors, committees, appointed officers,
and state-controlled agencies. The job here is to re-assemble it.

## Method: which data can carry a finding, and which cannot

The single most important discipline in this work is sorting layers by whether an
*absence* in them is a signal or just missing data.

| Layer | Source | Status | Absence means |
|---|---|---|---|
| Public libraries | AMC official facility list | **authoritative, complete** | a real, missing library — a finding |
| Ward councillors / Municipal Commissioner | AMC official roster & directory | **authoritative** | — |
| Bus stops & service | GTFS (AMTS + AJL/Janmarg, official) | **authoritative** (scheduled, not realised) | real low service |
| Population | WorldPop 2020, 100 m | **modelled** — total reliable, single-ward noisy | use for patterns, not precise ranks |
| Schools, health, toilets, police | OpenStreetMap | **incomplete & spatially biased** | usually just unmapped — NOT a finding |
| Land-use character | OpenStreetMap | **unreliable** (see below) | — |
| `deprivation` index | upstream (provenance to be re-traced) | unverified for circularity | — |

Findings are built **only** on the authoritative rows. The OSM rows are kept off the
deprivation analysis because OSM completeness correlates with affluence, and would
manufacture the very periphery-poor gradient we are testing for. `schools` had 74
points for a city of seven million — it measures mapping effort, not schooling.

Services are normalised **per resident**, not per ward or per stop. A count of
facilities inside an arbitrary boundary rewards big wards and ignores how many people
actually live there; it is also exposed to the Modifiable Areal Unit Problem. Real
population (WorldPop, summed per ward via the WorldPop stats API) is the denominator.

## Finding 1 — 2.66 million people live in a ward with no public library

**16 of 48 wards have zero AMC public libraries. They hold 2,660,771 residents — 38%
of the city. 1.56 million of them live in residential (non-industrial) wards.**

This needs no modelling: AMC's own facility list, times real population. It is the
cleanest result in the atlas because both inputs are authoritative.

It is **not a partisan story**. Of the residential library-desert wards, eleven are
BJP-held and one (Maktampura) is INC — the neglect tracks *which areas* (poorer,
peripheral), not which party. Per-capita library provision correlates with
deprivation at **r = −0.39** (moderate; the strongest service–deprivation signal in
the data once population is the denominator).

The contrast that locates the decision: the city funds the flagship M.J. Library at
about **₹12 crore a year** (from the 22-year AMC budget series), while these wards
have none. Library funding is a budget choice — made by the Standing Committee and
the Commissioner, not by the councillors those residents elect (see Finding 4).

## Finding 2 — the bus network is everywhere and barely runs, worst where people are densest

AMTS blankets the city — **6,280 stops across all 48 wards** — but the median stop
sees a bus only about every 30 minutes, and most routes run under 20 trips a day.
Against the metro's 38 stations on one line, the bus reaches the city at roughly
**174 stops to 1 metro station**.

Per resident, the starvation concentrates in the dense, deprived east:

| Ward | Population | Bus departures/day per 1,000 residents | Libraries |
|---|---|---|---|
| Baherampura | 283,000 | 4.7 | 1 |
| Kubernagar | 67,000 | 7.5 | 1 |
| Lambha | 455,000 | 19 | 0 |
| Ramol Hathijan | 399,000 | 27 | 0 |
| Vastral | 241,000 | 28 | 0 |

Per-capita bus service correlates with deprivation at **r = −0.27**; the per-stop
frequency measure at Spearman **−0.33**, and that survived a robustness check
(reassigning the 1,693 stops that fall outside the municipal boundary moved it by
nothing). The signal is real but modest — a penalty concentrated at the deprived
bottom, not a smooth city-wide gradient. Janmarg/BRTS largely skips these eastern
wards entirely.

Caveat: GTFS is *scheduled* service, not realised, and the Janmarg feed under-counts
its own network — so these are floors, and actual delays are unmeasured (they require
real-time vehicle data, not timetables).

## Finding 3 — the "empty industrial periphery" is a data artifact; it is densely populated

OpenStreetMap tags **Lambha and Ramol Hathijan as "100% industrial."** WorldPop shows
they are the **two most populous wards in the city** (455,000 and 399,000). Had the
analysis "controlled for land use" using OSM, it would have deleted nearly a million
of the most deprived residents as non-existent.

This is the methodological lesson in one example: the periphery's low service is not
explained away by industrial zoning. People live there in large numbers, and they are
under-served per head. Authoritative population inverted the confound into the finding.

## Finding 4 — the power map: responsibility without power

Ahmedabad is **not run by its ward councillors.** Under the Gujarat Provincial
Municipal Corporations Act, executive power sits with:

- the **Municipal Commissioner** — an **IAS officer appointed by the Gujarat state
  government**, not elected by the city; chief executive over staff and budget
  execution (currently Shri Banchhanidhi Pani, IAS);
- the **Standing Committee** — ruling-party-controlled, approves the budget and
  contracts;
- the **state government**, which appoints the Commissioner and controls the Act and
  the finances; and
- **parastatals pulled out of the corporation** — AUDA (land/development), AMTS and
  AJL (buses), GMRC (metro), water boards.

So the accountability chain for a starved ward runs: *councillor you elect (can raise
it, cannot deliver it) → Standing Committee → Commissioner (appointed) → state.* The
elected layer carries the responsibility; the unelected layer holds the power. That is
Article 243W made literal, and Ambedkar's warning that the spirit of a constitution
can be perverted without changing its text — only the form of administration.

The atlas now encodes this directly: clicking a ward shows **the service reality**,
then **who you elect (with no real power)**, then **who actually decides (appointed,
not elected here)** — councillor party composition and official contacts beside the
state-appointed Commissioner's. (Councillor *names* are withheld pending verification
of the OCR'd AMC roster; party and official phone are shown.)

## Caveats and open data gaps

- **WorldPop** has intra-urban allocation error (some formal western wards look
  under-counted); single-ward per-capita ranks carry uncertainty. The 38% headline
  depends only on which wards have zero libraries (certain) and population in the dense
  eastern wards (where WorldPop is most reliable), so it is, if anything, conservative.
- **Deprivation index provenance** must be re-traced; if it ingested OSM service
  layers, the service–deprivation correlations are partly circular and need
  re-grounding on an independent (census / built-form) base.
- **Authoritative replacements needed** for OSM: UDISE for schools, an AMC/health-dept
  facility list for health, AMC's public-toilet register.
- **AUDA Development-Plan land-use** (authoritative zoning) is not yet in the repo —
  only OSM land-use and AUDA TP-scheme news. Acquiring and georeferencing the DP would
  replace the unreliable land-use character.
- **Bus delays** are unmeasured; they need a real-time feed (the Janmarg ETA endpoint /
  AMTS app) polled over time against the schedule.

## Cross-city pattern (emerging): the dream zone outside the boundary

A recurring structure shows up the moment the analysis is honest about boundaries,
and it is not specific to Ahmedabad — it is the atlas's core observation.

- In **Ahmedabad**, 1,693 of 6,599 bus stops (937 of them genuinely far) fall
  *outside* the AMC ward boundary: the lived, serviced city spills past the line the
  elected corporation governs.
- The **₹16,000 cr metro** sits in a Gujarat state SPV (GMRC), outside the elected
  corporation's control — the most expensive mobility decision in the city is the
  least accountable to it.
- In **Visakhapatnam**, the GVMC ward boundary stops near 17.55°N. The Andhra Pradesh
  SEZ at Atchutapuram–Rambilli — and the ~₹1.3 lakh-crore / $15 bn Google–AdaniConneX
  AI data-centre campus announced for the same Rambilli–Achyutapuram cluster
  (October 2025) — lie *south of that line*, on rural land in (now) Anakapalli
  district, beyond the elected city. The corporation absorbs the water and power
  spillover; the SEZ authority and the state hold the decision.

The pattern: **the future is built just outside the body that has to live with it.**
The same coastal-Andhra ground is the subject of Jamie Cross's *Dream Zones*
(Pluto, 2014) and "The Economy of Anticipation" (Duke, 2015) — his "economy of
anticipation" names this from the labour side, where SEZs on dispossessed rural land
at the urban edge sell a deferred future to the people they displace. Two decades on,
under the same chief minister who unveiled the SEZ at Davos, the dream is re-skinned
from manufacturing to AI on the same fields. The boundary doctrine and the economy of
anticipation are one observation from two directions: *the dream zone is not in the
city you elect.*

This is an early, geometric observation — derived from ward-extent boundaries while
the multi-city acquisition is still completing; the precise SEZ/data-centre parcels
and their water/power draw are not yet mapped. It is recorded here so it is not lost.

## Sources

- AMC public records: facility/library list, ward councillor roster, contact
  directory, budget books (ahmedabadcity.gov.in).
- Cross-city boundary observation: Jamie Cross, *Dream Zones: Anticipating Capitalism
  and Development in India* (Pluto, 2014) and "The Economy of Anticipation" (Duke UP,
  2015); Adani–Google Visakhapatnam data-centre announcement (Oct 2025); GVMC ward
  geometry (this repo).
- Transit: AMTS + AJL GTFS feed.
- Population: WorldPop 2020 (100 m, UN-adjusted), via the WorldPop stats API.
- Governance: Gujarat Provincial Municipal Corporations Act; AMC institutional
  structure.
- Method: HM Treasury Green Book (distributional analysis); standard treatment of the
  Modifiable Areal Unit Problem and OSM completeness bias in spatial epidemiology.
