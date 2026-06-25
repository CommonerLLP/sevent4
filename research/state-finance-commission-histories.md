# State Finance Commission Histories

Status: integrated research memo from parallel agent pass; source confidence
varies by State. Research pass date: 2026-06-15.

The Unelected City treats State Finance Commissions (SFCs) as first-class evidence for
whether Part IX and Part IX-A devolution has fiscal content. For municipalities,
the constitutional hinge is Article 243Y, read with Article 243X and State
municipal law. For the Union Finance Commission side, Article 280 asks the Union
FC to recommend measures to augment State Consolidated Funds so that States can
supplement municipal resources.

The practical question for each city is not only whether an SFC exists. It is:

```text
Was the SFC constituted on time?
Did it report?
Was the report tabled?
Was an Action Taken Report laid?
Were municipal recommendations accepted?
Did money actually move to the ULB?
Can residents inspect the report, ATR, and transfer lines?
```

## City-State Scope

This scope is derived from `data/cities/*/city.yaml` in this repo.

| City id | City | Government to research | Analytic type |
|---|---|---|---|
| `ahmedabad` | Ahmedabad | Gujarat | ordinary State SFC path |
| `surat` | Surat | Gujarat | ordinary State SFC path |
| `mumbai` | Mumbai | Maharashtra | ordinary State SFC path, special city Act |
| `pune` | Pune | Maharashtra | ordinary State SFC path |
| `bengaluru` | Bengaluru | Karnataka | ordinary State SFC path, BBMP-specific surface |
| `chennai` | Chennai | Tamil Nadu | ordinary State SFC path |
| `hyderabad` | Hyderabad | Telangana | ordinary State SFC path, weak report surface |
| `visakhapatnam` | Visakhapatnam | Andhra Pradesh | ordinary State SFC path |
| `kochi` | Kochi | Kerala | ordinary State SFC path, high-devolution State |
| `bhubaneswar` | Bhubaneswar | Odisha | ordinary State SFC path, strong public report surface |
| `kolkata` | Kolkata | West Bengal | ordinary State SFC path, strong public report surface |
| `kanpur` | Kanpur | Uttar Pradesh | ordinary State SFC path, weak report surface |
| `jaipur` | Jaipur | Rajasthan | ordinary State SFC path |
| `delhi` | Delhi | Delhi NCT | capital-city exception, not an ordinary State row |

Delhi stays in the overall city set, but it should be modeled as a capital-city
exception. The useful comparative bucket is closer to "national capital with a
special constitutional/fiscal wrapper" than to "municipal corporation inside a
normal State." That is a modeling analogy, not a claim that Delhi, Washington,
Canberra, or Ottawa have the same law.

## Evidence Fields

Each State/NCT profile should fill these fields. Unknown is an acceptable value
only when the searches and sources checked are recorded.

| Field | Meaning |
|---|---|
| `sfc_applicability` | Whether Article 243Y-style SFC logic applies normally, specially, or not at all. |
| `sfc_rounds_constituted` | Numbered SFCs with constitution dates and chairpersons where verified. |
| `latest_sfc_period` | Award/report period covered by the latest verified SFC. |
| `latest_sfc_report_public` | Whether the latest report is publicly accessible. |
| `latest_sfc_report_url_or_path` | Official URL/path, preferably State Finance/legislature/local government source. |
| `atr_public` | Whether Action Taken Report/status is public. |
| `atr_url_or_path` | Official ATR URL/path, if found. |
| `municipal_recommendations` | Recommendations specific to ULBs/MCs: property tax, grants, formulae, assigned revenues, audit/accounts. |
| `accepted_municipal_recommendations` | Which municipal recommendations were accepted or visible in budget transfer lines. |
| `implementation_visible` | Evidence that accepted recommendations translated into actual grants/transfers. |
| `city_implication` | What the SFC history means for the repo city/cities in that State. |
| `source_quality` | Official, CAG/FC/RBI secondary, media/academic, or unverified. |

## Source Confidence

