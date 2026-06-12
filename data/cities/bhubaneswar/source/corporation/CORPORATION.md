# Bhubaneswar Municipal Corporation (BMC) — Corporation Data

_Compiled 2026-06-09 for the SevenT4 atlas. Authoritative sources only (bmc.gov.in, Odisha SEC). No OSM, no fabrication._

## COUNCIL STATUS (headline)

**A democratically elected council IS sitting. BMC is NOT under an administrator.**

- **Last election:** Odisha urban local body (ULB) polls held **March 2022**; results declared **24 March 2022**. Councillors and the directly-elected Mayor were sworn in shortly after (oath ~March 2022).
- **Significance:** 2022 was the **first time Odisha voters directly elected** the Mayor (and municipality/NAC chairpersons), under amendments to the Odisha Municipal Corporation Act. Term is **5 years** (so the current council runs ~2022–2027).
- **Mayor:** **Sulochana Das (Biju Janata Dal, BJD)** — first woman Mayor of BMC; won the direct mayoral election (defeated BJP's Suniti Mund by a large margin).
- **Deputy Mayor:** **Manjulata Kanhar (BJD)** (Ward 22 corporator).
- **Municipal Commissioner (appointed IAS, not elected):** Chanchal Rana, IAS (per Wikipedia infobox; commissioners rotate — verify against current BMC site for the present incumbent).
- **Wards:** **67** single-member wards, grouped into **3 zones** (North 21 wards, South-West 21 wards, South-East 25 wards), plus 46 revenue villages.

### Council composition (party tally — note source discrepancy)
From the Odisha SEC elected-corporators list (ward-by-ward, the most authoritative; see councillors.csv), the 67 wards break down as:
- **Biju Janata Dal (BJD):** ~48
- **Bharatiya Janata Party (BJP):** ~10
- **Independent (IND):** ~9
(BJD swept; this matches the Wikipedia infobox tally of BJD 48 / BJP 10 / IND 9 = 67. A press aggregate cited different numbers that do not sum to 67 and was not used.)

### Status confidence
- Election held + council sitting + directly-elected BJD mayor: **HIGH confidence** (multiple independent sources: Odisha SEC, BMC public-disclosure, OTV, Daily Pioneer, Wikipedia).
- As of compile date (June 2026) the 2022 council is within its 5-year term; no source indicates dissolution or administrator takeover. (Next ULB polls would be due ~2027.)

## Sources
- Odisha SEC — Names of Elected Corporators (KHORDHA → BMC, wards 1-67, party + reservation): https://sec.odisha.gov.in/wp-content/uploads/2023/02/NAME-OF-ELECTED-CORPORATORS.pdf (live copy currently 404; captured via Internet Archive snapshot 2024-02-08, saved in facilities/SEC_elected_corporators_2022.pdf)
- BMC Corporator Directory 2022 (names + contact numbers; scanned, OCR'd): https://cms.bhubaneswarone.in/uploadDocuments/Directory/Corporator%20Details/Directory20220520_122810.pdf
- BMC public disclosure (2022 ULB candidate affidavits, incl. 12 mayoral candidates): https://www.bmc.gov.in/public-disclosure/1273
- BMC Zones & Wards (3 zones, ward distribution, Deputy Commissioners): https://www.bmc.gov.in/about/zones-wards
- OTV election results: https://odishatv.in/odisha-municipal-elections/bhubaneswar
- Daily Pioneer "Sulochana elected BMC Mayor": https://www.dailypioneer.com/2022/state-editions/sulochana-elected-bmc-mayor.html
- Wikipedia (infobox: mayor, deputy mayor, party tally): https://en.wikipedia.org/wiki/Bhubaneswar_Municipal_Corporation

## Councillor roster
- **councillors.csv** — all **67 wards**: ward, name, party, reservation, contact phone, zone.
- Method: party + reservation + canonical name from the Odisha SEC list (authoritative). Contact phone numbers from the BMC corporator directory (OCR-extracted, tesseract). Zone from BMC Zones & Wards page.
- **Verification notes / gaps:**
  - Names are romanised English (no Odia script in either source). Minor spelling variants exist between SEC and the directory (e.g., Lakshmi Priya / Laxmipriya; Subhransu Sekhar) — SEC spelling used as canonical where they differ.
  - **Ward 27:** name blank in SEC PDF; filled from directory as **Subhransu Sekhar** (BJD). 
  - **Ward 38:** name blank in BOTH the SEC PDF and the OCR'd directory row (party BJD, Reserved-for-Woman). Left blank — **NOT fabricated**; needs manual verification.
  - **Ward 59:** name blank in SEC PDF; filled from directory as **Biranchi Narayana Mahasupakar** (BJD).
  - Contact numbers are best-effort OCR; a few digits may be misread (e.g., truncated/garbled rows in the scan). Treat phone numbers as indicative, not validated.

## Budget books
- **budget_index.json** — BMC budget PDF index, **14 fiscal years (2012-13 through 2025-26)**, direct links from the official BMC budget page (https://www.bmc.gov.in/budget). PDFs indexed/linked, not individually parsed.

## Facility lists (facilities/)
- **parks.csv** — 161 BMC parks (ward + zone), from the official BMC Parks & Recreation page. **CAPTURED.**
- Schools, health centres (UPHC/NUHM), libraries: **NOT captured** — no clean open list published by BMC located (some aggregate counts cited in search snippets only). See facilities/README.md for specifics and the known-but-unparseable BMC council PDF.

## Integrity notes
- All URLs are real and were fetched. The SEC roster PDF's live URL now 404s; the Internet Archive snapshot was used and saved locally for provenance.
- No party/name/contact value was invented. Blanks (Ward 38 name) are preserved as blanks.
