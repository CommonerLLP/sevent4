# Kolkata Municipal Corporation (KMC) — Corporation Data

Compiled 2026-06-09 for the SevenT4 atlas. Authoritative sources only (kmcgov.in,
West Bengal State Election Commission, Wikipedia where it transcribes the SEC result).
No OSM. Honest notes on every gated / 404 / unverified item.

---

## COUNCIL STATUS (HEADLINE)

- **Body:** Kolkata Municipal Corporation — **144 wards**, grouped into **16 boroughs**.
  Councillors directly elected; council term is **5 years**.
- **Last election:** **19 December 2021** (results declared 21 December 2021).
- **Result:** **AITC / Trinamool Congress swept 134 of 144 wards.** Others:
  BJP 3, INC 2, Left Front 2 (CPI(M) 1, CPI 1), Independents 3.
- **Council currently sitting:** YES — the council elected in Dec 2021 is in its term
  (5-yr term runs to ~Dec 2026; no fresh KMC general election has been held since).
- **Mayor — MAJOR CHANGE (June 2026):**
  - **Firhad Hakim** (AITC, Ward 82 Chetla) was elected Mayor on **28 Dec 2021** for a
    second term and served until **early June 2026**.
  - **Firhad Hakim RESIGNED as Mayor on 3–5 June 2026**, amid a reported TMC split /
    intra-party revolt following the May 2026 state-election outcome. Multiple national
    outlets (India TV, Republic, NewsX, India News Network) confirm the resignation,
    accepted with CM Mamata Banerjee's approval.
  - **No permanent successor confirmed as of 9 June 2026.** A KMC Board / Mamata-called
    meeting was underway (per Aaj Tak Bangla / India.com, 8 June 2026); names floated
    include former mayor Sovan Chatterjee (note: under current KMC rules any city resident
    can be mayor but must become a councillor within 6 months). **Treat the mayoralty as
    VACANT / in transition pending official KMC confirmation.**
  - Whether Hakim has also vacated his Ward-82 councillor seat is **unconfirmed** — captured
    as a flag in `councillors.csv`.
- **Other named office-bearers (from the Dec-2021 council, pending re-confirmation post-Hakim):**
  - **Deputy Mayor:** Atin Ghosh (Ward 11).
  - **Chairperson, KMC:** Mala Roy (Ward 88; also MP, Kolkata Dakshin).
  - **Mayor-in-Council members include:** Debasish Kumar (W85), Tarak Singh (W118),
    among others.

### Council-status sources
- 2021 KMC election — Wikipedia (transcribes WB SEC result):
  https://en.wikipedia.org/wiki/2021_Kolkata_Municipal_Corporation_election
- KMC official Mayors page (lists Firhad Hakim, elected 28/12/2021):
  https://www.kmcgov.in/KMCPortal/jsp/MayorsKolkata.jsp
- Firhad Hakim resignation (3–5 Jun 2026):
  https://www.indiatvnews.com/west-bengal/news-firhad-hakim-resigns-as-kolkata-mayor-after-mamata-banerjee-s-approval-amid-tmc-split-reactions-latest-updates-2026-06-03-1043517 ;
  https://www.republicworld.com/india/kolkata-municipal-corporation-mayor-firhad-hakim-resigns-from-his-post-2026-06-03-126824 ;
  https://www.indianewsnetwork.com/en/firhad-hakim-resigns-kolkata-mayor-amid-political-unrest-20260604
- Succession meeting (8 Jun 2026):
  https://bangla.aajtak.in/kolkata/story/who-will-be-next-kolkata-mayor-after-firhad-hakim-resignation-arg-1404492-2026-06-08

> INTEGRITY NOTE: The official WB SEC result PDF
> (`https://wbsec.gov.in/writereaddata/Result_upload/KMC%20ELECS.pdf`) was **unreachable**
> on 2026-06-09 — the wbsec.gov.in TLS certificate has **expired** and the server returned
> HTTP 503. Party totals/winners above are therefore sourced from Wikipedia's transcription
> of that SEC result, not the raw PDF. Re-verify against the SEC PDF once the site is fixed.

---

## COUNCILLOR ROSTER — `councillors.csv`