| Label | Meaning |
|---|---|
| `official_public` | State SFC portal, State Finance Department, legislature, India Code, CAG, Union FC, or Parliament source is public and directly inspected. |
| `fc_cag_secondary` | Union FC-commissioned State study, NIPFP SFC overview, or CAG audit summarizes the State SFC record, but the State's own report/ATR was not found. |
| `parliament_secondary` | Parliamentary committee/question-answer material identifies compliance or non-compliance. |
| `media_trace` | Current round or chair is visible only through media; do not encode as a working finance formula. |
| `not_found` | Searches did not locate a report, ATR, or notification. |

Core national sources used in this pass:

- Finance Commission constitutional provisions: https://fincomindia.nic.in/constitutional-provisions
- NIPFP, `Overview of State Finance Commission Reports`, hosted in the FC-15 repository: https://fincomindia.nic.in/asset/doc/commission-reports/15th-FC/reports/studies/Overview%20of%20SFC%20reports.pdf
- Repo-local Commoner Probe cross-checks in `data/tmp/commoner_probe_74th_evidence_table.*`, especially `LS|S|134|2022-12-15`, `LS|U|4211|2020-03-19`, and `RS|U|409|2020-09-16`.

## Comparative Summary

| Government | City ids | Latest usable SFC surface | Report/ATR status | City finance signal |
|---|---|---|---|---|
| Gujarat | `ahmedabad`, `surat` | 3rd SFC verified by FC State study, but usable formula evidence is mainly 2nd SFC. | Latest report/ATR not found publicly. | Treat Gujarat ULB formula as stale/unverified; keep Ahmedabad/Surat as municipal corporations with retained property-tax powers but weak SFC transfer visibility. |
| Maharashtra | `mumbai`, `pune` | 4th SFC formula studied; 5th/6th not usable without official report/ATR. | Latest report/ATR not found publicly. | Separate recommendation from implementation; 4th SFC core devolution was rejected, so Mumbai/Pune cannot be assigned a clean accepted formula. |
| Rajasthan | `jaipur` | 4th SFC formula and ATR summarized by FC/NIPFP; 5th interim only. | 5th final report/ATR not found publicly. | Jaipur receives only corporation-eligible ULB formula components if using 4th SFC; later formula not verified. |
| Karnataka | `bengaluru` | 5th SFC reported as tabled in 2026 by media only. | Official report/ATR URL not found. | Bengaluru needs a high-risk flag: BBMP-specific law and election status may affect grants; no formula should be encoded from media alone. |
| Tamil Nadu | `chennai` | Strong compliance indicated by parliamentary/secondary sources. | Exact latest report/ATR URLs not found. | Chennai can be marked as in a comparatively compliant SFC State, but city transfer logic still requires report, ATR, and budget heads. |
| Telangana | `hyderabad` | 1st and 2nd SFC traces; 2025 parliamentary committee described Telangana as early-stage with reports pending. | Report/ATR not found. | Hyderabad/GHMC should be marked weak SFC evidence; do not infer formula. |
| Andhra Pradesh | `visakhapatnam` | 5th SFC 2025-30 reported by media. | Official report/ATR not found. | Track ULB resource-gap and property-tax demand/collection questions, but do not encode formula. |
| Kerala | `kochi` | 7th SFC reported constituted/submitted first report; Kerala has long SFC history. | Latest official public report/ATR not found in this pass. | Model Kochi in high-devolution State context, but keep report/ATR visibility as a gap. |
| Odisha | `bhubaneswar` | 5th SFC public; 6th SFC current chair visible. | 5th report and ATR public; 6th report not found. | Bhubaneswar is directly covered by public SFC ULB recommendations and property/holding-tax questions. |
| West Bengal | `kolkata` | 6th SFC constituted 2024 with interim report/ATR surface; 5th and older reports public. | Strong public report/ATR surface, though 6th final report not found. | Kolkata should be modeled inside the State Municipal Affairs devolution stream, not as fiscally independent from SFC transfers. |
| Uttar Pradesh | `kanpur` | 3rd/4th SFC municipal devolution visible through CAG only. | Latest report/ATR not found. | Kanpur is SFC-transfer-dependent but source surface is weak; use CAG audit flags for accounting/property-tax risk. |
| Delhi NCT | `delhi` | Delhi Finance Commission / local-body finance-commission machinery exists under special NCT statutes. | Official DFC reports/ATRs not found. | Keep Delhi as a capital-city exception: GNCTD, MCD, NDMC, Cantonment, and Union routes must be separated. |

