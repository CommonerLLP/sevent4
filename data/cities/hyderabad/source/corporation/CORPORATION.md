# Greater Hyderabad Municipal Corporation (GHMC) — Corporation Data

City: Hyderabad | State: Telangana | Data captured: 9 June 2026

---

## COUNCIL STATUS (HEADLINE)

**There is NO sitting elected council as of June 2026. The GHMC council term ended on 9-10 February 2026, and the corporation was simultaneously trifurcated. It is now run by an appointed Special Officer / Commissioners pending fresh elections.**

| Item | Status |
|---|---|
| Last election | **1 December 2020** (4th Ordinary GHMC election; results declared 5 Dec 2020) |
| Council term | 2021–2026; first met / Mayor elected ~Feb 2021 |
| Mayor (2021–2026) | **Gadwal Vijayalakshmi (TRS/BRS)** — elected 11 Feb 2021 with AIMIM support |
| Term end | **9–10 February 2026** (five-year term concluded) |
| Trifurcation | **11 February 2026** — GHMC split into THREE corporations: **GHMC (150 wards), Cyberabad MC / CMC (76 wards), Malkajgiri MC / MMC (74 wards)** under the CURE (Core Urban Region) framework, via Telangana Govt G.O. |
| Current administration | No elected body. **Jayesh Ranjan (Spl. Chief Secretary, MA&UD) appointed Special Officer for all three corporations**, exercising council powers. R.V. Karnan continues as GHMC Commissioner; G. Srijana → Cyberabad Commissioner; T. Vinay Krishna Reddy → Malkajgiri Commissioner. |
| Next election | Expected ~April–May 2026 (not yet held / not confirmed as of capture date) |

> IMPORTANT for the atlas: the "GHMC" entity and its ward map are mid-reorganization. The councillor roster below reflects the **2020 election / 2021–2026 council** (now expired). Post-Feb-2026 ward boundaries for the three successor corporations were not yet published in machine-readable form at capture time.

### Status sources
- 2020 election & council: https://en.wikipedia.org/wiki/2020_Greater_Hyderabad_Municipal_Corporation_election
- GHMC overview / commissioner: https://en.wikipedia.org/wiki/Greater_Hyderabad_Municipal_Corporation
- Trifurcation (Feb 2026): https://www.thehansindia.com/telangana/ghmc-split-into-3-corporations-1047741 ; https://thesouthfirst.com/telangana/telangana-government-reorganises-ghmc-into-three-separate-municipal-corporations/ ; https://www.deccanchronicle.com/southern-states/telangana/telangana-splits-ghmc-into-three-corporations-1936447
- Telangana SEC GHMC results portal: https://tsec.gov.in/AbstractResultReportGhmc.do
- Official TSEC Gazette of ward-wise elected candidates (scanned PDF, archived): https://web.archive.org/web/20210301185423/https://tsec.gov.in/pdf/circular_gos/Gazette-Elected_Candidates_Names_236.pdf

---

## 1. Councillor Roster — `councillors.csv`

- **150 wards, 150 winners.** Party tally: **TRS 56, BJP 48, AIMIM 44, INC 2** (matches official result).
- Built from the **Telangana State Election Commission GHMC Election Results 2020** dataset (mirrored on OpenCity, organization = greater-hyderabad-municipal-corporation). Fields: ward number, ward name, ward reservation, councillor name, party, party full name, votes, vote-share %, term, source.
- **Contact column is empty** — phone/email for individual councillors is not published in any authoritative open dataset found; GHMC councillor contact pages are not machine-accessible (site behind WAF).
- Data-quality note: source CSV had interleaved duplicate rows for **Ward 18 (Lingojiguda)**; winner resolved as the highest-vote Position-1 record (AKULA RAMESH GOUD, BJP), consistent with Wikipedia. Recorded in the `note` column.
- A verbatim copy of the full official candidate-level results (all 1,278 candidate rows, winners + losers, with reservation/turnout) is preserved at `facilities/ghmc_election_results_2020.csv`.

---

## 2. Budget Books — `budget_index.json`

- **16 budget PDFs indexed, FY 2014-15 → FY 2025-26** (Budget Estimates, Statements, Highlights, plus a 2023-24 Annual Account Statement).
- FY2025-26 outlay reported ~Rs 8,440 crore.
- Authoritative GHMC budget books re-hosted by OpenCity (the GHMC org dataset). GHMC's own budget page `https://www.ghmc.gov.in/ghmcbuget.aspx` is **behind an F5 WAF that 403s automated fetch** from this environment; the `ghmc.gov.in/Budget/...pdf` direct links exist (one captured for 2024-25) but the OpenCity mirror is the reliable machine-readable index.

---

## 3. Official Facility Lists — `facilities/`

All from the GHMC / Telangana government layers mirrored on OpenCity (`organization: greater-hyderabad-municipal-corporation`). Telangana's own portal `data.telangana.gov.in` was **network-unreachable from this environment** (connection timeouts), so its mirror on OpenCity — which re-hosts the same GHMC/TRAC-GIS layers — was used.

| File | Records | Format | Content |
|---|---|---|---|
| `ghmc_election_results_2020.csv` | 1,278 candidate rows | CSV | Full official 2020 results (source for roster) |
| `schools.kml` | 43,242 placemarks (~102 MB) | KML | Telangana Education Dept schools across Hyderabad |
| `health_centres.kml` | 388 | KML | Public health centres |
| `hospitals_2018.kml` | 937 | KML | Hospitals (2018 layer) |
| `community_halls.kml` | 1,375 | KML | GHMC community halls (2018) |
| `public_toilets.kml` | 574 | KML | Public toilets (Sep 2018) |
| `parks.csv` | 50 | CSV | List of parks |
| `playgrounds.csv` | 528 | CSV | List of playgrounds |
| `fire_stations.kml` | 21 | KML | Fire stations (2018) |

Other GHMC OpenCity datasets available but not downloaded (KML, mostly geometry layers): Wards Info, Slums, Annapurna Meals, Canals/Drains/Lakes, Solid Waste Management, Flooding Locations, Trade Licenses, Cadastral Map, Master Plan 2031.

---

## What's missing / honest gaps

- **No machine-readable libraries dataset** found on GHMC/Telangana open data. State Central Library (Afzalgunj) and branch libraries are documented only in prose (sclhyd.telangana.gov.in, Wikipedia "List of libraries in Hyderabad") — not captured as a list.
- **Councillor phone/email contacts** not available in any authoritative open source.
- **data.telangana.gov.in is unreachable** from this environment (timeouts); the geolocations_amenities_ghmc.csv on the state portal could not be pulled directly — OpenCity mirror used instead.
- **Post-trifurcation (Feb 2026) ward boundaries / rosters** for GHMC, Cyberabad MC, Malkajgiri MC are not yet published in open data; only the pre-split 150-ward 2020 council is captured.
- Official **TSEC Gazette PDF** of elected candidates is a **scanned image (no text layer)**; not re-stored here since the structured CSV supersedes it (URL recorded above).
- Several facility KMLs are 2018-vintage (GHMC's last comprehensive open release).
