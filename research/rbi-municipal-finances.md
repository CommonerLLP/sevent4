# RBI Municipal Finance Reports

Status: deterministic extraction and working analysis.

This note separates RBI municipal-finance evidence from the Finance Commission
note. The FC record explains the constitutional grant/devolution chain. The RBI
reports give the empirical municipal-finance series that The Unelected City should use to
test whether city governments have fiscal life: own-source revenue, property
tax, user charges, State transfers, Finance Commission grants, State Finance
Commission grants, accounts, and expenditure.

## Source Status

| Report round | Local source status | Use in this repo |
|---|---|---|
| RBI 2024, `Report on Municipal Finances`, November 2024 | Verified local PDF. Two copies found with the same SHA-256: `ac021f301bce38e65eaed2328f028d61d15112e2abeb22e6414d92efc1c351db`. Primary copy parsed from `data/reference/RBI_Report_on_Municipal_Finances.pdf`. | Parsed into `research/rbi_municipal_finances_2024_extract.json` by `scripts/research/parse_rbi_municipal_finances.py`. |
| RBI 2022, maiden `Report on Municipal Finances`, November 2022 | A local 2022 PDF was not found on local storage drives by filename/content search. RBI's official press release and publication page were found. The full PDF URL is published, but direct `rbidocs` asset requests returned anti-automation HTML in this environment. | Parsed from official RBI `PublicationsView.aspx` HTML pages into `research/rbi_municipal_finances_2022_extract.json` by `scripts/research/parse_rbi_municipal_finances_2022.py`. |

## Deterministic Parse Contract

These extractions are not LLM synthesis.

The 2024 parser:

- runs `pdftotext -layout` against the verified PDF;
- anchors on fixed RBI table titles and row labels;
- parses only selected tables needed by this repo;
- fails if an expected State row or table row is absent;
- records source path, SHA-256, cover text, and parser path in the JSON output.

The 2022 parser:

- reads official RBI `PublicationsView.aspx` HTML captures with
  `pandas.read_html`;
- anchors on fixed table titles, entity headers, and row labels;
- parses Chapter II summary tables plus the Delhi/All States appendix table;
- records official URLs, downloaded HTML paths, SHA-256 hashes, and parser path;
- fails if an expected table or row is absent.

Parsed 2024 tables:

| RBI table | JSON key | Why it matters |
|---|---|---|
| Table II.2 | `ii_2_state_revenue_receipts_expenditure` | State-wise MC revenue receipts, revenue expenditure, and surplus/deficit. |
| Table II.3 | `ii_3_mc_revenue_to_state_revenue_ratio` | Weight of MC receipts relative to State revenue receipts. |
| Table II.4 | `ii_4_all_mc_revenue_receipts` | All-MC time series for revenue receipts, own tax, property tax, own non-tax, user charges, and transfers. |
| Table II.5 | `ii_5_mc_tax_non_tax_to_state_ratios` | MC tax and non-tax revenues relative to State tax and non-tax revenues. |
| Table II.7 | `ii_7_grants_to_ulbs` | Central grants, FC grants, State grants, SFC grants, and non-SFC State grants. |
| Table II.8 | `ii_8_key_ratios` | Own revenue, tax, property tax, and transfer ratios. |

Parsed 2022 tables:

| RBI source table | JSON key | Why it matters |
|---|---|---|
| Chapter II, Table II.1 | `ii_1_revenue_receipts_percent_gdp` | All-MC revenue receipts, own tax, property tax, own non-tax, and transfers as percent of GDP. |
| Chapter II, Table II.2 | `ii_2_non_tax_revenue_percent_gdp` | Non-tax revenue components, including fees/user charges. |
| Chapter II, Table II.3 | `ii_3_key_ratios_percent` | Own revenue, tax, property tax, State transfer, central transfer, and combined transfer ratios. |
| Appendix I, Delhi/All States table | `appendix_i_revenue_receipts_delhi_all_states_uts` | Delhi and all-State/UT revenue receipt components in INR lakh and derived INR crore. |

The parsers currently cover the tables that directly affect The Unelected City's
municipal-devolution model. They can be extended table by table if expenditure,
borrowings, bonds, or appendix-level MC rows become first-class data.

## What RBI 2022 Measures