## State Profiles

### Gujarat: Ahmedabad, Surat

`sfc_applicability`: normal State SFC model.

`source_quality`: `fc_cag_secondary` for chronology and formula; `not_found` for latest public State report/ATR.

Verified chronology from the FC-15 Gujarat State-finance study and the NIPFP
SFC overview:

- 1st SFC: constituted 1994, reconstituted 1998, report/submission around
  1997-98/1998, placed in Assembly in 2001.
- 2nd SFC: constituted 2003, report submitted 2006, placed in Assembly in
  2011.
- 3rd SFC: constituted 2011, award period 2010-11 to 2014-15 and extended to
  2016-17, report submitted March 2015. The FC-15 State study recorded that it
  had not been tabled as of May 2019.
- 4th and later SFCs: not verified in this pass.

Municipal substance:

- The 2nd SFC recommended increasing the shareable revenue flow to local bodies
  by an additional 10% of State total revenue receipts.
- The 2nd SFC vertical split was PRIs 62.64% and ULBs 37.36%, based on 2001
  population.
- Within the ULB share, municipal corporations received 49.06% and municipalities
  50.94%, based on urban population.
- Assigned-revenue categories reported in the NIPFP overview include sales tax,
  stamp/registration, electricity duty, entertainment tax, profession tax, and
  vehicles tax.
- The FC-15 Gujarat study says the post-GST issue is not that ULB property tax
  disappeared; it is that State transfers are uncertain because the SFC process
  and formula visibility are weak.

City implication:

- Ahmedabad and Surat should be tagged as `municipal_corporation` for SFC
  distribution logic.
- Do not encode a Gujarat 3rd SFC devolution formula until the actual report
  and ATR are obtained.
- Current data contract status should be:

```yaml
sfc_latest_verified_round: 3
sfc_latest_report_public: false
sfc_atr_public: false
usable_formula_round: 2
ulb_formula_status: stale_unverified
```

Sources:

- Gujarat FC-15 State study: https://fincomindia.nic.in/asset/doc/commission-reports/15th-FC/reports/studies/evaluation/Outcome%20Evaluation%20of%20State%20Finances%20-%20Gujarat.pdf
- NIPFP SFC overview: https://fincomindia.nic.in/asset/doc/commission-reports/15th-FC/reports/studies/Overview%20of%20SFC%20reports.pdf

### Maharashtra: Mumbai, Pune

`sfc_applicability`: normal State SFC model.

`source_quality`: `fc_cag_secondary` for 4th SFC; `media_trace` for 6th SFC; `not_found` for latest official report/ATR.

Verified chronology from NIPFP and the FC-15 Maharashtra State-finance study:

- 3rd SFC: referenced as recommending 40% of total tax and non-tax revenue to
  local bodies; exact constitution/submission metadata not verified here.
- 4th SFC: award period 2011-12 to 2015-16. NIPFP records that Maharashtra
  rejected the core devolution recommendation.
- 5th SFC: Cabinet approval to constitute reported in January 2018; chair
  indirectly identified as V. Giriraj in the FC-15 Maharashtra study
  acknowledgements. Report/ATR not found.
- 6th SFC: media reported Nitin Kareer as chair in August 2025. Official
  notification/report/ATR not found.

Municipal substance:

- 4th SFC recommended 40% of total State tax and non-tax revenue to local
  bodies.
- It recommended 20% of that pool as incentive/performance grants.
- The remaining pool was split 45% ULBs and 55% PRIs by urban/rural population.
- The ULB share was split 40% municipal corporations and 60% municipal councils.
- It recommended 50% profession-tax devolution to the relevant local bodies.
- The FC-15 Maharashtra study reports actual local-body allocation at about 20%
  of State revenue, around half the recommended 40%, and average ULB allocation
  around 4.20% of State revenue during 2006-07 to 2015-16.
