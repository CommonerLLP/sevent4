# The Unelected City

_Repo id: `sevent4`. This repository is **private**; the atlas is a static bundle
in `public/`, served locally — there is no live public site._

Indian city government is built so that responsibility is hard to see.

Part IXA of the Constitution is about municipalities. It was inserted by the
Constitution (Seventy-fourth Amendment) Act, 1992, and covers Articles 243P to
243ZG. The political point is devolution: financial and political power should
move down from State governments to urban local bodies. Article 243W is the
practical hinge: municipalities are meant to function as institutions of
self-government, with planning, social justice, and Twelfth Schedule functions
in view.

But the city people actually live in is usually split across municipal
corporations, state departments, development authorities, parastatals, police,
transport agencies, utilities, contractors, engineers, ward councillors, MLAs,
and MPs. When a road breaks, a ward has no library, a bus route fails, a heat
pocket grows, a street floods again, or a public toilet disappears,
responsibility gets scattered until nobody is answerable.

The Unelected City does one small thing: it helps internet-literate residents map
a city problem to the public geography and public office around it.

It puts ward, Assembly constituency, Parliamentary constituency, transit, public
service, land-use, heat, and civic gap layers in one city console. A resident can
select a ward, Assembly constituency, or Parliamentary constituency and connect
a road, drainage, heat, transport, library,
school, health, sanitation, or public-space issue to the ward councillor, MLA,
MP, and relevant public office where the data is available.

This is not a smart-city dashboard and it does not decide legal liability. It
makes the first accountability question easier to ask: whose jurisdiction is
this, and why is this power not with the urban local body?

Finance is part of that jurisdiction question. Finance Commission, State
Finance Commission, and RBI municipal-finance records show whether Part IXA has
material force: grants, own-source revenue, property tax, user charges, State
transfers, accounts, and audit decide whether devolution is real or only
statutory. See [Finance Commissions and Municipal Devolution](research/finance-commission-local-bodies.md),
[RBI Municipal Finance Reports](research/rbi-municipal-finances.md), and
[State Finance Commission Histories](research/state-finance-commission-histories.md).
The follow-on synthesis is [Fiscal Devolution Versus Political Devolution](research/decentralization-fiscal-vs-political.md).

Ahmedabad is the deepest seed (22 layers, a 22-year city budget, and derived
service-access metrics). Twelve more cities ship consoles: Bengaluru, Bhubaneswar,
Chennai, Delhi, Hyderabad, Jaipur, Kanpur, Kochi, Kolkata, Mumbai, Pune, and
Visakhapatnam. Fork the repo, replace the city data, and build the same console
for any other urban local body.

## Project Direction

The political frame now lives in the public reading layer of the atlas — the maps
are the evidence, this layer is the argument:

- **Why** (`/why/`): the explanatory layer — why an ordinary city problem maps to
  an office no one elected to fix it. Chapter 01 is "the air."
- **Findings** (`/findings/`): a data → synthesis → case arc — the 73rd/74th
  devolution scoreboard, "Where is power safe?" (the Ambedkar scale-of-capture
  reading), and "Should a city be its own state?" (the Bombay city-state case).
- **Devolution** (`/devolution/`): the per-state 73rd/74th-Amendment scoreboard.
- **About** (`/about/`): Part IXA, the Twelfth Schedule, and the Ambedkarite frame.

Supporting research and operating policy are tracked in-repo:

- [Source Policy and City Readiness](docsx/source-policy-and-readiness.md): the
  rules for OSM, Google Maps, official sources, and graded city readiness.
- [Ready-City Geo Layer Queue](docsx/ready-city-geo-layer-queue.md): the next
  geodata acquisition targets.
- [Finance Commissions and Municipal Devolution](research/finance-commission-local-bodies.md),
  [RBI Municipal Finance Reports](research/rbi-municipal-finances.md),
  [State Finance Commission Histories](research/state-finance-commission-histories.md),
  and the synthesis [Fiscal Devolution Versus Political Devolution](research/decentralization-fiscal-vs-political.md).

## The Atlas Bundle

The atlas is a static bundle in the checked-in `public/` directory.

The repository is currently **private** and GitHub Pages auto-deploy is disabled
(`.github/workflows/pages.yml` is dormant), so there is no live public URL. Serve
the bundle locally (see "Start Ahmedabad" below), or — if the repo is later made
public — enable Pages to publish the same `public/` directory. The bundle exposes:

- `/` — the home "municipal ledger": pick a city, see the city/state/centre split
  and the services taken from the elected council