RBI 2022 is the maiden report. RBI's press release describes it as a 201-MC
analysis across all States, with the theme `Alternative Sources of Financing
for Municipal Corporations`. Chapter II covers 2017-18 accounts, 2018-19
revised estimates, and 2019-20 budget estimates.

The 2022 report's all-MC fiscal ratios are:

| Ratio | 2017-18 accounts | 2018-19 RE | 2019-20 BE |
|---|---:|---:|---:|
| Own revenue / total revenue receipts | 64.5% | 60.5% | 64.0% |
| Own tax revenue / total revenue receipts | 34.0% | 31.3% | 31.0% |
| Property tax / total revenue receipts | 14.0% | 15.4% | 15.5% |
| State transfers / total revenue receipts | 31.2% | 34.7% | 32.0% |
| Central transfers / total revenue receipts | 3.6% | 4.4% | 3.7% |
| Combined Union plus State transfers / total revenue receipts | 34.8% | 39.1% | 35.7% |

Chapter II also reports revenue receipt components as percent of GDP:

| Component | 2017-18 accounts | 2018-19 RE | 2019-20 BE |
|---|---:|---:|---:|
| Revenue receipts | 0.61% | 0.67% | 0.72% |
| Own tax revenue | 0.21% | 0.21% | 0.22% |
| Property tax | 0.09% | 0.10% | 0.11% |
| Own non-tax revenue | 0.18% | 0.19% | 0.23% |
| Transfers | 0.21% | 0.26% | 0.26% |

The important point is not that the 2022 report and 2024 report form one
simple time series. They do not. The 2022 all-State/UT appendix reports
2019-20 budget estimates for 201 MCs, while the 2024 report reports 2019-20
accounts for 232 MCs. For example, the 2022 appendix gives all-State/UT
2019-20 BE revenue receipts of Rs. 1,41,517.019 crore, while the 2024 report
gives all-MC 2019-20 accounts revenue receipts of Rs. 1,11,308 crore. That
difference is a source-surface warning: report round, coverage, and
accounts/RE/BE status must travel with every row.

## What RBI 2024 Measures

RBI 2024 covers 232 municipal corporations for 2019-20 accounts through
2023-24 budget estimates. It widens the 2022 report's 201-MC coverage and adds
primary survey evidence on property-tax systems.

This matters because the report is not just a narrative about underpowered
ULBs. It gives a reproducible fiscal frame:

- how much revenue MCs report;
- how much is own tax revenue;
- how much comes from property tax;
- how much is own non-tax revenue;
- how much comes from fees and user charges;
- how much is transferred by State and Union channels;
- how Finance Commission and State Finance Commission grants appear in MC
  reports.

## All-India Municipal Corporation Series

From Table II.4 and Table II.8, all 232 MCs move as follows:

| Measure | 2019-20 accounts | 2023-24 BE | Change |
|---|---:|---:|---:|
| Revenue receipts | Rs. 1,11,308 crore | Rs. 1,70,722 crore | +53.4% |
| Own tax revenue | Rs. 30,371 crore | Rs. 51,237 crore | +68.7% |
| Property tax | Rs. 18,389 crore | Rs. 32,450 crore | +76.5% |
| Own non-tax revenue | Rs. 35,324 crore | Rs. 54,503 crore | +54.3% |
| Fees and user charges | Rs. 20,867 crore | Rs. 34,426 crore | +65.0% |
| Transfers | Rs. 45,613 crore | Rs. 64,982 crore | +42.5% |

Key ratios show that MCs are not transfer-free governments:

| Ratio | 2019-20 accounts | 2023-24 BE |
|---|---:|---:|
| Own revenue / total revenue receipts | 59.0% | 61.9% |
| Tax revenue / total revenue receipts | 27.3% | 30.0% |
| Property tax / total revenue receipts | 16.5% | 19.0% |
| State transfers / total revenue receipts | 30.3% | 28.7% |
| Central transfers / total revenue receipts | 2.7% | 2.5% |
| Combined Union plus State transfers / total revenue receipts | 33.0% | 31.3% |

The analytical point is precise: the RBI series does not support a simple
"municipalities only survive on grants" story, but it also does not support a
fiscal-autonomy story. Own revenue is material, property tax is growing, and
transfers remain structurally important.

## Grants, FCs, And SFCs

