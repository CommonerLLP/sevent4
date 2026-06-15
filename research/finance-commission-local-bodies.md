# Finance Commissions And Municipal Devolution

Status: working analysis for SevenT4.

This note pulls the Finance Commission (FC) material on local bodies into this
repo's understanding of Part IX-A. It is based on report material found on the
external disk, plus the Commoner Probe Parliament corpus already extracted in
`data/tmp/`. The PDFs remain local source material; this public repo should cite
canonical sources instead of redistributing third-party PDFs.

## Source Inventory

External-disk files inspected:

| Local file | How it is used here |
|---|---|
| `16 th Finance Commission Vol 1 - Main - Report.pdf` | Main source for the current FC view, especially Chapter 10 on local body grants. |
| `Draft-Report-on-Conditional-Transfers-Fifteenth-Finance-Commission.pdf` | Historical and legal analysis of conditional grants under Articles 270, 275, and 282; useful for FC-10 to FC-14 local-body conditions. |
| `MUNICIPALFINANCES131124AE4D91D4DD4A4629A88DA79BF0C52C73.pdf` | RBI 2024 municipal-finance report; not an FC report, but a strong empirical companion on own-source revenue, transfers, SFCs, property tax, and Delhi municipal receipts. |
| `Finance_Commission_Public_Libraries_Submission.pdf` | Civil-society style submission asking FC-16 for an earmarked local-body public-library grant; useful as evidence of how civic infrastructure claims are routed through FC grants. |
| `State-wise_Devolution_Shares__13th_15th_FC_.csv` | Background on State devolution shares across FC-13 to FC-15, not a municipal-grant dataset. |
| `Finance_Commission_Weight_Comparison.csv` | Background on horizontal devolution criteria across FC-13 to FC-15, not a municipal-grant dataset. |

Open gap: older official FC report PDFs were not found by obvious filename
search on the mounted external disk. The historical account below therefore
uses FC-16's review of previous FC local-body grants and the report to FC-15 on
conditional transfers, both of which summarize older FC grant architecture.

The RBI municipal-finance material is now treated separately in
[RBI Municipal Finance Reports](rbi-municipal-finances.md). That note records
the verified 2024 PDF hash, the parser, and the extracted tables used for Delhi
and all-India municipal-finance claims.

Repo-local Commoner Probe evidence used as a cross-check:

| Record | Relevance |
|---|---|
| `RS|U|409|2020-09-16` | Describes FC-15 ULB grants: million-plus cities, tied grants, and non-million-plus grant split. |
| `RS|U|1496|2024-12-09` | Frames 74th Amendment as transformative but says functional devolution has not been matched by adequate revenue transfer. |
| `LS|U|4211|2020-03-19` | Places Article 243X fiscal powers in State hands and records Delhi as having 13 Twelfth Schedule functions devolved. |
| `LS|S|134|2022-12-15` | Links strengthening ULBs to SFC constitution, SFC award implementation, property tax/user charges, and municipal bonds. |
| `LS|U|2684|2022-03-17` | Connects FC-15 property-tax conditions, AMRUT/SBM reforms, and municipal-bond incentives to ULB revenue. |

## Main Finding

The Finance Commissions do not see municipalities as fiscally sovereign city
governments. They see them as constitutionally recognized local bodies whose
capacity depends on a State-mediated fiscal chain:

```text
Union FC recommendation -> State Consolidated Fund -> State/SFC distribution -> ULB budget -> public accounts and services
```

That is the operational meaning of "no money, no devolution." Part IX-A creates
the municipal constitutional frame, but the FC record asks whether that frame is
backed by grants, State transfers, assigned revenues, own-source revenue,
property tax, user charges, accounts, audit, and service-level data.

For SevenT4, this means the finance layer is not an appendix. It is one of the
ways jurisdiction becomes visible.

## Constitutional Mechanism

Article 280 is the FC hinge. For municipalities, the relevant question is not
only vertical tax devolution from Union to States, but the FC duty to recommend
measures needed to augment the Consolidated Fund of a State so that the State
can supplement municipal resources.

The FC mechanism is therefore indirect. It does not normally send a clean,
resident-facing entitlement straight to a city. It operates through the State,
and it expects State Finance Commissions (SFCs) under Article 243Y to recommend
how municipal resources should be distributed within that State.

That design produces the central tension in the record:

- The Constitution says the Union FC should consider local-body resources on
  the basis of State Finance Commission recommendations.