- `/why/`, `/findings/`, `/devolution/`, `/about/`, `/whose-city/` — the reading layer
- `/cities/<city>/` — 13 city consoles (ahmedabad, bengaluru, bhubaneswar, chennai,
  delhi, hyderabad, jaipur, kanpur, kochi, kolkata, mumbai, pune, visakhapatnam)
- `/cities/<city>/layers/*.geojson` — processed map layers
- `/assets/*` — shared theme, masthead, and vendored MapLibre files

There is no backend service. The atlas HTML, map assets, and processed city
layers are static files.

## Start Ahmedabad

```bash
git clone https://github.com/CommonerLLP/sevent4.git
cd sevent4
scripts/start.sh
```

Open the URL printed by the script:

```text
http://127.0.0.1:9174/public/cities/ahmedabad/index.html
```

`scripts/start.sh` creates the local environment if needed, builds the Ahmedabad
console, and serves the repo on localhost.

## Common Commands

Set up the local environment:

```bash
scripts/setup.sh
```

Build the Ahmedabad console:

```bash
scripts/build-ahmedabad.sh
```

Build any configured city:

```bash
scripts/build-city.sh ahmedabad
```

Serve the repo locally:

```bash
scripts/serve.sh ahmedabad
```

Use another port:

```bash
PORT=8080 scripts/start.sh
```

## Data Recipes

The atlas ships processed Ahmedabad layers so the console can run immediately.
The public recipes under `scripts/recipes/ahmedabad/` document how to rebuild
key pieces of that seed from public sources.

Ahmedabad city budgets are published as PDFs on the AMC budget page. AMC also
publishes balance sheets/audit reports and finance context pages:

```text
https://ahmedabadcity.gov.in/SP/Budget
https://ahmedabadcity.gov.in/SP/BalanceSheet
https://ahmedabadcity.gov.in/SP/AboutAMCFinance
```

The budget recipe is city-generic by filename but Ahmedabad-specific by default:

```bash
python3 scripts/recipes/ahmedabad/fetch_city_budget.py
python3 scripts/recipes/ahmedabad/fetch_city_budget.py --kind balance-sheet
python3 scripts/recipes/ahmedabad/fetch_city_representatives.py
python3 scripts/recipes/ahmedabad/parse_city_representatives.py
python3 scripts/recipes/ahmedabad/ocr_city_budget.py
python3 scripts/recipes/ahmedabad/parse_city_budget.py
```

That shape is intentional. Other cities may publish budgets through different
websites, portals, PDF naming schemes, spreadsheets, or tender-like archives, so
each city needs its own fetch adapter. Once PDFs are present under
`data/cities/<city>/source/budget/pdfs/`, the OCR and parse scripts can be
extended city by city.

Ahmedabad representative, officer, civic-center, and department source notes are
tracked in:

```text
data/cities/ahmedabad/source/public_sources.json
```

## What The Console Shows

The Ahmedabad seed is built around one workflow: pick a public geography, then
read the city problem through the offices that touch it.

It includes:

- ward boundaries and ward-level service access
- Assembly constituency and Parliamentary constituency boundaries
- ward councillor, municipal commissioner, MLA, and MP attribution where public
  data is available
- bus, BRTS, and metro layers
- public services such as libraries, schools, health facilities, toilets, fire,
  police, universities, and colleges
- land-use and road layers
- ward heat and 30m surface heat layers
- search, layer toggles, light/dark mode, and ward/Assembly constituency/Parliamentary constituency focus filters

The filters matter. A resident should be able to select a ward, Assembly constituency, or Parliamentary constituency and
see the city layers in relation to that public geography. As city datasets
improve, the same pattern can attach engineers, departments, zones, contractors,
budgets, public works, and grievance channels.

The public site should also explain why the console exists. Indian cities are
often dysfunctional because authority is split across elected local bodies,
state governments, parastatals, development authorities, utilities, police,
transport agencies, and contractors. The atlas should help residents see that
fragmentation instead of treating a city problem as just a point on a map.

## Governance Frame

The Unelected City starts from a narrow claim: public data should help residents
attribute ordinary civic problems to public jurisdiction.

The project avoids the usual smart-city habit of making data look apolitical.
Indian urban governance is political because powers, functions, funds, land, and
service delivery are split across institutions. A useful city console should make
that split visible instead of hiding it behind a neutral map.

For each city, the base data contract should therefore include:

- ward boundaries and councillor attribution
- Assembly constituency boundaries and MLA attribution
- Parliamentary constituency boundaries and MP attribution
- municipal zones, departments, engineers, works, budgets, and grievance channels
  where public data is available
- public service and infrastructure layers that let a resident connect a visible
  issue to the office that can be questioned