Table II.7 is the bridge back to the Finance Commission note.

| Grant line | 2019-20 accounts | 2022-23 RE/actual |
|---|---:|---:|
| Central grants to MCs | Rs. 13,881 crore | Rs. 14,731 crore |
| FC grants reported by MCs | Rs. 5,386 crore | Rs. 7,067 crore |
| Central grants other than FC grants | Rs. 8,495 crore | Rs. 7,664 crore |
| State grants to MCs | Rs. 32,148 crore | Rs. 41,872 crore |
| SFC grants reported by MCs | Rs. 6,861 crore | Rs. 8,605 crore |
| State grants other than SFC grants | Rs. 25,287 crore | Rs. 33,267 crore |
| FC grants to ULBs reported in Union Budget | Rs. 25,098 crore | Rs. 17,779 crore |

Two implementation cautions follow.

First, State grants dominate central grants in the MC-reported series. In
2022-23, MC-reported State grants were about 2.8 times central grants. The State
is not a secondary actor in municipal finance; it is the main pass-through and
control point.

Second, do not collapse Union Budget FC grants to ULBs into MC-reported FC
grants. The Union Budget memo line and the MC-reported line are different
measurement surfaces. In 2022-23, the Union Budget line reports Rs. 17,779
crore, while MCs report Rs. 7,067 crore. The Unelected City should store both with source,
denominator, report round, and coverage notes.

The SFC line is also politically important. In 2022-23, MCs report Rs. 8,605
crore as SFC grants, but Rs. 33,267 crore as State grants other than SFC grants.
That means ordinary State grant channels are much larger than the
constitutionally named SFC channel in this RBI table.

## Delhi Signal

Delhi is the strongest immediate reason to parse RBI carefully instead of
guessing.

The 2022 appendix gives Delhi revenue receipts in INR lakh. Converted to INR
crore, the selected rows are:

| Row | 2017-18 accounts | 2018-19 BE | 2018-19 RE | 2019-20 BE |
|---|---:|---:|---:|---:|
| Revenue receipts | Rs. 14,050.742 crore | Rs. 19,811.833 crore | Rs. 19,591.086 crore | Rs. 21,801.725 crore |
| Own revenue | Rs. 9,513.588 crore | Rs. 12,777.387 crore | Rs. 11,953.203 crore | Rs. 14,641.558 crore |
| Own tax revenue | Rs. 4,256.414 crore | Rs. 6,388.770 crore | Rs. 5,140.224 crore | Rs. 5,383.890 crore |
| Property tax | Rs. 2,165.234 crore | Rs. 4,291.000 crore | Rs. 2,822.000 crore | Rs. 2,940.000 crore |
| Own non-tax revenue | Rs. 5,257.174 crore | Rs. 6,387.317 crore | Rs. 6,797.980 crore | Rs. 9,253.668 crore |
| Fees and user charges | Rs. 1,490.369 crore | Rs. 1,673.622 crore | Rs. 1,704.256 crore | Rs. 1,915.737 crore |
| Transfers | Rs. 4,537.154 crore | Rs. 7,034.447 crore | Rs. 7,637.883 crore | Rs. 7,160.167 crore |
| Assigned revenues/compensation | Rs. 838.918 crore | Rs. 1,001.000 crore | Rs. 2,644.833 crore | Rs. 1,020.000 crore |
| SFC grants | Rs. 1,962.383 crore | Rs. 4,632.300 crore | Rs. 3,628.900 crore | Rs. 3,982.000 crore |
| State grant-in-aid transfers | Rs. 1,625.464 crore | Rs. 1,194.647 crore | Rs. 1,161.150 crore | Rs. 1,934.167 crore |

The Delhi appendix row is a direct reason to keep transfer subtypes separate.
In the 2022 extraction, Delhi reports State transfers but no central-transfer
breakout in this appendix row. That does not mean no Union money can ever reach
Delhi municipal finance. It means this RBI source surface did not report a
Delhi central-transfer split here.

Table II.2 gives Delhi MCs:

| Fiscal year | Revenue receipts | Revenue expenditure | Surplus/deficit |
|---|---:|---:|---:|
| 2021-22 accounts | Rs. 14,127 crore | Rs. 15,079 crore | -Rs. 952 crore |
| 2022-23 RE | Rs. 20,678 crore | Rs. 21,116 crore | -Rs. 438 crore |
| 2023-24 BE | Rs. 21,634 crore | Rs. 20,947 crore | Rs. 687 crore |