- **144 ward rows** (wards 1–144), plus a borough column and per-row source + verification note.
- **Wards 16–144:** name + office address pulled live from KMC's official councillor pages
  `Councillors2.jsp … Councillors10.jsp` (current site data). **No phone numbers** are published
  on these pages (all blank). **No party column** on the KMC site.
- **Wards 1–15:** name + party from the **2021 SEC result (via Wikipedia)**, because KMC's
  `Councillors1.jsp` consistently returns **HTTP 404** (broken on the KMC site; confirmed by
  both WebFetch and curl). These 15 rows lack office addresses.
- **Party column caveat:** Only individually-verifiable parties are stated outright (the 2021
  AITC sweep means most are AITC; named opposition winners e.g. BJP's Meena Devi Purohit W22,
  Sajal Ghosh W50 are tagged BJP). Rows where party is **inferred from the TMC sweep but not
  verified per-ward** are marked **`AITC*`** — the asterisk = "inferred, verify against SEC PDF."
- **Blank-name wards on the official site:** Ward **47** and Ward **79** render with no name on
  the KMC pages — flagged for follow-up (possible vacancy, by-poll, or site data gap).
- Bengali/transliterated names captured **as published** (KMC uses ALL-CAPS English
  transliteration; honorifics SHRI/SMT/MD retained verbatim).

Supplementary: `facilities/borough_chairmen.csv` — 16 borough chairpersons with mobile numbers
(from KMC's borough-chairman page); several are also ward councillors and cross-referenced.

---

## BUDGET BOOKS — `budget_index.json`

KMC hosts year-stamped budget PDFs at `kmcgov.in/KMCPortal/downloads/` under a clean naming
convention. **All URLs below HTTP-verified (200 + PDF payload) on 2026-06-09:**

| FY | Statement (Mayor's speech) | Estimate (detailed) |
|----|---------------------------|---------------------|
| 2026-2027 | ✅ Budget_English_2026_2027.pdf | ✅ Budget_Estimate_2026_2027.pdf |
| 2025-2026 | ✅ Budget_English_2025_2026.pdf | ✅ Budget_Estimate_2025_2026.pdf |
| 2024-2025 | ✅ Budget_English_2024_2025.pdf | ✅ Budget_Estimate_2024_2025.pdf |
| 2023-2024 | ✅ Budget_English_2023_2024.pdf | ✅ Budget_Estimate_2023_2024.pdf |
| 2022-2023 | ❌ 404 (no statement at conventional path) | ✅ Budget_Estimate_2022_2023.pdf |

Full URLs + byte sizes in `budget_index.json`. The downloads directory is **not browsable**
(no index page); filenames must be inferred by convention, so pre-2022-23 years were not probed.

---

## OFFICIAL FACILITY LISTS — `facilities/`

All KMC-hosted, downloaded 2026-06-09 (see `facilities/README.md` for per-file sources):

- **Health:** `KMC_Health_Units.pdf` (ward/UPHC list w/ medical officers + phones),
  `KMC_UPHC_2019.pdf` (Urban Primary Health Centres by ward, 2019).
- **Schools:** `schools/School_Borough_<I..XVI>.pdf` — **all 16 borough PDFs** captured
  (school code, address, type, classes; ~358 KMC primary schools). Plus
  `KMC_Education_Dept_2013.pdf`.
- **Parks:** `KMC_Parks.pdf` (Parks & Squares Dept list).

**Libraries:** No KMC-hosted public-library list found — public libraries in Kolkata sit under
the **WB State Central Library / Dept of Mass Education Extension**, not KMC. Deferred to the
libraries pass.

---

## WHAT'S MISSING / GAPS

1. **WB SEC official result PDF** — gated (expired TLS cert + HTTP 503 on wbsec.gov.in).
   Per-ward party verification + wards 1–15 official names still depend on it.
2. **Councillors1.jsp (wards 1–15)** — 404 on KMC site; addresses for these wards absent.
3. **Wards 47 & 79** — blank names on official KMC pages.
4. **Councillor phone/email** — KMC publishes none; only borough-chairman mobiles available.
5. **Current mayor** — vacant/in transition since Hakim's June-2026 resignation; successor TBD.
6. **Library facility list** — not a KMC dataset.
