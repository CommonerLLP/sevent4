# Greater Visakhapatnam Municipal Corporation (GVMC) — Corporation Profile

Compiled for the SevenT4 atlas. City: Visakhapatnam, Andhra Pradesh.
Last updated: 2026-06-09.

---

## COUNCIL STATUS (headline)

**GVMC has an ACTIVE elected council (98 wards). In April 2025 the council flipped from a
YSRCP mayoralty to an NDA (TDP-led) mayoralty via a no-confidence motion.**

- **Current Mayor:** **Peela Srinivasa Rao (Telugu Desam Party / TDP — NDA alliance candidate)**,
  elected **28 April 2025**. He is himself the elected corporator of **Ward 96 (Pendurthi),
  Zone 8** (see councillors.csv). The election meeting was presided over by District Joint
  Collector Mayur Ashok. Rao had earlier been TDP's mayoral nominee in 2021 but lost then for
  want of a majority.
- **The 2025 flip (no-confidence):** On **19 April 2025** the NDA (TDP + Jana Sena + BJP)
  passed a **no-confidence motion against sitting Mayor Golagani Hari Venkata Kumari (YSRCP)**,
  securing **74 votes** — the two-thirds threshold required. YSRCP boycotted the meeting. The
  motion followed a post-2024 political realignment in AP (TDP-led NDA came to state power in
  2024, eroding YSRCP's corporator base through defections/ex-officio shifts). NDA corporators
  also moved a separate no-confidence notice against Deputy Mayor J. Sridhar (YSRCP), with 57
  signatures. GVMC subsequently issued show-cause notices to 27 YSRCP corporators over the
  mayoral vote. YSRCP publicly contested the legitimacy of the ouster.
- **Original 2021 election:** Polled **10 March 2021** for all **98 wards** (wards were raised
  from 81 to 98 in Jan 2021). Result: **YSRCP 58, TDP 30, Jana Sena 3 (Wikipedia tally; some
  press cited 4), BJP 1, CPI 1, CPI(M) 1, Independents 3–4**. Turnout ~59.4%.
  **Golagani Hari Venkata Kumari (YSRCP)** was elected Mayor (the city's 2nd woman mayor) and
  **Jiyyani Sridhar (YSRCP)** Deputy Mayor in March 2021.
- **Party alignment now:** The corporator roster (per the official ward-wise PDF, reflecting the
  2021 result) remains majority-YSRCP on paper, but governance control sits with the **NDA
  (TDP/JanaSena/BJP)** after the 2024 state-level realignment and the April-2025 mayoral change.
  Note the ousted mayor (Ward 11, YSRCP) and the new mayor (Ward 96, TDP) both sit in this council.

### Council status sources
- New mayor Peela Srinivasa Rao (28 Apr 2025): https://www.yovizag.com/peela-srinivasa-rao-elected-as-new-mayor-of-visakhapatnam/
- No-confidence motion passed, 74 votes (19 Apr 2025): https://www.yovizag.com/no-confidence-motion-passed-against-visakhapatnam-mayor/
- No-confidence build-up / strength tally: https://myind.net/Home/viewArticle/nda-alliance-passes-no-confidence-motion-against-ysrcp-mayor-in-greater-visakhapatnam-municipal-corporation
- Show-cause notices to 27 YSRC corporators: https://www.deccanchronicle.com/southern-states/andhra-pradesh/gvmc-issues-show-cause-notices-to-27-ysrc-corporators-over-mayoral-vote-1892000
- YSRCP reaction (mayor removed): https://www.sakshipost.com/news/andhrapradesh/vizag-mayor-removed-ysrcp-slams-tdp-govt-murdering-democracy-399349
- 2021 election (Wikipedia): https://en.wikipedia.org/wiki/2021_Greater_Visakhapatnam_Municipal_Corporation_election
- 2021 mayor election (ANI): https://www.aninews.in/news/national/general-news/ysrcps-golagani-venkat-hari-kumari-elected-as-mayor-of-greater-visakhapatnam-municipal-corporation20210318161054/

---

## Councillor roster (98 wards)

- File: `councillors.csv` — **98 of 98 wards captured.**
- Fields: ward_no, zone (1–8), name, party, address. **Contact/phone is NOT in the source PDF
  and is left blank** (the official corporators PDF lists name + door-number address + party +
  localities only; no phone numbers).
- **Authoritative source:** GVMC official PDF *"Greater Visakhapatnam Municipal Corporation —
  Elected Council Members Details"*, 14 pages, hosted on the corporation site:
  `https://www.gvmc.gov.in/image_uploads/GVMC%20Corporators%20Ward%20wsie%20Area%20details.pdf`
  - **VERIFICATION NOTE:** Direct fetch of gvmc.gov.in failed (TLS connection reset from this
    environment). The PDF was retrieved via the **Internet Archive Wayback Machine** mirror of
    that exact GVMC URL (`https://web.archive.org/web/2id_/https://www.gvmc.gov.in/image_uploads/GVMC%20Corporators%20Ward%20wsie%20Area%20details.pdf`),
    324 KB, PDF v1.7, and text-extracted with `pdftotext`. The PDF reflects the **2021-elected
    council** (it lists Golagani Hari Venkata Kumari as Ward-11 member and Jiyyani Sridhar as
    Ward-52 member). It does NOT encode the April-2025 mayoral change. Names are
    Telugu-origin transliterations exactly as printed in the English-language PDF.
- Party distribution in the roster (as printed): YSRCP majority; remainder TDP, with
  Jana Sena (wards 22, 33, 64), BJP (ward 48), CPI (ward 72), CPI(M) (ward 78), and
  Independents (wards 15, 32, 35, 39). Wards 80–84 fall in the Anakapalli-area zone 7.

---

## Budget books

- File: `budget_index.json`.
- **2024-25:** ~Rs **5,457 crore** (press-reported approved figure; a Rs 5,614 cr figure also
  circulated socially). Presented under Mayor Golagani Hari Venkata Kumari; TDP boycott noted.
- **2023-24:** Rs **4,300 crore** (opening balance Rs 480 cr, closing Rs 239 cr).
- **Canonical budget-PDF index NOT confirmed.** The gvmc.gov.in "Reports/Tenders & Downloads"
  section is served by the dynamic site whose TLS endpoint reset all connections here, so no
  direct official budget-book PDF link was verified. Figures are from press reporting.
- **CAUTION:** `gvmc.org` (.org) is the **US "Grand Valley Metro Council"** and is NOT this
  corporation — do not cite it for Visakhapatnam budgets.

---

## Official facility lists (libraries / schools / health)

See `facilities/README.md`. Summary:
- **Open & available:** Visakhapatnam Wards Map 2024 (98 wards) on OpenCity — KML + PDF, open
  license. (Boundary geometry, not a facility roster.)
- **Health:** GVMC Health page is narrative prose (King George Hospital, est. 1845, 1200+ beds);
  **no structured list** of municipal UHCs/dispensaries published there.
- **Schools / libraries:** **NOT found** as open data. GVMC has Education/Public-Health/UCD
  department sections on its (TLS-blocked) site; AP open-data portals had no GVMC facility roster.

---

## Atlas note — Google/Adani AI data-centre cluster is OUTSIDE GVMC

The ~Rs 87,500 crore (~US$10–15 bn) **Google (Raiden Infotech) AI / hyperscale data-centre
cluster, implemented by Adani Infra**, is being built across three campuses on land facilitated
by **APIIC (AP Industrial Infrastructure Corporation)** — NOT by GVMC:
- **~174.8 acres at Rambilli** — **Anakapalli district** (outside GVMC limits).
- ~266.6 acres at **Tarluvada/Atchutapuram** area and ~160 acres at **Adavivaram & Mudasarlova**
  (Visakhapatnam district). Total allotment reported ~480 acres; 1 GW target capacity; Adani
  created three SPVs for the campuses. Construction start reported 28 April 2025.
- **Jurisdiction flag:** The Rambilli/Atchutapuram SEZ-belt sites are in **Anakapalli district**,
  outside GVMC's municipal boundary. (Note GVMC's own zone-7 wards 80–84 lie in the
  Anakapalli town area — distinct from the Atchutapuram/Rambilli SEZ land.) Land authority is
  **APIIC**, the state industrial-infrastructure body, not the municipal corporation.
- Sources:
  - IBEF (480 acres allotment): https://www.ibef.org/news/andhra-pradesh-government-allots-480-acres-for-adani-google-ai-data-centre-in-visakhapatnam
  - Outlook Business: https://www.outlookbusiness.com/amp/story/news/andhra-govt-allots-480-acres-for-adani-google-ai-data-centre-in-visakhapatnam
  - Swarajya (construction start, $15bn hub): https://swarajyamag.com/news-brief/15-billion-google-data-centre-hub-near-visakhapatnam-to-begin-construction-on-28-april

---

## Integrity / provenance notes
- All URLs above are real and were fetched during compilation. No data fabricated.
- The corporators PDF is the **official GVMC document**, captured via Wayback because the live
  GVMC HTTPS endpoint reset connections from this environment (a March 2026 Wayback snapshot of
  gvmc.gov.in confirms the site is live; the block is environmental, not a dead host).
- Telugu-name roster: transliterations are reproduced verbatim from the English GVMC PDF.
- Gaps honestly flagged: councillor phone numbers (not in source), official budget-PDF links
  (site TLS-blocked), and school/library facility rosters (not openly published).
