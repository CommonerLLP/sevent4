# Ahmedabad road contractors: how we find the names, map the roads, and test the BJP link

_Drafted 2026-06-10. Method note + defamation discipline. Companion to
`data/institutions/rent_capture/ahmedabad_roads.json` and
`the-double-extraction.md` (the "road-building as a rent" frame)._

This note answers three questions the project asked, in order:
1. **Where do the contractor names actually live?** (Solved.)
2. **Where are these roads, spatially?** (Solved — ward + zone join.)
3. **How do we responsibly establish a link to the BJP?** (Method + the
   defamation line. Not yet executed; needs MCA/ECI access + your go-ahead.)

---

## 1. The names are in the *resurfacing registers*, not the budget books

The 25-year budget corpus gives the **spend** (the ₹-by-head, by-year series —
see `roads/code_rows_raw.csv`), but it names **no firm**. The only contractor
string anywhere in the budget books is the *income* head
`23306 PENALTY RECOVERED FROM CONTRACTORS` (₹5–9 cr/yr). nProcure couldn't
yield names because the e-tender portal is JS-gated and award-PDFs sit behind
opaque IDs.

The names live in a different document AMC itself publishes: the **annual
"roads resurfaced" register** (the work-order list with contractor and
consultant columns). Three are already on disk in the twenty27 corpus
(`data/news/roads/resurfaced_2017-18.pdf`, `_2024-25.pdf`, `_2025-26.pdf`).

`scripts/recipes/ahmedabad/parse_resurfaced_registers.py` parses all three
into **852 road segments**, each with: zone, ward, road description
(from–to), length, width, defect-liability/completion date, **contractor**,
and **consultant**. Output in
`data/cities/ahmedabad/source/budget/roads/resurfaced_registers/`:
`roads_resurfaced_rows.csv`, `resurfacing_by_ward.geojson`,
`resurfacing_summary.json`.

**Encoding caveat (HITL):** 2017-18 and 2024-25 are legacy non-Unicode
Gujarati fonts; 2025-26 is Unicode with mangled conjuncts. Firm and ward
names are decoded via explicit dictionaries. The firm *transliterations*
(below) must be confirmed against MCA before any is published as fact.

To extend the series: AMC publishes these registers periodically; the missing
years (2018–2023, plus pre-2017) are the acquisition target — and are the
RTI ask if not online (see §4).

---

## 2. The fifteen firms, and the zonal carve-up (the spatial finding)

Across the three registers, road resurfacing is carried by a **small, stable
set of firms, and each effectively owns a zone**:

| Zone | Dominant firm (segments) | Repeats across years? |
|---|---|---|
| West | Apex Protech LLP (54) + L.G. Chaudhary (45) | Apex dominant **2024-25 and 2025-26** |
| North | Apex Protech LLP (46) | dominant **2024-25 and 2025-26** |
| North-West | Keystone Infrastructure (84) | Keystone 2025-26; Nar Narayan 2024-25 |
| Central | Maruti Construction (30) | Maruti **2024-25 and 2025-26** |
| East | Maruti / Vimal Construction | Maruti 2025-26; Vimal 2024-25 |
| South | Ashish Infracon (34) | Ashish 2017-18 |
| South-West | Vimal Construction (19) + Fortune Builders (16) | 2025-26 |
| Citywide "Road Project" dept | R.K.C. Infrabuild (16) | 2025-26 |

That a handful of firms split the city by zone, and the same firm tops the
same zone in consecutive years, **is** the repeat-contractor pattern the
"pothole economy" names — established here from AMC's own work-orders, not
from allegation. (This is a tier-A *pattern* claim about award distribution;
it is **not** a claim that any award was rigged — that stays §3/tier-B.)

**Where the road money lands, by ward** (segments, all three registers):
Naroda (63), Paldi (50), Gota (47), Sarkhej (38), Navrangpura (37),
Chandkheda (32), Ranip (31), Chandlodia (30), Bodakdev (29). Four wards show
**zero** mapped resurfacing in these registers (Saijpur Bogha, Viratnagar,
Maktampura, Amraiwadi) — worth checking against the deprivation layer: do the
peripheral/industrial east-side wards get less resurfacing money than the
west-side developed wards? `resurfacing_by_ward.geojson` carries per-ward,
per-year segment counts + km + top contractor for the MapLibre overlay.

**Firm totals (segments, all years, HITL-transliteration):** Apex Protech 100,
Keystone Infrastructure 100, Maruti Construction 56, L.G. Chaudhary 50,
Ashish Infracon 37, Vimal Construction 35, Fortune Builders 31, Nar Narayan
Infrastructure 25, R.K.C. Infrabuild 22, N.C.C. Infra 18, K.E.C.L. 8, plus
~30 rows of firms whose name-prefix still needs decoding.

---

## 3. The BJP link: method, and the line we do not cross

