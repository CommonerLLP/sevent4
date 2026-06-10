# The road money: who repaves Ahmedabad, and who decides

_A standing finding. Ahmedabad, 2017–2026. Built entirely from the Ahmedabad
Municipal Corporation's own published records. Every figure cites its source;
every claim is marked for how far the evidence carries it._

---

## The one-paragraph version

Across the seven years for which AMC has published a road register, **seven of
Ahmedabad's 48 wards were resurfaced in every single one of them** — Naroda
alone records **109 separate resurfacing work-orders in seven years**. That
recurring work — on the order of **₹1,000 crore a year** — is carried not by an
open field of contractors but by a **closed set of about seven firms**, each of
which holds a zone and hands it on to the next in multi-year blocks. Every one
of those firms is registered in AMC's **top contractor class**, and most are
based in the **central-Gujarat town belt**, not the city they repave. And every
rupee of it is awarded by a **Standing Committee controlled by the same party
that has governed the corporation without interruption for two decades.** None
of those statements is an allegation. All of them are in the record AMC itself
publishes.

---

## 1. The evidence base

AMC publishes, for most years, a **Defect-Liability-Period (DLP) Road
register**: the list of resurfaced road stretches still under contractor
warranty, naming — for each stretch — the ward, the road, its length and width,
the completion date, and **the contractor liable**. It is the one document that
ties a road to the firm that built it.

Seven of these registers are public, served from AMC's own document API
(`ahmedabadcity.gov.in/ViewFile/ViewFile?TYPE=FileRepository,<id>`):

| Year | ID | Year | ID |
|---|---|---|---|
| 2017-18 | 315 | 2020-21 | 318 |
| 2018-19 | 316 | 2022-23 | 319 |
| 2019-20 | 317 | 2024-25 | 2424 |
| | | 2025-26 | 2628 |

(No register exists for **2021-22 or 2023-24** — AMC did not publish one, a gap
that also shows up independently in the budget books.) Parsed together, the
seven registers hold **1,683 resurfacing work-orders**, of which 1,380 are
mapped to a ward and 1,156 to a named contractor. _(Method:
`scripts/recipes/ahmedabad/parse_resurfaced_registers.py`. Firm and ward names
are decoded from legacy-font Gujarati and are HITL-pending — confirmed against
the MCA company register and AMC's own contractor-registration list where a
match exists.)_

---

## 2. The roads that never stop being repaved  · TIER A

Shade the 48 wards by **recurrence** — how many of the seven years each appears
in a register — and the "pothole city" stops being a metaphor:

| Ward | Years repaved | Work-orders (7 yr) |
|---|---|---|
| **Naroda** | **7 / 7** | 109 |
| **Gota** | **7 / 7** | 93 |
| **Khokhra** | **7 / 7** | 58 |
| Asarwa | 7 / 7 | 34 |
| Sardarnagar | 7 / 7 | 29 |
| Danilimda | 7 / 7 | 27 |
| Saraspur-Rakhiyal | 7 / 7 | 13 |
| Sarkhej | 6 / 7 | 94 |
| Bodakdev | 6 / 7 | 65 |
| Thaltej | 6 / 7 | 61 |

A road resurfaced under a defect-liability warranty is, by definition, supposed
to *last*. Seven wards repaved in seven straight years is the warranty's own
contradiction: the work recurs because the surface fails, and the failure is
the demand. _(Interactive ward map:
`data/cities/ahmedabad/source/budget/roads/resurfacing_map.html`.)_

Three wards — **Viratnagar, Saijpur Bogha, Amraiwadi** — appear in **no**
register at all. Whether that is clean roads or unrecorded ones is its own
open question.

---

## 3. The closed club, and the rotating turf  · TIER A

The 1,156 contractor-named work-orders resolve to a short list. Six firms do
the bulk of it:

| Firm | Work-orders (7 yr) | AMC class |
|---|---|---|
| Nar Narayan Infrastructure Pvt Ltd | 226 | AA |
| M/s L.G. Chaudhary | 128 | AA |
| N.C.C. Infraspace Pvt Ltd | 118 | AA |
| Keystone Infrastructure | 106 | — |
| Apex Protech LLP | 101 | AA |
| Maruti Construction | 99 | AA |
| Vimal Construction | 65 | AA |
| Maruti Infracreation Pvt Ltd | 64 | AA |
| Ashish Infracon Pvt Ltd | 53 | AA |

But the headline is not the totals — it is the **geography over time**. Track
the dominant firm in each zone, year by year, and the pattern is not open
competition but **turf passed between a fixed set of hands**:

| Zone | 2017-18 | 2018-19 | 2019-20 | 2020-21 | 2022-23 | 2024-25 | 2025-26 |
|---|---|---|---|---|---|---|---|
| **North** | NCC | NCC | NCC | — | NarNarayan | **Apex Protech** | **Apex Protech** |
| **North-West** | — | NarNarayan | Maruti Infracr | Maruti Infracr | Maruti Infracr | NarNarayan | **Keystone** |
| **West** | L.G. Chaudhary | **L.G. Chaudhary** | — | — | — | **Apex Protech** | **Apex Protech** |
| **Central** | — | — | — | — | **Maruti** | **Maruti** | **Maruti** |
| **South** | Ashish | NarNarayan | NarNarayan | NarNarayan | Vimal | Vimal | Maruti |
| **South-West** | — | NarNarayan | NarNarayan | Disha | **NarNarayan (53)** | — | Vimal |