- NIPFP records a data-institution problem: lack of authentic updated data and
  no single agency responsible for local-body data collection, analysis, and ATR
  review.

City implication:

- Mumbai and Pune are both municipal corporations, but Mumbai needs a separate
  `municipal_act` marker because it is under the Mumbai Municipal Corporation
  Act rather than the general Maharashtra municipal-corporation frame used for
  Pune.
- Do not use 5th or 6th SFC as an operative formula until official report/ATR is
  found.
- Store the 4th SFC recommendation separately from implementation:

```yaml
recommended_local_body_pool: 40_percent_state_tax_and_non_tax
ulb_share_of_post_incentive_pool: 45_percent
municipal_corporation_share_within_ulb: 40_percent
core_devolution_status: rejected
profession_tax_devolution: recommended_50_percent
```

Sources:

- Maharashtra FC-15 State study: https://fincomindia.nic.in/asset/doc/commission-reports/15th-FC/reports/studies/evaluation/State%20Finances%20of%20Maharashtra.pdf
- NIPFP SFC overview: https://fincomindia.nic.in/asset/doc/commission-reports/15th-FC/reports/studies/Overview%20of%20SFC%20reports.pdf

### Rajasthan: Jaipur

`sfc_applicability`: normal State SFC model.

`source_quality`: `fc_cag_secondary` for 4th SFC; `not_found` for 5th final report/ATR.

Verified chronology from the FC-15 Rajasthan State-finance study and NIPFP:

- 4th SFC: award period 2010-11 to 2014-15; report around 2014-15; ATR accepted
  core recommendations with modifications.
- 5th SFC: constituted in 2015; NIPFP said the final report was not yet
  submitted in its 2018 overview; FC-15 Rajasthan study said two interim reports
  had been submitted.
- 6th SFC: not verified.

Municipal substance:

- 4th SFC recommended 5% of net own tax revenue, plus 100% land revenue, 25%
  entry tax, 3% mineral royalty, 2% excise cess, and 10% stamp-duty surcharge to
  local bodies.
- PRI/ULB split was 75.1% PRIs and 24.9% ULBs, based on 2011 rural/urban
  population.
- ULB distribution formula: 50% population, 10% area, 10% average revenue
  mobilisation, and 30% only among municipalities by population.
- NIPFP records functional grants, performance grants, untied grants, uniform
  municipal accounting under CAG guidance, and service-level benchmarking for
  water, sewerage, and solid waste management.

City implication:

- Jaipur is a municipal corporation/nagar nigam. If using Rajasthan 4th SFC, do
  not accidentally give Jaipur the municipality-only 30% component unless a later
  SFC changed that rule.

```yaml
rural_urban_split: "75.1_pri_24.9_ulb"
ulb_formula: "population_50_area_10_revenue_10_municipalities_only_population_30"
accepted_with_modification: true
latest_final_report_public: false
```

Sources:

- Rajasthan FC-15 State study: https://fincomindia.nic.in/asset/doc/commission-reports/15th-FC/reports/studies/evaluation/Rajasthan.pdf
- NIPFP SFC overview: https://fincomindia.nic.in/asset/doc/commission-reports/15th-FC/reports/studies/Overview%20of%20SFC%20reports.pdf

### Karnataka: Bengaluru

`sfc_applicability`: normal State SFC model, but Bengaluru has a BBMP-specific
statutory/governance surface that needs separate law verification.

`source_quality`: `media_trace` for 5th SFC; `not_found` for official report/ATR.

Agent findings:

- 1st to 4th SFCs were not verified from official public sources in this pass.
- 5th SFC was reported in media as chaired by C. Narayanaswamy, covering
  2026-30, with a 542-page report tabled in the Assembly in March 2026.
- The same media surface reports recommendations to raise local bodies' share to
  60% of Karnataka non-loan net own revenue receipts: 45% rural and 15% urban.
- Media also reports use of slum population instead of illiteracy as an urban
  allocation indicator, and stress on own-source revenue/tax collection.
