# Greater Chennai Corporation (GCC) — Corporation Data

City: Chennai, Tamil Nadu | Captured: 2026-06-09 | Agent: SevenT4 corporation-data

---

## COUNCIL STATUS (headline)

**The GCC council is SITTING.** Chennai ended a six-year administrator gap (2016–2022) with civic elections on **19 February 2022** (counting 22 Feb 2022). The council was constituted and the Mayor/Deputy Mayor elected on **4 March 2022**.

- **Last election:** 19 February 2022 (urban local body polls). First GCC council since the 2016 term lapsed; the city was run by a state-appointed Special Officer/administrator from 2016 until the 2022 polls.
- **Term:** 5 years (per GCC council rules), i.e. nominally running to ~2027. As of capture date the council is in office and active.
- **Mayor:** **R. Priya (Priya Rajan)**, DMK, Ward 74 (Mangalapuram) — 46th Mayor of Chennai; first Dalit woman mayor and youngest woman mayor of the city. Elected unopposed 4 Mar 2022.
- **Deputy Mayor:** **M. Magesh Kumaar**, Ward 169.
- **Composition (2022 result):** DMK 153; INC 13; CPI(M) 4; VCK 4; MDMK 2; CPI 1; IUML 1 (DMK-led Secular Progressive Alliance ≈ 178). Opposition: AIADMK 15; BJP 1; AMMK 1; Independents 5. Total 200 wards across 15 zones.
- **Verification note:** Election dates, party tallies and mayor identity corroborated by Wikipedia (2022 Tamil Nadu local elections; Priya Rajan), Citizen Matters, and the official GCC council site. The live GCC councillor directory (council-address page) independently confirms R. Priya as Mayor (Ward 74) and M. Magesh Kumaar as Deputy Mayor (Ward 169).

### Sources (council status)
- GCC Council (official): https://chennaicorporation.gov.in/gcc/council/about-council/
- GCC Councillors directory (official): https://chennaicorporation.gov.in/gcc/council/council-address/
- 2022 Tamil Nadu local elections — Wikipedia: https://en.wikipedia.org/wiki/2022_Tamil_Nadu_local_elections
- Priya Rajan — Wikipedia: https://en.wikipedia.org/wiki/Priya_Rajan
- Citizen Matters (winners + mayor): https://citizenmatters.in/chennai-local-body-poll-results-winning-councillors-dmk-mayor-38740

---

## Councillor roster — councillors.csv

Source: official GCC councillor directory (council-address page), scraped 2026-06-09. 200 ward rows.

- **194** wards with a named sitting councillor (incl. Mayor Ward 74, Deputy Mayor Ward 169).
- **4** wards marked "Vacant place" on the official roster: **59, 122, 146, 165**.
- **2** wards (**5, 189**) appear as blank cards on the official page (no name/contact published) — recorded as "Not listed on official roster".

Columns: `ward_no, councillor_name, party, role, phone, email`.
- `email` follows the official pattern `ward###@chennaicorporation.gov.in`.
- `party` is **left blank**: the official GCC directory does NOT publish party affiliation. Party-by-ward is available in the Citizen Matters 2022 winners list, but that page renders its table dynamically and was not machine-extractable in this pass — DO NOT fabricate. Aggregate party tallies are recorded above under Composition. To fill `party`, scrape the Citizen Matters table with a JS-capable fetcher or the TN State Election Commission ward results.

---

## Budget books — budget_index.json

Official GCC budget landing pages exist per year at `chennaicorporation.gov.in/gcc/Budget_YYYY-YYYY/` but return HTTP 404 to programmatic fetch (browser-only / bot block). **OpenCity Urban Data Portal** mirrors the official GCC budget PDFs with stable, directly-downloadable URLs.

- **Budget years indexed (OpenCity):** 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26, 2026-27, plus Climate Budget 2025-26.
- **2024-25** fully resolved to 14 direct PDF URLs (Budget Speech, Announcement, At-A-Glance, Dept-wise Receipts/Expenditure, North/Central/South division receipts & expenditure, Elementary Education, Action Taken Report 2023-24) — see `budget_index.json`.
- Official extras: Citizen's Guide to Budget 2025-26 PDF and Climate Budget 2025-26 PDF (direct on chennaicorporation.gov.in).

---

## Official facility lists — facilities/

Downloaded from OpenCity (org: Greater Chennai Corporation), which republishes official GCC/TN data. See `facilities/SOURCES.md` for per-file source URLs.

| Category | File | Records (approx, ex-header) |
|----------|------|------|
| Libraries | chennai_libraries.csv | 161 |
| Schools — Aided | chennai_schools_aided.csv | 354 |
| Schools — High | chennai_schools_high.csv | 41 |
| Schools — Higher Secondary | chennai_schools_hr_sec.csv | 18 |
| Health — UPHCs | chennai_health_uphc.csv | 159 |
| Health — UCHCs | chennai_health_uchc.csv | 18 |
| Burial grounds | chennai_burial_grounds.csv | 67 |
| Night shelters | chennai_night_shelters.csv | 45 |
| Public toilets (ward-wise, Jan 2019) | chennai_public_toilets_wardwise_2019.csv | 200 wards |

Not downloaded (KML map layers only on OpenCity): TB centres, maternity hospitals, VPHCs, ABC centres, all-school / GCC-school geometries.

---

## What's missing / caveats
- **Councillor party-by-ward** not in `councillors.csv` (official source omits party; CM table not machine-readable this pass). Aggregate tallies captured.
- Wards **5 and 189** have no councillor published on the official roster (blank cards); wards **59, 122, 146, 165** explicitly "Vacant".
- Official GCC budget pages block automated fetch; budget PDFs sourced via OpenCity mirror. Per-PDF direct links resolved for 2024-25 only; other years available via their OpenCity dataset pages (linked in `budget_index.json`).
- Regional-language: source pages are English; no Tamil-only fields captured. Facility CSVs are GCC-published English transliterations.