AMC first went to the **BJP in 1987** and the party has governed it
**continuously since 2005** (it won the April-2026 election 160/192; current
term to ~2031). [VERIFY-FLAG: do not publish "40 continuous years since 1987"
— the 1987–2005 continuity is unconfirmed in sourcing seen so far; confirm
against SEC Gujarat records first.] The **Standing Committee** — which approves
every tender award — is BJP-chaired.
So at the institutional level the link is simply true: a BJP standing
committee awards this work. That is a tier-A structural fact and needs no
firm-level allegation.

The firm-level link ("firm X is owned by / donates to / is a relative of BJP
person Y") is a **different, defamation-loaded claim**. We pursue it only
through documentary chains, and we hold the STATE_OF_BRAIN line: **every
named-individual political-connection claim is tier-B (attributed, with
denial), never asserted as fact; the documentable core is the mechanism.**

### The five evidentiary chains (in order of strength)

**A. MCA company master data → directors/shareholders.** Each "Pvt Ltd"/"LLP"
firm has a CIN; MCA's master data + the DIN registry give current and past
directors and shareholders. This is the spine. Cross-reference director names
and addresses against (i) BJP corporators/office-bearers, (ii) their declared
relatives. Source: MCA21 portal / signed company filings. **Tier A for "who
owns the firm"; the BJP overlap is tier B until a filing or affidavit ties
the same individual to the party.**

**B. Electoral-bond disclosure (ECI/SBI, March 2024).** The full purchaser↔
party bond ledger is public. Test directly: did any of these fifteen firms (or
their parent/sibling entities by CIN) buy electoral bonds, and to which party?
A bond purchase to the BJP by a firm holding AMC road contracts is the single
cleanest, least-deniable link available. **Tier A if the firm name matches the
disclosed purchaser list exactly.**

**C. AMC corporator interest/asset declarations + MyNeta affidavits.** Election
affidavits require candidates to declare business interests, directorships and
immovable assets. Search BJP corporators'/MLAs' affidavits for these firm
names or for construction-business declarations. We hold `bjp_mla_myneta.csv`
locally (state MLAs); the **AMC corporator** affidavits are the missing layer.
**Tier A for the declaration itself; the inference is tier B.**

**D. Standing Committee award records.** AMC standing-committee agendas/
resolutions record who proposed and approved each award, the L1 basis, and any
single-bid/repeat-L1 pattern. A documented pattern of one firm repeatedly
being sole/lowest bidder in one zone is tier-A evidence of *concentration*;
"cartel/rigging" remains tier-B/C unless an audit or court says otherwise.

**E. Named reporting + audit.** Gujarat Samachar, DeshGujarat, DNA, the
Local-Fund audit and the AMC blacklist already document the Hatkeshwar
contractor (Ajay Engineering) and two blacklisted Road-Project firms (Akash
Infra, GPC Infra). Use these as corroboration, cite the outlet, carry denials.

### What we do NOT do
- We do not assert "BJP contractor" of any firm on zonal dominance alone.
  Concentration is documented; *motive/collusion is not* until A–E prove it.
- We do not name a private individual as a BJP-linked beneficiary without a
  filing/affidavit/bond-record/court doc. Surnames matching is a **hypothesis
  to verify**, never a finding.
- Defamation-safe framing: "firm X, which holds AMC road contracts in [zone],
  is [per MCA] directed by [names]; [per ECI] purchased ₹Y in electoral bonds
  to [party]" — each clause sourced, no causal claim glued between them.

### Execution (blocked on access + your go-ahead)
Chains A–C need network access I don't have permission for yet (MCA, the ECI/
ADR bond dataset, MyNeta). Per the standing rule I won't WebSearch/WebFetch
without explicit OK. The local-only step I *can* run now is a hypothesis-grade
surname overlap between the firm strings and the BJP MLA list — but that is
tier-C noise, not evidence, and I'd label it as such.

**If you green-light web/MCA access, the first three pulls are:**
1. ECI electoral-bond purchaser list → exact-match the 15 firm names.
2. MCA master data → CIN + directors for each firm.
3. AMC standing-committee resolutions for the resurfacing awards (proposer/
   approver + bid count).

---

## 4. RTI fallback (if the records aren't online)

To AMC Road Project Department / each Zonal Engineer, under the RTI Act 2005:
> "For FY 2015-16 to 2025-26, for the Road Project department and each of the
> seven zones: a list of all road resurfacing / construction work orders,
> showing for each — work description and location (ward/TP), estimated cost,
> awarded cost, name of the awarded contractor, number of bids received, the
> L1 bidder, date of award, and the approving Standing Committee resolution
> number." Plus: "the list of contractors blacklisted/penalised for road work
> 2015–2026 with the reason and resolution number."

That single RTI, answered, collapses chains D and most of E into one
authoritative table.

---

## 5. Acquiring the missing register years (the current priority)