- Official Karnataka Finance/Legislature report PDF and ATR were not located.

City implication:

- Do not encode the 2026-30 Karnataka 5th SFC formula as operative until the
  official report/ATR is obtained.
- Bengaluru should carry two flags: `bbmp_specific_surface` and
  `latest_sfc_media_only`.
- Election status/local-body constitution can matter for Finance Commission
  grants and should be checked separately.

### Tamil Nadu: Chennai

`sfc_applicability`: normal State SFC model.

`source_quality`: `parliament_secondary` and `media_trace`; `not_found` for exact latest public report URLs.

Agent findings:

- A 2026 Janaagraha-reported finding classed Tamil Nadu among States that have
  constituted all seven SFCs since 1992-93.
- A 2025 Lok Sabha Standing Committee report on Panchayati Raj/Local Governance
  identified Tamil Nadu, along with Punjab, as showing good compliance on SFC
  constitution, report submission, and laying ATRs.
- Exact 1st to 7th constitution dates, chairpersons, latest report URL, and ATR
  URL were not verified in this pass.

City implication:

- Chennai can be marked as being inside a comparatively compliant SFC State.
- That does not yet provide a Chennai transfer formula. The city finance layer
  still needs the latest SFC report, ATR, State budget transfer heads, and
  Greater Chennai Corporation receipts.

Parliament source:

- Standing Committee PDF surfaced in the local Commoner Probe manifest as
  `LS|rural_development|15|18`: https://sansad.in/getFile/app/lsscommittee/Rural%20Development%20and%20Panchayati%20Raj/18_Rural_Development_and_Panchayati_Raj_15.pdf?source=app

### Telangana: Hyderabad

`sfc_applicability`: normal State SFC model, but post-bifurcation source surface is weak.

`source_quality`: `parliament_secondary` plus `media_trace`; `not_found` for report/ATR.

Agent findings:

- 1st Telangana SFC: reportedly constituted in 2017, with G. Rajesham Goud as
  first chair; official order/report not located.
- 2nd Telangana SFC: reportedly chaired by Siricilla Rajaiah for a two-year
  term from 16 February 2024; official report/ATR not located.
- The 2025 Standing Committee report described Telangana as at an early stage,
  with SFC reports yet to be submitted.

City implication:

- Hyderabad/GHMC should be flagged as `weak_sfc_evidence_surface`.
- Do not infer municipal devolution formula until the 2nd SFC report, an ATR, or
  relevant government orders are obtained.

### Andhra Pradesh: Visakhapatnam

`sfc_applicability`: normal State SFC model, with bifurcation-related chronology risk.

`source_quality`: `media_trace`; `not_found` for official latest report/ATR.

Agent findings:

- 1st to 4th AP SFCs were not verified in this pass, especially because
  pre/post-2014 continuity needs careful treatment.
- 5th SFC was reported in 2025 as covering 2025-26 to 2029-30.
- Media summary reported an estimated ULB resource gap of Rs 2,016 crore for
  2025-30 and a property-tax demand/collection gap.
- Official report/ATR not located.

City implication:

- Visakhapatnam/GVMC should track property-tax demand, collection, arrears, and
  the SFC-estimated ULB resource gap.
- No formula should be populated until the report text and ATR are obtained.

### Kerala: Kochi

`sfc_applicability`: normal State SFC model.

`source_quality`: `media_trace` for current round, secondary evidence for SFC regularity; `not_found` for latest official public report/ATR in this pass.

Agent findings:

- Kerala was reported among States that have constituted all seven SFCs since
  1992-93.
- 7th Kerala SFC was reported as constituted in September 2024 for two years,
  chaired by K. N. Harilal, with a first report submitted for FY 2026-27.
- Final recommendations for 2027-28 to 2030-31 were reported as pending after
  the Union FC report.
- Direct probe of the Kerala SFC site did not yield a usable body in this
  environment.

City implication:

- Kochi should be modeled in a high-devolution State context, but report/ATR
  visibility remains a gap.
- City finance fields should separately track State formula grants, own-source
  revenue, property tax, profession tax, user charges, Union FC grants, and
  municipal accounts.