Table II.3 reports Delhi MC revenue receipts as a share of GNCTD revenue
receipts:

| 2019-20 | 2020-21 | 2021-22 | 2022-23 RE | 2023-24 BE |
|---:|---:|---:|---:|---:|
| 31.7% | 31.7% | 28.6% | 32.9% | 34.5% |

For comparison, the all-India MC-to-State revenue-receipts ratio is 4.0% in
2023-24 BE. Delhi is the highest State/UT row in the parsed table, followed by
Maharashtra at 14.1% and Gujarat at 7.8%.

Table II.5 makes Delhi even more unusual:

| Ratio | 2019-20 | 2023-24 BE |
|---|---:|---:|
| Delhi MC tax revenue / GNCTD tax revenue | 8.3% | 12.3% |
| Delhi MC non-tax revenue / GNCTD non-tax revenue | 48.1% | 82.4% |
| All-India MC tax revenue / State tax revenue | 1.6% | 1.6% |
| All-India MC non-tax revenue / State non-tax revenue | 4.4% | 4.7% |

This does not prove Delhi municipal fiscal autonomy. It proves that Delhi is a
special fiscal object. The MCD/GNCTD budget series must therefore separate:

- MCD own taxes, especially property tax;
- MCD own non-tax revenue, including fees, user charges, parking,
  advertisement, rents, and other recoveries;
- assigned revenues and compensation flows;
- GNCTD grants-in-aid and department-wise transfers to MCD-linked functions;
- FC, SFC, and SFC-like lines, if any;
- accounting effects caused by Delhi's NCT status and the unified/restructured
  MCD history.

## The Unelected City Data Model Implications

Add or preserve these fields wherever city finance data is modeled:

| Field | Reason |
|---|---|
| `source_report_round` | Distinguishes RBI 2022, RBI 2024, FC-15, FC-16, GNCTD budget, and MCD budget surfaces. |
| `source_artifact_sha256` | Makes extracted facts traceable to the exact PDF or HTML capture used by the parser. |
| `coverage_municipal_corporations` | RBI 2022 and 2024 do not cover the same number of MCs. |
| `fiscal_year_status` | Distinguishes accounts, revised estimates, budget estimates, and actuals. |
| `revenue_receipts` | Basic size of municipal fiscal surface. |
| `own_tax_revenue` | Own fiscal life; not the same as total revenue. |
| `property_tax` | Core municipal own-tax instrument in the RBI/FC reform path. |
| `own_non_tax_revenue` | User charges, fees, rents, and recoveries need separate treatment. |
| `fees_user_charges` | Tests service pricing and O&M recovery. |
| `transfers_total` | Upper-tier dependence and pass-through exposure. |
| `central_grants_total` | Union channel; distinct from FC grants. |
| `fc_grants_reported_by_ulb_or_mc` | MC/ULB-reported FC receipts, not Union Budget allocation. |
| `state_grants_total` | Main State channel into MC finance. |
| `sfc_grants_reported_by_ulb_or_mc` | Constitutional State finance channel. |
| `state_grants_other_than_sfc` | Captures State discretion outside SFC logic. |
| `ratio_to_state_revenue_receipts` | Shows whether the ULB is fiscally small or large relative to the State/NCT. |

## Next Delhi Work

The next deterministic step is not another synthesis. It is a joinable Delhi
finance dataset:

1. Parse GNCTD budget time series for MCD grants, assigned revenues, sanitation,
   education, public health, roads, and municipal transfers.
2. Parse MCD budget time series for property tax, fees/user charges, own
   non-tax revenue, grants, assigned revenues, establishment expenditure, and
   capital/revenue expenditure.
3. Add source status for every row: source PDF/URL, fiscal year, accounts/RE/BE,
   table/page if available, extractor version, and hash.
4. Reconcile the MCD series with the RBI 2024 Delhi rows above before any public
   claim is made.

Only after that reconciliation should The Unelected City say whether Delhi's large
municipal-revenue ratio is own-source strength, State/NCT transfer structure,
accounting classification, or a mix.
