# Source Policy And City Readiness

Status: binding working policy for SevenT4.

This note separates three things that were previously collapsed into one
"ready" label:

- whether a city console is selectable;
- whether a data source can carry a public finding;
- whether a city has strong finance, governance, and walkability
  evidence.

## Source Hierarchy

| Source class | Use for findings? | Use for context? | Rule |
|---|---:|---:|---|
| Official municipal, State, Union, court, CAG, RBI, FC, SFC, census, GTFS, or statutory source | yes | yes | Preferred source of record. Preserve URL/path, retrieval date, and parser. |
| OpenCity mirror of official/public records | yes, if publisher and resource are recorded | yes | Cite publisher -> OpenCity -> SevenT4 processed. Check licence/resource type before reuse. |
| OpenStreetMap | limited | yes | Use as open fallback geometry/context. Do not treat missing OSM features as proof of missing real-world services. |
| Google Maps / Google Places / Google Geocoding | no, for stored analytical layers | limited manual verification | Do not scrape, bulk download, cache, or derive SevenT4 datasets from Google Maps content. Store durable `place_id` only where permitted. |
| Satellite / remote sensing | modelled evidence | yes | Useful for heat, built-up, water, and access modelling; must carry resolution, date, and method. |
| Field survey / RTI / manual audit | yes, if documented | yes | Record collector, date, method, and uncertainty. |

## OSM Rule

OpenStreetMap is open data under ODbL. It can be copied, adapted, and used with
attribution and share-alike obligations. That makes it useful for a public atlas.

But OSM completeness is not uniform. For SevenT4, OSM can support:

- road, rail, metro, and rough routing context;
- first-pass public-service point context;
- open fallback geometry when official layers are absent;
- "mapped in OSM" claims.

OSM cannot by itself support:

- "this ward has no school/library/toilet/clinic";
- deprivation rankings;
- authoritative land-use control;
- proof that a service is absent.

Source: https://www.openstreetmap.org/copyright

## Google Maps Rule

Google Maps may be useful for visual/manual verification, but it is not an open
dataset for SevenT4.

SevenT4 should not use Google Maps content to create stored analytical layers,
bulk geocode city assets, scrape POIs, trace roads/buildings/sidewalks, build
tree or service inventories, or publish derived walkability datasets. The
noncommercial character of a project does not remove those restrictions.

Permitted narrow uses:

- inspect a source-published Google Maps embed or shortlink to verify a point;
- store a Google `place_id` where the relevant Google policy permits indefinite
  storage;
- display Google content only under Google Maps Platform rules and attribution,
  if a future UI intentionally uses Google Maps.

Do not mix Google-derived content into OSM or official SevenT4 layers.

Sources:

- Google Maps Platform Terms: https://cloud.google.com/maps-platform/terms
- Geocoding API policies: https://developers.google.com/maps/documentation/geocoding/policies
- Places API policies: https://developers.google.com/maps/documentation/places/web-service/policies

## Readiness Grades

The code-facing grades live in `sevent4/build_city_console.py` as
`CITY_READINESS`. `READY_CITIES` is derived from `console_grade == "full"`.

| Grade | Meaning |
|---|---|
| `console_grade` | Whether the city is selectable in the atlas UI. |
| `finance_grade` | Whether municipal finance evidence is strong, partial, research-only, missing, or a special case. |
| `walkability_grade` | Whether walkability/access analysis is routable, approximate, or not ready. |
| `governance_grade` | Whether public power/responsibility evidence is strong, partial, weak, or special case. |
| `source_confidence` | Whether major layers are official, mixed official, OSM fallback, or unverified. |

Current selectable cities:

| City | Console | Finance | Walkability | Governance | Source confidence |
|---|---|---|---|---|---|
| Ahmedabad | full | strong | routable | strong | mixed_official |
| Bengaluru | full | partial | approximate | partial | mixed_official |
| Chennai | full | partial | approximate | partial | mixed_official |
| Delhi | full | special_case_partial | approximate | special_case | mixed_official |
| Kolkata | full | research_only | approximate | partial | mixed_official |

## Finance Rule

Only Ahmedabad is currently marked `strong` for finance.

The other selectable cities need more work before they can carry the same kind
of municipal finance claim:

- Bengaluru: BBMP work orders and finance material exist, but finance is still
  partial.
- Chennai: zone finance and GCC material exist, but report/account confidence
  needs audit.
- Delhi: rich but special; GNCTD, MCD, NDMC, DCB, and Union routes must be kept
  separate.
- Kolkata: strong SFC/State surface, but municipal budget parsing is not yet
  strong enough for the top finance grade.

## Walkability Rule

Walkability needs more than a map. A rigorous city walkability layer needs:

- facility source of record;
- pedestrian/road graph source and date;
- transit stops/routes where relevant;
- known sidewalk/crossing/obstruction limits;
- confidence label for each feature and derived score.

Google Maps can help with manual checks. It cannot become the stored pedestrian
network or POI source. OSM can be the open routing fallback, but absence in OSM
must be labelled as missing mapping, not missing service.