### Odisha: Bhubaneswar

`sfc_applicability`: normal State SFC model.

`source_quality`: `official_public`.

Verified chronology/source surface:

- Odisha has a public State Finance Commission portal that links previous SFC
  reports and ATRs.
- The portal shows a 6th SFC chair, Dr. Arun Kumar Panda.
- 5th SFC profile identifies Dr. Ravi Narayan Senapati as chair, notification or
  constitution date as 02.08.2019, report submission as 17.02.2020, and period
  2020-21 to 2024-25.
- 5th SFC Volume I, Volume II, and Action Taken Report are public on the portal.
- 6th SFC report/ATR not found in this pass.

Municipal substance:

- Odisha SFC material separates Municipal Corporations, Municipalities, and
  NACs.
- The 4th ATR records ULB devolution categories and total ULB devolution of
  Rs. 823 crore, including municipal corporations and municipalities.
- The 4th ATR discusses municipal cadre, Directorate of Municipal
  Administration, accounting standards, utilization monitoring, service
  standards, and web disclosure.
- Property/holding-tax issues recur: property-tax bills, holding-tax litigation,
  low municipal rates, and periodic increase of core municipal taxes.
- 5th SFC Volume II sought information from Bhubaneswar Municipal Corporation on
  simplification of property/holding tax, GIS mapping, land-use change fee,
  parking, and 4th SFC grant project status.

City implication:

- Bhubaneswar is a strong candidate for early deterministic SFC acquisition
  because report and ATR URLs are public.

```yaml
latest_completed_public_round: 5
latest_completed_period: "2020-21_to_2024-25"
latest_report_public: true
latest_atr_public: true
current_round_report_public: false
```

Sources:

- Odisha SFC portal: https://sfc.odisha.gov.in/
- 5th SFC Volume I: https://sfc.odisha.gov.in/sites/default/files/2025-04/5th%20SFC%20Report%20Volume-I_0.pdf
- 5th SFC Volume II: https://sfc.odisha.gov.in/sites/default/files/2025-04/5th%20SFC%20Report%20Volume-II_0.pdf
- 5th SFC ATR: https://sfc.odisha.gov.in/sites/default/files/2025-04/5th%20SFC%20Action%20Taken%20Report_0.pdf

### West Bengal: Kolkata

`sfc_applicability`: normal State SFC model.

`source_quality`: `official_public`.

Verified chronology/source surface:

- 1st SFC: Notification 1023-FB dated 30.05.1994; report submitted 27.11.1995;
  ATR published 22.07.1996.
- 2nd SFC: Notification 1770-FB dated 14.07.2000; report submitted 06.02.2002;
  ATR published 15.07.2005.
- 3rd SFC: Notification 4000-FB dated 22.02.2006; report submitted 31.12.2008;
  ATR published 16.07.2009.
- 4th SFC: Notification 121-FB dated 30.04.2013; report date has an internal
  source conflict between 02.02.2016 and 02.03.2016; ATR tabled/published
  20.06.2022.
- 5th SFC: Notification 132-FB dated 23.05.2022; chair Dr. Abhirup Sarkar;
  period 2020-21 to 2024-25; started 01.06.2022.
- 6th SFC: Notification 1196-FB dated 17.12.2024; chair Dr. H.K. Dwivedi;
  period commencing 01.04.2025; preliminary/interim report surface found, final
  report not found.

Municipal substance:

- The 6th SFC notification explicitly covers distribution of State taxes,
  duties, tolls, and fees with Municipalities; assignment/appropriation of taxes
  to Municipalities; grants-in-aid from the Consolidated Fund; and measures to
  improve municipal finances.
- 5th SFC recommended Rs. 905 crore vertical devolution for 2020-21 with a 5%
  annual increase.
- 5th SFC split untied funds between RLBs and ULBs by 2011 rural/urban
  population ratio, recorded as 68:32.
- 5th SFC recommended a 2% incentive fund based on accounts/audit reporting and
  fund utilization, split 68% Panchayats and Rural Development and 32% Municipal
  Affairs.