**What the three files actually are.** From their embedded titles, these are
AMC's **DLP (Defect Liability Period) Road** registers, published as website
uploads:
- `resurfaced_2024-25.pdf` → "Formate DPL Road 2024-25 Website.xlsx"
- `resurfaced_2025-26.pdf` → "DLP ROAD DETAILS WEBSITE UPLOAD - 2025-2026.xlsx"
- `resurfaced_2017-18.pdf` → PDFCreator/Ghostscript 2019 print (likely an
  earlier RTI/website artefact, different provenance).

This matters analytically: a **DLP register lists roads still inside their
defect-liability window and the contractor liable for them** — so it is the
single document that names the firm-on-the-hook for each stretch. That is a
sharper instrument than a generic "resurfaced" list.

**Years we have:** 2017-18, 2024-25, 2025-26.
**Gap to fill:** 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, and
anything pre-2017.

**Source + access reality.** These live on `ahmedabadcity.gov.in` under the
roads/DLP section. The site is a **JS-rendered SPA, not script-scrapable**
(confirmed during the budget pull); document URLs carry opaque CMS IDs not
derivable blind. The four gap *budget* books were ultimately obtained by
**manual/VPN download** from `ahmedabadcity.gov.in/SP/...`. The DLP registers
will need the same: a manual browser pull (or the live page's XHR/document-API
endpoint captured from the network tab), or an RTI for the gap years.

**Pipeline once files land.** Drop each new PDF into
`data/cities/ahmedabad/source/budget/roads/resurfaced_registers/` (and the raw
into the twenty27 corpus), add the year to the dump step + to the year list in
`parse_resurfaced_registers.py`. The parser already handles all three
encodings; new years extend the panel and the ward GeoJSON automatically. Each
added year sharpens the **repeat-contractor-by-zone** test: a firm topping the
same zone across 2018→2026 is the headline.

**Acquisition attempt (2026-06-10, web authorized):** the gap-year DLP files
are NOT reachable by search/fetch — `ahmedabadcity.gov.in` is a JS SPA whose
document listing isn't indexed and whose CMS IDs aren't guessable (the same
wall the budget books hit). Static `Uploads/...` PDFs that we already know the
URL of *do* fetch (the Standing Committee list and contractor-registration
list came down fine), but the DLP-road register listing for 2018–2023 cannot be
enumerated headlessly. **Still needs a manual/VPN browser pull** (capture the
live page's XHR/document-API call), then drop the files into
`resurfaced_registers/` — the parser handles the rest.

---

## 6. Linkage results (2026-06-10 — web/MCA/ECI authorized, executed)

Full structured output: `data/cities/ahmedabad/source/budget/roads/contractor_registry.json`.

**Identities confirmed (tier-A, from AMC's own contractor register + MCA):**
seven of the twelve firms now carry a verified legal name, registration class
and directors — Ashish Infracon (AA-1546, Patel Ashish Ashokbhai), Narnarayan
Infrastructure (AA-1548, Jagdishchandra C Patel), RKC Infrabuilt (AA-1550,
Parth K Shah), NCC Infraspace (AA-1552, Kantibhai Kalidas Patel), Apex Protech
LLP (AA-1610, Nirav Navnitbhai Patel), Vimal Construction (AA-1625, Rajankumar
M Kanani), L.G. Chaudhary (AA-1629, Laljibhai Godadbhai Chaudhary). Every
big-volume road firm is **AA-class** — AMC's top registration tier — and the
contractor base sits substantially in the **central-Gujarat Patel contractor
belt** (Kheda/Kapadwanj/Kathlal/Nadiad, Mehsana, Gandhinagar), not Ahmedabad
city. Both are tier-A who-profits data.

**The BJP test — honest result:**
- **Electoral bonds: NEGATIVE.** None of these municipal firms appears in the
  SC/SBI bond disclosure. (A "match" a search returned was *APCO Infratech*,
  Lucknow — a different company.) Bonds were a >₹1cr, big-national-firm
  instrument; city contractors are below that floor. The finding itself
  matters: **local-contractor→party money does not run through bonds** — it
  runs through channels bonds don't capture (local party funds, corporator/
  relative interests, cash).
- **Director → BJP office: not established.** No public source ties any named
  director to a BJP post. The directors are common Gujarati business-community
  surnames; resemblance is not evidence.
- **Structural link: tier-A and sufficient.** A **BJP Standing Committee**
  (2021–26 chair Hiteshbhai Kantilal Barot, since made Mayor; members listed in
  the registry JSON) approves every award, and AMC has been BJP-run continuously
  since 2005 (BJP first won it in 1987; 160/192 seats after April 2026).
  *That* is the defensible, documentable statement: a BJP body hands ~₹1,000
  cr/yr of road work to a stable, zone-partitioned set of AA-class central-
  Gujarat firms.

**What remains to test a firm-level link:** cross-reference the seven
confirmed directors against the **full AMC councillor roster + their
election-affidavit relative/business declarations**. That is the only route
that could turn the structural link into a named one — and until it produces a
documented tie, **no firm is labelled a "BJP contractor."**
