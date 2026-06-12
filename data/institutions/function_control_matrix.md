# The control matrix: the 18 constitutional functions × 6 cities — who actually controls each?

This is the atlas in one grid. The **Twelfth Schedule** (Article 243W) lists the **18 functions** the
Constitution envisions for *elected* municipalities. For each, in each city, who actually controls it?

**Legend:** **City** = the elected municipal corporation (in-house) · **State** = a state board /
development authority / state department · **Centre** = a central body or centrally-designed scheme ·
**Mixed** = split (e.g. the corporation issues building permits *within* a state authority's master plan;
street-lighting is the city's but the bus service is the state's).

> Caveat: cells are coded from `service_providers.json`, the `fragmentation/` dossiers and the enabling
> statutes in `data/laws/`. The clearly-carved functions (water, planning, slums, fire) are firm; the
> **Mixed** cells (2, 8, 13, 17) are genuine judgment calls and flagged below.

| # | 12th-Schedule function | Ahmedabad | Mumbai | Kolkata | Chennai | Bengaluru | Hyderabad |
|---|---|---|---|---|---|---|---|
| 1 | Urban planning / town planning | **State** | State | State | State | State | State |
| 2 | Land-use & building regulation | Mixed | Mixed | Mixed | Mixed | Mixed | Mixed |
| 3 | Economic & social development planning | **State** | State | State | State | State | State |
| 4 | Roads & bridges (local) | **City** | City | City | City | City | City |
| 5 | **Water supply** | **City** | **City** | **City** | **State** | **State** | **State** |
| 6 | Public health, sanitation, conservancy, SWM | **City** | City | City | City | City | City |
| 7 | **Fire services** | **City** | **City** | **State** | **State** | **State** | **State** |
| 8 | Urban forestry / environment | Mixed | Mixed | Mixed | Mixed | Mixed | Mixed |
| 9 | Safeguarding weaker sections | **State** | State | State | State | State | State |
| 10 | Slum improvement & upgradation | **State** | State | State | State | State | State |
| 11 | Urban poverty alleviation | **Centre** | Centre | Centre | Centre | Centre | Centre |
| 12 | Parks, gardens, playgrounds | **City** | City | City | City | City | City |
| 13 | Cultural, educational, aesthetic | Mixed | Mixed | Mixed | Mixed | Mixed | Mixed |
| 14 | Burials & cremations | **City** | City | City | City | City | City |
| 15 | Cattle pounds; cruelty to animals | **City** | City | City | City | City | City |
| 16 | Vital statistics (births & deaths) | **City** | City | City | City | City | City |
| 17 | Public amenities (lighting, parking, **bus stops**) | Mixed | Mixed | Mixed | Mixed | Mixed | Mixed |
| 18 | Slaughterhouses & tanneries | **City** | City | City | City | City | City |

## The tally — how much of the constitutional mandate the elected city actually holds

| City | **Fully City** | Mixed | State | Centre | *Not the elected city (State+Centre)* |
|---|---|---|---|---|---|
| **Ahmedabad** | **9 / 18** | 4 | 4 | 1 | 5 |
| **Mumbai** | **9 / 18** | 4 | 4 | 1 | 5 |
| **Kolkata** | **8 / 18** | 4 | 5 | 1 | 6 |
| **Chennai** | **7 / 18** | 4 | 6 | 1 | 7 |
| **Bengaluru** | **7 / 18** | 4 | 6 | 1 | 7 |
| **Hyderabad** | **7 / 18** | 4 | 6 | 1 | 7 |

(The split is set by two functions: **water** — City in Ahmedabad/Mumbai/Kolkata, State in Chennai/Bengaluru/Hyderabad — and **fire** — City only in Ahmedabad/Mumbai. Everything else is uniform across the six.)

## What the matrix shows

1. **No elected city controls even half of its own constitutional mandate.** The best (Ahmedabad, Mumbai)
   fully run **9 of 18**; the carve-out cities (Chennai, Bengaluru, Hyderabad) run **7 of 18**. The
   Twelfth Schedule names eighteen functions for the people you elect; they get seven to nine.

2. **The split is by *value*, not by accident.** What stays with the elected city is the **labour-heavy,
   low-rent** half — roads, sanitation, parks, burials, cattle pounds, birth-and-death registration,
   slaughterhouses. What is taken is the **capital-and-rent-rich** half — **urban planning, land-use,
   water, slum redevelopment, poverty programmes, and public transport.** The city keeps the broom; the
   state keeps the pipes, the land and the plan. This is the scorecard's finding, mapped onto the
   Constitution's own list.

3. **The "Mixed" cells hide a further state tilt.** In land-use (2) the *master plan* is the state
   authority's and the city only issues permits within it; in public amenities (17) the lighting is the
   city's but the *bus service* is a state transport corporation; in environment (8) the city does some
   greening but *regulation* is the state pollution board's. Read strictly, the elected city's real grip is
   even thinner than the tally suggests.

4. **It compounds the fiscal point.** The city that controls 7–9 of 18 functions also has **no
   constitutional power to tax** (no Seventh-Schedule entry; Art. 243X's "may authorise"). Few functions
   *and* no own revenue: the municipality is administratively partial and fiscally dependent by design.

---
*Coding sources: `data/institutions/service_providers.json`, `data/institutions/fragmentation/*.json`,
`data/laws/` (enabling statutes), and `data/laws/_constitution/twelfth-schedule.txt` (the verbatim 18
functions). Companion: `the-political-economy-of-the-unelected-city.md`. This grid is the natural candidate
for the site's central visual.*