- 5th SFC recommended 30% of profession tax and vehicle tax collections to be
  shared between Panchayats and Municipalities in the 68:32 ratio.
- 6th interim/ATR accepted continuation of the 5th formula for FY 2025-26 and
  accepted Rs. 1,155 crore total devolution, with ULB/RLB split by 68:32.

City implication:

- Kolkata Municipal Corporation belongs inside the State Municipal Affairs
  devolution stream.
- The city should not be modeled as fiscally independent from SFC transfers just
  because it is a major metropolitan municipal corporation.
- West Bengal is a strong candidate for deterministic report/ATR parsing because
  public State Finance Department PDFs exist.

Sources:

- 6th SFC notification: https://finance.wb.gov.in/writereaddata/1196-F.B..pdf
- 5th SFC interim report: https://finance.wb.gov.in/writereaddata/5th%20SFC%20Report.pdf
- 4th SFC publication page: https://finance.wb.gov.in/Fin_New/Pages/publication.aspx?type=26
- 5th SFC publication page: https://finance.wb.gov.in/Fin_New/Pages/publication.aspx?type=32
- 6th SFC publication page: https://finance.wb.gov.in/Fin_New/Pages/publication.aspx?type=33

### Uttar Pradesh: Kanpur

`sfc_applicability`: normal State SFC model.

`source_quality`: `fc_cag_secondary`; `not_found` for latest official SFC report/ATR.

Agent findings from CAG source surface:

- Relevant municipal statutes in the CAG audit are the Uttar Pradesh
  Municipalities Act, 1916 and Uttar Pradesh Municipal Corporation Act, 1959,
  both amended after the 74th Amendment.
- CAG says the 3rd SFC recommended devolution of 7.5% of total State tax revenue
  to ULBs.
- CAG says the 3rd and 4th SFCs recommended 7.5% of State tax revenue to ULBs.
- Latest SFC report, ATR, constitution notification, or SFC portal was not
  located.

Municipal substance:

- CAG describes UP ULB revenue as SFC grants, Central Finance Commission grants,
  State grants, centrally sponsored scheme grants, and own revenue.
- CAG records that actual devolution against the 3rd/4th SFC 7.5%
  recommendation was erratic and below the recommended level.
- Property-tax administration was weak: assessment lists, old surveys,
  self-assessment implementation, arrears, and demand/collection registers all
  appeared as problem areas.
- Accounts/audit weaknesses included delayed or non-laid audit reports,
  unsettled audit observations, partial implementation of accrual/double-entry
  accounting, and weak utilization certification.
- Kanpur was named in municipal solid-waste audit material for processing,
  disposal, transport, concession/tipping-fee, and SFC/13th FC fund issues.

City implication:

- Kanpur should be flagged as SFC-transfer-dependent but low-visibility.
- Do not populate precise UP chronology fields until an official UP report/ATR
  or government order is obtained.

Source:

- CAG Uttar Pradesh ULB audit, 2016: https://cag.gov.in/webroot/uploads/download_audit_report/2016/Report_of_2016_-_Annual_Technical_Inspection_on_Urban_Local_Bodies_Government_of_Uttar_Pradesh_for_the_year_ending_31_March_2016.pdf

## Capital-City Exception: Delhi

`city_id`: `delhi`

`analytic_type`: `capital_city_exception`

Delhi is retained in the city set, but it should not be forced into the normal
State SFC comparison. The modeling problem is different: Delhi is a Union
Territory with a legislature, a national-capital constitutional wrapper, and
multiple local bodies with different statutory homes.

Legal/fiscal surface:

- Part IX-A applies to Union Territories through Article 243ZB's adaptation
  clause.
- Article 239AA separately identifies the National Capital Territory and limits
  the legislative field, with police, public order, and land excluded.
- Delhi Municipal Corporation Act, 1957, section 107A requires the Administrator
  to constitute a Finance Commission every five years for MCD finances. The
  commission recommends distribution of divisible local taxes/fees between NCT
  Delhi and MCD, assigned or appropriated taxes/fees, grants-in-aid from the
  Consolidated Fund of NCT Delhi, and measures to improve MCD finances. It also
  requires report/recommendations plus explanatory material/ATR to be laid before
  the Delhi Assembly.
