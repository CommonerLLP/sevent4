# The Unelected City

An atlas that maps an everyday Indian city problem — a broken road, a missing
library, a failed bus route, a flooded lane — to the public office actually
responsible for it. Indian city power is split across municipal corporations,
state departments, development authorities, parastatals, police and contractors
until no one is answerable; this makes the first accountability question easy to
ask: **whose jurisdiction is this, and why isn't it the city's?**
(The full frame: [why this atlas exists](docsx/governance-frame.md).)

## What's in it

- **14 city consoles** (`/cities/<city>/`) — ward, Assembly- and
  Parliamentary-constituency boundaries, transit, services, land-use and heat
  layers, with councillor / MLA / MP attribution where public data exists.
  Ahmedabad is the deepest seed (22 layers + a 22-year budget); also Bengaluru,
  Bhubaneswar, Chennai, Delhi, Hyderabad, Jaipur, Kanpur, Kochi, Kolkata,
  Lucknow, Mumbai, Pune, Visakhapatnam.
- **The reading layer** — the argument over the maps:
  `/why/` (explanatory chapters: the air, the roads…), `/findings/` (devolution
  scoreboard + the Ambedkar / Bombay city-state pieces), `/devolution/`, `/about/`.

No backend — HTML, map assets and processed GeoJSON are static files.

## Quick start

The built atlas is checked into `public/`, so a fresh clone serves immediately —
no build, no env:

```bash
git clone https://github.com/CommonerLLP/sevent4.git
cd sevent4
scripts/serve.sh           # static server on :9174 (PORT=8080 to change)
```

Open the first URL it prints (`…/index.html`). To smoke-test the checked-in
static bundle on mobile, tablet, and desktop viewports with the Playwright CLI:

```bash
.venv/bin/python -m sevent4.qa.browser_smoke
```

> Rebuilding a console (`scripts/start.sh` / `scripts/build-city.sh <city>`) needs
> the per-city source data under `data/`, which is **local-only** (gitignored) — so
> it's for maintainers who hold that data, not a fresh clone.

## Add a city

```bash
cp -r data/cities/ahmedabad data/cities/<city>     # then edit city.yaml
# replace layers/{wards,acs,pcs}.geojson + jurisdiction_crosswalk.json,
# edit layers/layer_manifest.json to match the layers you have, then:
scripts/build-city.sh <city> && scripts/serve.sh <city>
```

Each city lives under `data/cities/<city>/` with a `city.yaml`, a `layers/`
manifest, and a jurisdiction crosswalk (ward → AC → PC → district), which is
required — the console is a governance tool first, a map second. Full spec +
Python entry points: [city data contract](docsx/city-data-contract.md). To
rebuild the Ahmedabad seed: [data recipes](docsx/data-recipes.md).

## Layout

```text
sevent4/        Python package (console + layer builders)
scripts/        setup / build / serve
data/cities/    per-city configs + source & layer data   (local-only)
public/         the built static atlas (consoles + reading layer + assets)
```

## Docs

- [Why this atlas exists](docsx/governance-frame.md) — Part IXA, the
  fragmentation problem, finance, what the console shows
- [Architecture doctrine](docsx/architecture.md) — constitutional implementation
  frame, evidence contract, and source/adapter rules
- [System architecture](docsx/system-architecture-2026-06-22.md) — current
  ports/adapters boundaries, shared-infra rules, and browser smoke gate
- [City data contract](docsx/city-data-contract.md) — `city.yaml`, layer
  manifest, the jurisdiction crosswalk, add-a-city, entry points
- [Data recipes](docsx/data-recipes.md) — rebuilding the Ahmedabad seed
- [Reading](docsx/reading.md) — Constitution, NITI Aayog, RBI, Janaagraha

## License & attribution

- **Code** (recipes, console generator, page templates) — **AGPL-3.0** (see
  [`LICENSE`](LICENSE)).
- **Data** (geospatial, population, finance) — **third-party, redistributed under
  each source's own license** (OpenStreetMap/ODbL, WorldPop/CC-BY, DataMeet,
  OpenCity, Census of India, city/state governments). **Not** relicensed under
  AGPL; per-source credits and terms in [`ATTRIBUTION.md`](ATTRIBUTION.md).
