# Kochi Municipal Corporation (Cochin Corporation) — Corporation Data

**City:** Kochi, Kerala (Ernakulam district) · **LB code:** 169 · **Body type:** Municipal Corporation
**Compiled:** June 2026 · **Role in atlas:** Kerala = DEVOLUTION CONTROL GROUP

---

## COUNCIL STATUS (headline)

**An elected council is sitting right now, freshly mandated.** Kerala held its
local-self-government elections **on time** in December 2025 (Kochi polled
9 Dec 2025; results 13 Dec 2025; council/mayor sworn in 26 Dec 2025), seamlessly
succeeding the 2020-2025 council whose term completed normally.

- **Current Mayor (2025-2030):** **V. K. Minimol (INC)**, councillor from
  Palarivattom division. Elected 26 Dec 2025 with 48 votes vs 22 for LDF's
  Jagathambika Sudarshan (CPI(M)).
- **Council composition (76 divisions):** UDF ~48 · LDF ~20 · BJP ~6 ·
  Independent ~2. **UDF holds the majority** — a flip from the 2020-2025 LDF-led
  council. (UDF's 48 includes Congress rebel Bastin Babu, who won Chullickal as
  an independent.)
- **Deputy Mayor:** disputed/transitional. News reporting (Onmanorama, 23-26 Dec
  2025) states UDF agreed a **one-year Deputy Mayor term for IUML nominee
  T. K. Ashraf**; Wikipedia lists **Deepak Joy (INC)**. Captured both —
  **needs verification** once the corporation publishes the official order.
- **Previous Mayor (2020-2025):** **M. Anilkumar (LDF / CPI(M))**, full term.
- **Delimitation:** divisions increased **74 → 76** ahead of the 2025 polls.

### DEVOLUTION CONTRAST (why this matters for the atlas)
Unlike **Bengaluru** (BBMP — no elected council since Sept 2020, governed by
administrators/commissioners for years) or **Mumbai** (BMC — elected body
dissolved March 2022, run by an administrator since), **Kochi's elected council
is continuous and uninterrupted.** Kerala has held LSG elections on schedule
every five years (2010, 2015, 2020, 2025), so there is no "administrator gap" —
the elected body, the mayor, and the standing-committee structure have a live
democratic mandate at all times. This is the core of the Kerala control-group
case: devolution backed by *electoral regularity*, not just statutory design.

---

## Files in this directory
- `councillors.csv` — **2020-2025 roster, full 74-division authoritative list**
  from Kerala LSGD (lsgkerala.gov.in/en/lbelection/electdmemberdet/2020/169):
  ward no, name, party, reservation.
- `councillors_2025.csv` — **2025-2030 winners (75 captured)** from IndiaTV's
  ward-wise results. NOTE: ward numbering in this source follows the news outlet
  and **differs from official LSGD division numbering**; one row name blank
  (Ravipuram independent) and Chullickal=Bastin Babu reconciled from mayor-vote
  reporting. The LSGD 2025/169 elected-member page was JS-rendered and did not
  yield rows on fetch — **2025 roster needs cross-check against LSGD once it
  populates.**
- `budget_index.json` — budget pages FY2019-20 → FY2024-25 + financial-statement
  (AFS) PDFs FY2020-21 → FY2023-24, from the official corporation portal.
- `facilities/SOURCES.md` — health/library/school source index.

## Sources (authoritative)
- Kerala LSGD elected-member DB (LB 169): https://lsgkerala.gov.in/en/lbelection/electdmemberdet/2020/169
- Kerala LSGD 2025 (LB 169): https://lsgkerala.gov.in/en/lbelection/electdmemberdet/2025/169 (JS-rendered, empty on fetch)
- Cochin Corporation portal: https://kochicorporation.lsgkerala.gov.in/en
- Budget index: https://kochicorporation.lsgkerala.gov.in/en/budget
- Financial statements: https://kochicorporation.lsgkerala.gov.in/en/financial-statement

## Sources (news, for council status / 2025 results)
- Onmanorama, "VK Minimol elected Kochi Mayor" (26 Dec 2025): https://www.onmanorama.com/news/kerala/2025/12/26/udf-councillor-vk-minimol-new-kochi-mayor.html
- Onmanorama, UDF announces Minimol; Deputy Mayor / IUML Ashraf (23 Dec 2025): https://www.onmanorama.com/news/kerala/2025/12/23/kochi-new-mayor-vik-minimol-say-dcc-sources.html
- IndiaTV, Kochi 2025 ward-wise winners: https://www.indiatvnews.com/news/india/kochi-municipal-corporation-election-results-full-list-of-ward-wise-winners-leading-candidates-parties-2025-12-13-1021555
- Wikipedia, Kochi Municipal Corporation: https://en.wikipedia.org/wiki/Kochi_Municipal_Corporation

## Integrity notes
- All URLs are real and were fetched/searched in this pass. No fabricated rows.
- 2020 roster is from the authoritative LSGD DB; 2025 roster is from a reputable
  news outlet pending LSGD reconciliation (numbering + 1 missing name flagged).
- Deputy Mayor conflict between sources is preserved, not resolved.
- Malayalam-origin names transliterated as published in English sources.
