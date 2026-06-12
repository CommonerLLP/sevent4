# Communicating the gap: how the site tells a citizen about misgovernance, and why the 74th Amendment is the key

This is the editorial spine of The Unelected City. Every data layer serves it; if a
layer doesn't, it's decoration.

## The one thing a visitor must leave understanding

> The Constitution promised your city would be run by people *you elect*, with real
> power over your water, roads, health, and money. That promise has been quietly
> broken — here is exactly how, and here is who holds the power instead.

The site is not "a map of city data." It is **the gap between what the 74th Amendment
promised and what your city actually is.** The Amendment is not background; it is the
**measuring stick** laid against every city and every ward.

## Why the 74th Amendment is *the* key — concretely, not rhetorically

The 74th Amendment (1992) and its **12th Schedule list 18 functions** — water supply,
public health, urban planning, roads, fire services, slum improvement, parks, and so
on — that were meant to be devolved to *elected* municipalities, backed by the three
F's: **Funds** (Art. 243Y, the State Finance Commission), **Functions**, and
**Functionaries**. The promise was elected local self-government with real control.

So the atlas's single analytical question, for every city, is: **of the functions the
Constitution assigned to your elected corporation, how many does it actually run — and
who took the rest?**

And the data already answers it. **`service_providers.json` IS that scorecard.**
Ahmedabad: water = corporation (devolved ✓), but electricity = Torrent (private),
metro = GMRC (state SPV), BRT = AJL (SPV), development/land = AUDA (state board),
police = state. Of the functions a resident relies on, the *elected* body controls
roughly a third. **That ratio — "how much of your city you actually get to vote on" —
is the headline number to put on every city.**

## The five gaps the site makes visible (each measured against the promise)

1. **Democratic gap** — *Do you even have an elected council?* (Bengaluru: none for 11
   years; Hyderabad, Jaipur: none now.) → the red banner.
2. **Power gap** — *the councillor you elect can't deliver; the IAS Commissioner +
   Standing Committee + state decide.* → the ward power-map popup.
3. **Devolution / fragmentation gap** — *who runs your water, bus, metro? Mostly not
   the corporation.* → the service-provider scorecard (12th-Schedule scoring).
4. **Money gap** — *the city funds the prestige metro, off your books, while the bus
   you ride and the library you lack are starved.* → the finance / opportunity-cost view.
5. **Capacity gap** — *the regulator meant to protect your air is 30–84% empty.* → the
   hollow-regulator layer.

Each ends on the same quiet line: **"The 74th Amendment said this would be different."**

## The user's journey (UX spine)

- **Land** → "Pick your city." The grid already flags the democratic gap (red = no
  elected council).
- **City** → a **devolution scorecard** up top: *"Your elected corporation controls X
  of the functions the Constitution assigned it"* + the council-status banner.
- **Click your ward** → the power map (elect-vs-decide) + your service reality (heat,
  library, bus per resident).
- **Follow the money** → the dream zone / metro vs the bus.
- The Amendment is the refrain throughout — shown, never lectured.

## What's needed to make every city tell this (scrape / parse / pull / analyse)

- **Devolution score** (analysis, *doable now*): `service_providers.json` × the 12th
  Schedule → "% of functions under the elected body" per city. This is the number that
  makes the Amendment legible in one glance.
- **Service deprivation per ward** (the lived gap): WorldPop per-capita + library
  geocoding + GTFS bus frequency + heat (heat done) → per-resident shortfall.
- **Money gap**: the 20-year municipal budget per city (Ahmedabad-style scrape).
- **CRMS** (department → complaint): your problem → which (often non-elected) body owns
  it (per-city complaint-portal scrape).
- **Capacity gap**: per-state SPCB vacancy/budget (state tables).
- **Water/groundwater**: CWC/CGWB + state utilities (gov portals currently network-blocked).

The connective tissue is the **devolution score** — it turns a pile of layers into a
single, constitutional indictment a citizen can read in five seconds.
