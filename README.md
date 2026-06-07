# SevenT4

Indian city government is built so that responsibility is hard to see.

The Seventy-fourth Amendment brought municipalities into the Constitution as
urban local self-government. The Twelfth Schedule names the work cities should be
able to govern: planning, land use, roads, water, sanitation, public health, fire
services, slum improvement, urban poverty, parks, public amenities, street
lights, bus stops, and more.

But the city people actually live in is usually split across municipal
corporations, state departments, development authorities, parastatals, police,
transport agencies, utilities, contractors, engineers, ward councillors, MLAs,
and MPs. When a road breaks, a ward has no library, a bus route fails, a heat
pocket grows, a street floods again, or a public toilet disappears,
responsibility gets scattered until nobody is answerable.

SevenT4 does one small thing: it helps internet-literate residents map a city
problem to the public geography and public office around it.

It puts ward, Assembly constituency, Parliamentary constituency, transit, public
service, land-use, heat, and civic gap layers in one city console. A resident can
select a ward, AC, or PC and connect a road, drainage, heat, transport, library,
school, health, sanitation, or public-space issue to the ward councillor, MLA,
MP, and relevant public office where the data is available.

This is not a smart-city dashboard and it does not decide legal liability. It
makes the first accountability question easier to ask: whose jurisdiction is
this, and why is this power not with the urban local body?

Ahmedabad is the first working example. Fork the repo, replace the city data,
and build the same console for Kolkata, Chennai, Bengaluru, Hyderabad, Pune,
Mumbai, Delhi, Surat, Jaipur, Lucknow, or any other urban local body.

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

SevenT4 ships processed Ahmedabad layers so the console can run immediately.
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
- search, layer toggles, light/dark mode, and ward/AC/PC focus filters

The filters matter. A resident should be able to select a ward, AC, or PC and
see the city layers in relation to that public geography. As city datasets
improve, the same pattern can attach engineers, departments, zones, contractors,
budgets, public works, and grievance channels.

## Governance Frame

SevenT4 starts from a narrow claim: public data should help residents attribute
ordinary civic problems to public jurisdiction.

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
```

`city.yaml` tells SevenT4 where the city is and where its data lives:

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
- service points: schools, health facilities, libraries, toilets, transit stops,
  and other city-specific public infrastructure

Ward councillor data should be joined into `wards.geojson` when a public ward
roster is available. MLA and MP attribution should be joined into `acs.geojson`
and `pcs.geojson` when public representative data is available.

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

- Constitution/74th Amendment summary and Twelfth Schedule functions:
  https://secforuts.mha.gov.in/74th-amendment-and-municipalities-in-india/
- NITI Aayog, `Moving Towards Effective City Government - A Framework for
  Million-Plus Cities`:
  https://niti.gov.in/whats-new/moving-towards-effective-city-government-framework-million-plus-cities
- RBI municipal finance report release:
  https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=59093
- Janaagraha, Annual Survey of India's City-Systems:
  https://www.janaagraha.org/asics/