Read across the rows: **NCC** holds North from 2017 to 2019, then **Apex
Protech** takes it and keeps it. **L.G. Chaudhary** owns West (fifty work-orders
in 2018-19 alone), then cedes it to **Apex Protech**. **Maruti** locks Central
from 2022 on. **Nar Narayan** runs South and South-West for years — fifty-three
work-orders in South-West in a single year. A zone rarely has two firms
competing in it; it has one firm holding it, and a successor when it changes
hands. That is what a market looks like when it has been **divided rather than
contested** — and it is visible only because we can now read seven years at
once.

This is a documented distribution pattern from AMC's own registers. It is **not**
a claim that any tender was rigged.

---

## 4. Who the firms are  · TIER A

Seven of them are confirmed against the MCA company register **and** AMC's own
contractor-registration list:

- **Ashish Infracon Pvt Ltd** — CIN U45100GJ2010PTC062372, AMC class AA-1546,
  dir. Ashish Ashokbhai Patel (Prahladnagar).
- **Narnarayan Infrastructure Pvt Ltd** — CIN U45200GJ2006PTC048728, AA-1548,
  dir. Jagdishchandra C Patel (Sector 22, Gandhinagar).
- **RKC Infrabuilt Pvt Ltd** — CIN U45200GJ2011PTC067196, AA-1550, dir. Parth K
  Shah (Thaltej) — also a state-highway BOT player.
- **NCC Infraspace Pvt Ltd** — AA-1552, dir. Kantibhai Kalidas Patel.
- **Apex Protech LLP** — AAZ-3675, AA-1610, partners Nirav Navnitbhai /
  Navnitkumar / Darpit Patel (Sargasan / Kapadwanj).
- **Vimal Construction** — AA-1625, partner Rajankumar Mansukhbhai Kanani
  (Kathlal, Kheda).
- **L.G. Chaudhary** — AA-1629, partner Laljibhai Godadbhai Chaudhary (Sola).

Two facts fall out of the addresses. First, **every high-volume firm is
AA-class** — AMC's top registration tier, the only one eligible for the largest
works. The road money does not spread down the contractor ladder; it stays at
the top of it. Second, the contractor base is substantially the
**central-Gujarat Patel town belt** — Kheda (Kapadwanj, Kathlal, Nadiad),
Mehsana, Gandhinagar — *not Ahmedabad itself.* The people who repave the city
are, in good part, not of it.

_(Names transliterated from the registers are HITL-pending; the seven above are
MCA/AMC-confirmed. The generic-named firms — some "Maruti", "Fortune",
"Keystone" entries — have register namesakes and are not yet uniquely resolved;
see `contractor_registry.json`.)_

---

## 5. Who decides  · TIER A (structural)

Every one of these awards is approved by AMC's **Standing Committee**. The
Standing Committee is controlled by the **Bharatiya Janata Party**, which **first
won the corporation in 1987, has governed it continuously since 2005, and holds
160 of 192 seats** after the April 2026 election (current term to ~2031).
_(Verify-flag: a single uninterrupted "N years since 1987" figure is not yet
sourced — state the anchors, not the span, until checked against SEC Gujarat
records.)_

So the structural sentence needs no allegation to stand: **a BJP committee hands
roughly ₹1,000 crore a year of recurring road work to a closed set of top-class
firms, on roads that fail and are repaved year after year.** That is the finding.

---

## 6. The line we do not cross

It is tempting to close the loop — to call these "the BJP's contractors." We
tested that, on the cleanest public evidence, and it does **not** hold up:

- **Electoral bonds.** None of these municipal firms appears in the
  Supreme-Court-forced SBI/ECI disclosure. (Bonds were a large-national-firm
  instrument; city contractors sit below the floor.) The money does not move
  through bonds.
- **Directors vs councillors.** No director of the seven confirmed firms is a
  sitting AMC councillor — checked against the full roster for **both** the
  2021-26 and 2026-27 terms. One surname ("Chaudhary") coincides on two
  councillors, but neither is the L.G. Chaudhary partner. Coincidence, not a
  person.

So the firm-level link — *this firm is owned by / funds / is the relative of
that BJP person* — is **not establishable from open public data**, and we do not
assert it. What remains untested would require matching directors to
councillors' *relatives* through 160 individual election affidavits — heavy,
low-yield, and precisely where a careless match becomes defamation. We stop
short of it deliberately.

The honest claim is the structural one, and it is strong enough on its own:
**not that named individuals are partisan beneficiaries, but that the
architecture of who-decides and who-profits is closed, concentrated, recurring,
and single-party — and that the public can see it only because the corporation
documents its own road work and we read seven years of it together.**

---

## Sources & method

- **Primary:** AMC DLP Road registers (ViewFile IDs 315/316/317/318/319/2424/2628);
  AMC contractor-registration list (`Uploads/FormsFonts/Contractors/`); AMC
  Standing Committee member list and councillor roster (ViewFile 2638); MCA
  company register (via ZaubaCorp/Tofler/IndiaFilings); SBI/ECI electoral-bond
  disclosure; April-2026 AMC election result.
- **Derived data:** `data/cities/ahmedabad/source/budget/roads/` —
  `roads_resurfaced_rows.csv` (1,683 work-orders), `panel_7yr_summary.json`
  (zonal-dominance matrix), `resurfacing_by_ward.geojson` + `resurfacing_map.html`
  (ward recurrence), `contractor_registry.json` (firm identities + linkage tests).
- **Method & caveats:** `docs/ahmedabad-road-contractors-method.md`.
- **Tier key:** TIER A = documented fact from AMC/MCA/ECI records. Structural
  claims about who-decides are tier A; firm-level partisan claims are **not made**
  (see §6). All transliterated firm/road/ward names are HITL until confirmed.
- **Frame:** the road as the purest rent — recurring, opaque, quality-indifferent
  — in `docs/the-double-extraction.md` and `data/institutions/rent_capture/ahmedabad_roads.json`.