- State Finance Commissions are frequently delayed, uneven, methodologically
  inconsistent, or weakly implemented.
- The Union FCs therefore repeatedly design national grant formulae without
  being able to rely fully on SFC reports.
- The State remains the primary constitutional actor for functions, funds, and
  functionaries.
- The Union FC becomes a pressure device: it uses grants and conditions to push
  States and ULBs toward accounts, revenue effort, property tax reform, and
  service benchmarks.

This is why the FC view is not just "give cities money." It is "make cities
auditable, make States transfer money, make ULBs raise some of their own
revenue, and use grant conditionality to discipline the chain."

## Historical Arc

### FC-10 To FC-12: Local Bodies Enter The FC Grant Frame

After the 73rd and 74th Amendments, local bodies enter the FC system as grant
recipients. FC-10 used ad hoc grants: Rs. 100 per capita for rural population
and Rs. 1,000 crore for municipalities. FC-11 raised the envelope to
Rs. 8,000 crore for panchayats and Rs. 2,000 crore for municipalities. FC-12
recommended Rs. 25,000 crore, divided 80:20 between panchayats and ULBs.

The analytical point: the FCs initially translate the constitutional amendment
into fiscal supplementation. The ULB is recognized, but still as a body whose
resources are topped up through State-mediated grants.

### FC-13: Buoyancy And Conditionality

FC-13 changed the character of local-body finance by linking local bodies to
the buoyancy of Union taxes. It recommended that local bodies receive a share
equivalent to a percentage of the divisible pool, converted into grants-in-aid.
For 2010-15, local-body grants were equivalent to 1.93% of the divisible pool.
The urban share was 26.82%, based on population.

FC-13 also made performance grants a governance instrument. Conditions included:

- maintenance of accounts by PRIs and ULBs;
- audit systems for all local bodies;
- an independent local-body ombudsman;
- electronic transfer of grants to local bodies within a short deadline;
- legislation specifying SFC member qualifications;
- enabling local bodies to collect property tax;
- creation of State-level property tax boards;
- standards for essential services;
- fire-hazard response plans.

The analytical point: FC-13 turns municipal finance into an institutional test.
The ULB is not assessed only by functions listed in law. It is assessed by
whether accounts, audit, tax powers, transfer systems, and service standards
exist.

### FC-14: Fixed Grants, Basic Grants, Performance Grants

FC-14 moved toward fixed grants under Article 275. It recommended
Rs. 2,87,436 crore in local-body grants for 2015-20: Rs. 2,00,292.2 crore for
panchayats and Rs. 87,143.8 crore for municipalities.

For municipalities, FC-14 used an 80:20 split between basic and performance
grants. Performance grants were tied to audited accounts and improvement in own
revenues.

The analytical point: FC-14's architecture treats municipal autonomy as a
combination of unconditional minimum support plus conditional incentives for
financial discipline. "Own revenue" becomes a proxy for whether the ULB is a
governmental body with fiscal life, not merely a local spending office.

### FC-15: Tied Grants, Online Accounts, Property Tax, SFC Pressure

FC-15 scaled the local-body envelope to Rs. 4,36,361 crore for 2021-26. Within
that, Rs. 1,21,055 crore went to ULBs. Its ULB architecture distinguished
million-plus cities from other ULBs. The local Parliament corpus describes the
million-plus stream as tied to air quality and water/sanitation/solid waste,
while non-million-plus grants were split between basic and tied components.

FC-15 also made online publication of accounts an entry-level condition for
grants. RBI's municipal-finance report reads FC-15 as mandating ULBs to prepare
and publish unaudited accounts for the previous year and audited accounts for
the year before that. It also records FC-15's property-tax direction: States
should notify minimum floor rates and improve collection in line with State GSDP
growth as a grant condition.

The analytical point: FC-15 makes municipal finance more data-dependent. It
does not simply ask whether the State has passed a municipal law. It asks
whether accounts are online, whether property tax is being modernized, and
whether tied grants are producing measurable water, sanitation, solid waste, and
air-quality outcomes.

### FC-16: Conditional Fiscal Federalism For Local Bodies

FC-16 is the clearest current statement of the FC view. It says full devolution
of governance and financial powers to local bodies remains a work in progress.
It also states that Union FC grants should supplement, not substitute, resources
transferred by States on SFC recommendations.

Core FC-16 recommendations and design choices:

- Total local-body grants for 2026-31: Rs. 7,91,493 crore.
- Urban allocation: Rs. 3,56,257 crore.
- ULB grant categories: basic, performance, special infrastructure, and
  urbanisation premium.
- Basic/performance split: 80:20.
- State-level ULB allocation: 90% projected urban population, 10% own-source
  revenue index.
- Within-State ULB distribution: use latest accepted SFC recommendations; if
  absent, distribute by ULB urban population and own-source revenue in a 90:10
  ratio.
- Entry-level conditions: a duly constituted local body under Part IX/IX-A,
  online public accounts, and timely SFC constitution with Action Taken Reports
  laid in the State legislature.
- ULB performance component: ULBs must grow own-source revenue by the specified
  formula from the second award year onward.
- State performance component: States must transfer from their own resources at
  least 20% of the previous year's basic FC grant to local bodies.
- Tied component: 50% of the basic component is tied to sanitation/solid waste
  management and/or water management.
- Use restrictions: untied grants should not pay salaries or establishment
  expenditure, and no more than 20% of untied allocation should go to roads.
- Data/accounting: extend the Urban Data platform to ULB accounts and financial
  reports.
- Audit: strengthen CAG technical guidance and Local Fund Audit Departments.
- Budget transparency: States should separately report transfers to RLBs and
  ULBs, including FC grants, CSS transfers, SFC grants, and other State grants.

The major institutional move is FC-16's recommendation to remove the
constitutional phrase requiring Union FC local-body recommendations to be made
"on the basis" of SFC recommendations. That is not a minor drafting point. It
signals that SFCs are constitutionally central but operationally unreliable. The
Union FC wants a cleaner national basis because State SFC reports remain too
heterogeneous, delayed, and difficult to use.

## The FC Theory Of Municipal Government

Across these materials, the FCs see municipalities through five linked tests.

### 1. Legal Constitution Is Necessary But Not Sufficient

A duly constituted ULB is now an entry condition for grants, but it is only the
first test. FCs do not treat elections or municipal incorporation as enough.
The harder question is whether the body has money, accounts, tax instruments,
and service responsibility.

### 2. States Are The Bottleneck

The FCs repeatedly say the primary responsibility for funds and functionaries
rests with State governments. Parliament answers echo this: urban development
and local self-government remain State subjects, and Article 243X fiscal powers
are exercised through State law.

This is the key political reading for SevenT4. When a ULB is weak, the cause is
often not only municipal failure. It is State control over functions, fiscal
assignments, staffing, grants, and audits.

### 3. SFCs Are The Constitutional Bridge And The Administrative Failure Point

The SFC is supposed to be the State-level equivalent that tells the State how to
share resources with municipalities and panchayats. But the FC record treats
SFCs as irregular and uneven. FC-15 used grant eligibility to push States to
constitute SFCs and lay reports. FC-16 keeps that pressure but also recommends
weakening the dependency of Union FC recommendations on SFC reports.

For the atlas, "SFC status" should be a first-class field.

### 4. Own-Source Revenue Is Treated As Autonomy Evidence

FCs and RBI both treat own-source revenue as the measure of municipal fiscal
life. The core revenue instruments are property tax, user charges, fees, rents,
assigned revenues, and other local taxes where still available.

RBI's 2024 report sharpens this: municipal corporations remain heavily reliant
on upper-tier transfers, own revenues are inadequate for most MCs, property tax
is the major own-tax source, and user charges are often underpriced. RBI's
recommended path aligns with the FC path: GIS property tax systems, digital
payment, periodic revision of water and drainage taxes, rational user charges,
stronger collection, standardized accounts, and predictable State transfers.

### 5. Data And Audit Are Governance, Not Back Office

FC conditionality turns accounts, audits, public disclosure, and data platforms
into constitutional infrastructure. A city whose accounts are missing, late,
unstandardized, or unaudited is not merely administratively sloppy. It is harder
for that city to claim performance grants, prove need, prove revenue effort, or
prove that devolution has material content.

## Delhi Implications

Delhi should not be modeled as an ordinary State-municipality case.

The FC-16 local-body chapter is framed around States and State-level allocation
formulae. Its general devolution chapters explicitly work with 28 States, while
taxes accruing to Union Territories sit outside the divisible pool. In the
searched local-body text, Delhi does not surface as a normal State allocation
row. That means Delhi finance work cannot rely on a standard "State FC grant
row -> ULB allocation" path without checking Delhi's special constitutional and
statutory route.