The Ahmedabad console is the example, not the limit. The same contract should be
usable for Kolkata, Chennai, Bengaluru, Hyderabad, Pune, Mumbai, Delhi, Surat,
Jaipur, Lucknow, and eventually any urban local body.

## City Data Contract

Each city lives under `data/cities/<city-id>/`.

```text
data/cities/ahmedabad/
  city.yaml
  source/
  layers/
    layer_manifest.json
    wards.geojson
    acs.geojson
    pcs.geojson
    jurisdiction_crosswalk.json
```

`city.yaml` tells the console builder where the city is and where its data lives:

```yaml
id: ahmedabad
name: Ahmedabad
country: India
state: Gujarat
center: [72.58, 23.03]
bbox: [72.45, 22.90, 72.74, 23.18]
crs_metric: EPSG:32643
layers_dir: data/cities/ahmedabad/layers
source_dir: data/cities/ahmedabad/source
outputs_dir: public/cities/ahmedabad
```

`layer_manifest.json` controls what appears in the console: layer id, display
name, GeoJSON or image file, layer type, default visibility, popup fields, and
map styling.

Minimum useful layers:

- `wards.geojson`: urban local body ward polygons
- `acs.geojson`: Assembly constituency polygons
- `pcs.geojson`: Parliamentary constituency polygons
- `jurisdiction_crosswalk.json`: District/Parliamentary constituency/Assembly constituency/Block/Ward or GP mapping used
  by the console filters
- service points: schools, health facilities, libraries, toilets, transit stops,
  and other city-specific public infrastructure

Ward councillor data should be joined into `wards.geojson` when a public ward
roster is available. MLA and MP attribution should be joined into `acs.geojson`
and `pcs.geojson` when public representative data is available.

The crosswalk is not optional. The console is an Indian governance tool first
and a map second. For every city, someone must match the relevant public
administration and electoral geographies:

- State and district
- Parliamentary constituency
- Assembly constituency
- Block, where relevant
- ULB ward for cities, or gram panchayat/local rural unit for rural work

Ahmedabad ships a generated `jurisdiction_crosswalk.json` as the complete
reference case. New city forks can start from:

```text
data/jurisdiction_crosswalk.stub.json
```

If polygons are available, generate the city crosswalk by intersecting wards or
GPs with ACs, PCs, districts, and blocks. If polygons are not available, curate
the table manually from official public records, keeping one row per real
overlap or assignment. Delhi should be handled with a separate governance
adapter when added; do not force it into a simple municipal model.

## Make A New City

1. Copy `data/cities/ahmedabad` to `data/cities/<your-city>`.
2. Edit `city.yaml`: name, center, bbox, CRS, and paths.
3. Replace `layers/wards.geojson`, `layers/acs.geojson`, and
   `layers/pcs.geojson`.
4. Replace or remove service layers in `layers/`.
5. Edit `layers/layer_manifest.json` so it names the layers you actually have.
6. Build:

```bash
scripts/build-city.sh <your-city>
scripts/serve.sh <your-city>
```

The output will be written to:

```text
public/cities/<your-city>/index.html
```

## Project Layout

```text
sevent4/                  Python package code
scripts/                  startup and build scripts
data/cities/              city configs and source/layer data
public/assets/            vendored MapLibre files
public/cities/            built city consoles
```

## Python Entry Points

The shell scripts call these package entry points:

```bash
sevent4-console
sevent4-gtfs-corridors
sevent4-ward-service-access
```

You can also run the builder directly:

```bash
python -m sevent4.build_city_console \
  --city data/cities/ahmedabad/city.yaml \
  --layers data/cities/ahmedabad/layers/layer_manifest.json \
  --out public/cities/ahmedabad/index.html
```

## Reading

- Constitution of India, Part IXA: The Municipalities, Articles 243P-243ZG:
  https://www.constitutionofindia.net/parts/part-ixa/
- Constitution of India, Article 243W: powers, authority, and responsibilities
  of municipalities:
  https://www.constitutionofindia.net/articles/article-243w-powers-authority-and-responsibilities-of-municipalities-etc/
- Constitution/74th Amendment summary and Twelfth Schedule functions:
  https://secforuts.mha.gov.in/74th-amendment-and-municipalities-in-india/
- NITI Aayog, `Moving Towards Effective City Government - A Framework for
  Million-Plus Cities`:
  https://niti.gov.in/whats-new/moving-towards-effective-city-government-framework-million-plus-cities
- RBI municipal finance report release:
  https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=59093
- Janaagraha, Annual Survey of India's City-Systems:
  https://www.janaagraha.org/asics/