- NDMC Act, 1994 has an analogous finance-commission architecture; NDMC is not a
  ward-level component of MCD.
- Delhi Cantonment Board should remain a separate Ministry of Defence/cantonment
  governance surface.

Union FC implication:

- Do not treat Delhi as receiving the ordinary State share/local-body grant path.
- FC-15 treated Delhi specially for an urban-flooding metro allocation because
  it is a Union Territory with legislature, directing the Ministry of Finance to
  handle the requisite allocation rather than making a normal State allocation.

City implication:

```yaml
sfc_status: capital_city_exception_nct_finance_commission
ordinary_state_sfc_comparable: false
delhi_finance_surfaces:
  - gnctd_budget
  - mcd_budget
  - ndmc_budget
  - delhi_cantonment_board
  - union_ministry_or_fc_special_routes
sfc_report_public: false_or_not_found
atr_public: false_or_not_found
assigned_revenue: true_under_dmc_act_surface
state_or_nct_grants: true_under_dmc_act_surface
```

Sources:

- Delhi Municipal Corporation Act, 1957: https://www.indiacode.nic.in/bitstream/123456789/1410/1/a1957-66.pdf
- NDMC Act page: https://www.ndmc.gov.in/ndmc/act.aspx
- Finance Commission constitutional provisions: https://fincomindia.nic.in/constitutional-provisions

## Data Contract Additions

The SFC note suggests these finance fields for each city profile or city finance
record:

```yaml
state_finance_commission:
  applicability: normal_state_sfc | capital_city_exception | unknown
  latest_verified_round: null
  latest_verified_period: null
  latest_report_public: false
  latest_report_url_or_path: null
  latest_atr_public: false
  latest_atr_url_or_path: null
  usable_formula_round: null
  usable_formula_confidence: official_public | fc_cag_secondary | parliament_secondary | media_trace | not_found
  municipal_tier_in_formula: municipal_corporation | municipality | nac | special_capital_body | unknown
  formula_summary: null
  implementation_evidence:
    report_text: false
    atr_or_acceptance_order: false
    state_budget_transfer_head: false
    municipal_receipt_line: false
    cag_or_fc_cross_check: false
  city_implication: null
```

For Delhi:

```yaml
capital_city_exception:
  enabled: true
  comparable_to_ordinary_state_sfc: false
  local_body_surfaces:
    - mcd
    - ndmc
    - cantonment
  upper_government_surfaces:
    - gnctd
    - union
```

## Integration Rule

Do not merge SFC claims into a city finance dataset until the source surface is
known:

- report text;
- ATR or government acceptance order;
- State budget demand/head showing transfers to ULBs;
- municipal budget/accounts showing receipt;
- CAG or FC cross-check where primary State publication is missing.

Use `media_trace` only as a search lead. It can identify that a commission may
exist, but it cannot become a formula in the city dataset.

For Delhi, do not force a normal State-SFC model. Keep it as a capital-city
exception and build the finance view from GNCTD budget lines, MCD budget lines,
NDMC budget lines, Cantonment material where relevant, and Union/FC special
routes.

## Acquisition Queue

1. Parse official West Bengal and Odisha reports/ATRs first. They have the best
   public source surface and can define the extraction schema.
2. For Gujarat, Maharashtra, and Rajasthan, use FC-15 State studies and NIPFP as
   secondary anchors, then search State legislature/finance portals for the
   missing primary reports and ATRs.
3. For Tamil Nadu, Kerala, Karnataka, Andhra Pradesh, Telangana, and Uttar
   Pradesh, locate official SFC report/ATR URLs before encoding formulae.
4. For every State, connect SFC recommendations to State budget demand heads and
   municipal receipt lines. The report/ATR alone is not implementation.
5. For Delhi, continue the separate GNCTD budget series plus MCD budget
   acquisition work. Do not let the Delhi exception distort ordinary State SFC
   comparisons.