For Delhi, the FC frame still tells us what to look for:

- GNCTD budget heads for grants-in-aid, municipal transfers, assigned revenues,
  sanitation, education, public health, roads, and other MCD-linked functions.
- MCD budget heads for property tax, toll/parking/advertisement style revenues,
  user charges, fees, rents, grants, assigned revenues, and scheme transfers.
- Any FC or FC-like grant recorded in MCD accounts.
- Any SFC-like Delhi/NCT finance commission material, or the absence of it.
- Whether MCD publishes provisional and audited accounts online in a
  grant-compatible form.
- Whether GNCTD records transfers to MCD separately from other urban schemes.
- Whether MCD's own-source revenue is sufficient for the 13 devolved Twelfth
  Schedule functions recorded in the Parliament corpus.

The RBI 2024 municipal-finance report gives Delhi an additional empirical
signal. For 2023-24 BE, Delhi municipal corporations' revenue receipts are
listed at Rs. 21,634 crore against revenue expenditure of Rs. 20,947 crore,
with a budgeted surplus of Rs. 687 crore. RBI also reports Delhi MC revenue
receipts at 34.5% of GNCTD revenue receipts, the highest ratio in the report's
State/UT table. Delhi MC tax revenue is 12.3% of GNCTD tax revenue, while MC
non-tax revenue is 82.4% of GNCTD non-tax revenue.

That does not prove fiscal autonomy. It proves Delhi is fiscally unusual. The
next Delhi task is to disaggregate the MCD/GNCTD relationship: which revenues
are genuinely MCD own revenue, which are assigned or compensated by higher
government, which are tied grants, and which are accounting effects of Delhi's
special NCT structure.

## What This Changes In SevenT4

The city note should no longer stop at "which Act governs this ULB?" It should
ask how the FC/SFC fiscal chain sees the city.

For each city, SevenT4 should maintain:

| Field | Why it matters |
|---|---|
| `municipal_statute` | Names the legal body and the State law controlling functions and taxes. |
| `sfc_status` | Shows whether the constitutional State-level finance mechanism is alive. |
| `sfc_report_public` | Shows whether residents can inspect the State's devolution logic. |
| `sfc_atr_public` | Shows whether the State has acted on the SFC report. |
| `fc_grants_basic` | Captures minimum FC support. |
| `fc_grants_tied` | Shows grant dependence on water, sanitation, solid waste, air quality, etc. |
| `fc_grants_performance` | Tracks whether the ULB qualifies through accounts and revenue effort. |
| `state_grants` | Captures ordinary State support outside FC grants. |
| `assigned_revenue` | Tracks State-assigned taxes/revenues that substitute for direct municipal tax power. |
| `own_source_revenue` | Measures fiscal life of the ULB. |
| `property_tax` | Main municipal own-tax instrument. |
| `user_charges` | Tests whether services recover O&M or remain politically underpriced. |
| `accounts_public` | FC entry condition and public accountability baseline. |
| `audit_public` | Tests whether finances can be trusted. |
| `grant_release_delay_days` | Captures State bottleneck and pass-through failure. |
| `cityfinance_record_available` | Indicates whether national municipal-finance data can be used. |
| `property_tax_gis_system` | Tracks FC/RBI reform path for enumeration and collection. |

This also changes public explanatory notes. Each city should have a jurisdiction
note and a finance-devolution note:

- Who is the ULB?
- Which State law creates it?
- Which functions are legally devolved?
- Which parastatals or State departments hold city functions outside the ULB?
- What did the latest SFC say?
- What did the State actually transfer?
- What FC grants reached the ULB?
- What own revenue does the ULB raise?
- Are accounts and audits public?
- Which public services are tied to grant conditionality rather than local
  self-government discretion?

## Analytical Bottom Line

The FCs see municipal devolution as an unfinished fiscal project. They accept
Part IX-A as the constitutional frame, but their practical language is not
romantic local democracy. It is grants, own-source revenue, property tax,
accounts, audit, SFCs, State transfers, tied components, performance
conditionality, and service benchmarks.

For SevenT4, that is useful because it gives a hard test for every city:

```text
Can the ULB act, or is it only where responsibility is dumped after the State,
parastatals, schemes, and grant conditions have already decided the money?
```

That test should sit beside the ward, Assembly, Parliament, parastatal, and
service-layer maps.
