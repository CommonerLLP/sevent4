# Construction Worker And BOCW Feature Scope

Status: side-track scoping note for a future engineering feature.

This scope extends the atlas's `who labours` axis from sanitation and contract
work into construction labour. It is not a UI/UX build. The first deliverable
should be a data and provenance layer that can later support city pages,
ward/contract overlays, and accountability findings.

## Verified Report Source

The immediate research trigger is:

> *Beyond Barriers and Biases: Engendering the Indian Construction Industry*.

Verified source trail:

- ILO news page: `https://www.ilo.org/resource/news/creating-opportunities-women-construction-india-call-action`
- Report PDF: `https://womenleadershipcenter.in/img/publications/reports/Engendering-the-Indian-construction-industry-report-1.pdf`
- Avtar page: `https://www.avtarcc.com/engendering-the-indian-construction-industry/`

Source metadata captured from the PDF and ILO page:

- title: *Beyond Barriers and Biases: Engendering the Indian Construction
  Industry*;
- publisher/copyright holder: Confederation of Indian Industry (CII), 2024;
- institutional trail: report outcome by Employers' Federation of India (EFI)
  and CII in collaboration with the International Labour Organization (ILO);
- research design and implementation partner: Avtar, Chennai;
- ILO launch/news trail: released at CII Centre for Women Leadership's Inclusion
  and Competitiveness Summit in Mumbai on 30 April 2025; ILO news page dated 7
  May 2025;
- PDF length: 54 pages;
- rights: all rights reserved; record URL/hash metadata, but do not vendor the
  PDF into the repo without permission;
- methods: desk review, surveys, focus group discussions, and company
  good-practice profiling;
- survey sample: 345 construction-industry professionals, including 100 women
  and 245 men, plus 62 women STEM students;
- qualitative sample: 11 virtual FGDs with 64 women across student, early
  career, mid-career, and senior cohorts;
- sample caveat: snowball sampling through CII/Avtar networks; strongest for
  organized construction/STEM and enterprise practices, weaker for informal
  worksite and BOCW-delivery claims.

The report should be treated as a conceptual and sector-framing source for
gender, informality, skills, site conditions, and institutional barriers in
construction work. It should not substitute for official city/state worker,
BOCW, labour department, municipal-contract, union, field, RTI, CAG, court, or
parliamentary/assembly records.

Important BOCW caveat: text extraction did not surface substantive references
to BOCW, cess, or construction welfare boards. For this atlas feature, the ILO
report can structure the gendered-barriers schema, but official board and labour
department sources must carry registration, cess, benefits, staffing, and
grievance facts.

Sector facts from the ILO page and report background that can seed the feature
brief, with attribution:

- construction accounts for about 9 per cent of India's GDP;
- the sector is reported by the ILO page as employing approximately 71 million
  people; the PDF also cites a 57 million employment base in its background;
- women are about 12 per cent of the construction workforce in the ILO page's
  summary;
- the PDF background reports that 96.9 per cent of women employed in
  construction work as casual labour under PLFS 2022/23;
- the ILO page reports only 2 per cent of women in the sector occupy senior
  management roles;
- the PDF background reports only 1.4 per cent of women are in technical and
  managerial roles such as architects, civil engineers, and supervisors;
- the ILO page reports an average daily wage of INR 412 for casual workers and
  a 30-40 per cent informal-sector gender wage gap, citing the report's source
  base.

## Five-City Scope

The feature should initially cover only the five selectable cities:

| City | State / Board Target | Municipal/City Target |
|---|---|---|
| Ahmedabad | Gujarat BOCW Welfare Board; Gujarat Labour Department | AMC public works, building permissions, roads, housing, metro and infrastructure contracts |
| Bengaluru | Karnataka Building and Other Construction Workers Welfare Board; Karnataka Labour Department | BBMP/GBA works, BDA/BMRCL/BWSSB/BMTC infrastructure contracts |
| Chennai | Tamil Nadu Construction Workers Welfare Board; Tamil Nadu Labour Welfare and Skill Development Department | GCC works, CMWSSB, CMDA/CUMTA, metro/flood/drainage contracts |
| Delhi | Delhi Building and Other Construction Workers Welfare Board; GNCTD Labour Department | MCD, NDMC, DCB, DDA, PWD, DMRC, NCR/CAQM-adjacent infrastructure where relevant |
| Kolkata | West Bengal BOCW Welfare Board; West Bengal Labour Department | KMC, KMDA/KMWSA/KMRC, drainage, markets, rail/metro-adjacent works |

Do not expand to the other city folders until their atlas readiness catches up.

## Core Question

For each city, the feature should answer:

> Who builds the city, who registers them, who collects cess in their name, who
> spends it, and which workers remain invisible to the welfare state?

This should be modelled as four linked surfaces:

- worker population and composition;
- worksite and contractor chain;
- BOCW registration, cess, benefits, and grievance delivery;
- gendered barriers and site conditions.

## Evidence Tracks

### Worker Population

Minimum fields:

- city;
- state;
- year;
- estimate_type: official count, survey estimate, census/PLFS/NSS estimate, union/NGO estimate;
- total construction workers;
- women construction workers;
- migrant workers;
- registered BOCW workers;
- active registrations;
- renewals pending;
- worker age bands if available;
- caste/community fields only where official and ethically publishable;
- source_url;
- source_path;
- retrieval_date;
- confidence.

Primary sources:

- state BOCW board dashboards and annual reports;
- labour department annual reports;
- e-Shram aggregate tables where geography is usable;
- Census worker classification;
- PLFS/NSS construction employment estimates;
- Parliamentary/Assembly questions;
- CAG audits;
- RTI/manual collection where public tables are absent.

### Worksites And Contract Chain

Minimum fields:

- project_id;
- city;
- ward/zone where locatable;
- owning authority;
- implementing agency;
- contractor;
- subcontractor if disclosed;
- project type: road, bridge, housing, metro, drain, sewer, water, public building, redevelopment;
- estimated project value;
- labour cess assessed;
- labour cess paid;
- safety officer requirement;
- accident/death/injury records if disclosed;
- source and confidence.

Potential city joins:

- municipal work orders;
- public works contracts;
- building-permission records;
- RERA project lists;
- metro/water/sewer/drainage project packages;
- CAG audit samples;
- court and labour-inspector records.

### BOCW Welfare Delivery

Minimum fields:

- board;
- financial year;
- opening balance;
- cess collected;
- interest/income;
- expenditure;
- closing balance;
- expenditure share;
- registered workers;
- beneficiaries by scheme;
- benefit type: education, maternity, death, injury, pension, housing, tools, health, skill training;
- applications received;
- applications approved;
- applications rejected;
- pending applications;
- grievance count and disposal where available;
- board staffing: sanctioned, filled, vacant;
- labour inspector staffing where available.

Analytical ratios:

- benefit expenditure per registered worker;
- expenditure as share of available funds;
- active registration as share of estimated worker base;
- women beneficiary share;
- pending renewal share;
- vacancy rate in board/labour machinery;
- inspection rate per active construction project where data permits.

### Gendered Barriers And Site Conditions

The ILO report should inform the conceptual schema here, while official/local
data should drive publishable city claims.

Candidate fields:

- women registered under BOCW;
- women receiving benefits;
- maternity benefit claims and approvals;
- creche availability at worksites;
- toilet and drinking-water provision at worksites;
- PPE availability by gender where inspected;
- skill-training participation by gender;
- wage category and task segregation where survey data exists;
- harassment/grievance mechanisms;
- contractor/broker dependence;
- documentation barriers for migrants and women workers;
- bank/account/mobile/Aadhaar dependency in benefit access.

Report-derived barrier taxonomy:

- entry barriers: stereotypes about physical capacity, family resistance,
  limited visibility of STEM/construction pathways, campus-placement bias;
- retention barriers: supervisor support gaps, biased appraisal, peer-group
  exclusion, remote sites, late hours, long commutes, and unpaid care load;
- site infrastructure barriers: toilets, changing rooms, drinking water, safe
  transport, lighting, crèches, and gender-appropriate PPE/safety gear;
- mobility barriers: lack of women mentors, thin role-model pipeline,
  assignment away from core project/site roles, and weak sponsorship into
  leadership;
- protection barriers: harassment reporting, responsive internal processes,
  inspection capacity, and the gap between formal policies and field practice.

Report-to-data translation:

- use the report to define the questions and field names;
- use official inspections, board records, labour department records, municipal
  contract records, field surveys, unions, and RTI to populate city facts;
- keep national/sector report claims separate from city-specific measurements;
- label unsupported fields explicitly as missing rather than inferring that a
  condition is absent.

## Data Products

Recommended first engineering products:

1. `data/labour/construction/source_inventory.csv`
   - one row per source, across the five cities.
   - include `source_role` values such as `sector_frame`, `official_record`,
     `survey`, `audit`, `court_record`, `rti`, and `secondary_research`.

2. `data/labour/construction/bocw_board_finance.csv`
   - one row per board-year.

3. `data/labour/construction/bocw_registration.csv`
   - one row per board/city/year/gender/status where available.

4. `data/labour/construction/bocw_benefits.csv`
   - one row per board/year/scheme/gender where available.

5. `data/labour/construction/contract_project_links.csv`
   - one row per public construction project or sampled contract.

6. `data/labour/construction/source_manifest.json`
   - attribution, retrieval date, hashes, licences, and confidence.
   - include the ILO/CII/EFI/Avtar report as `sector_frame`, not as a BOCW
     official source.

Public-layer outputs should wait until source coverage is strong enough. The
first useful public output is likely a city-level table, not a map.

## Feature Contract

Add a future `construction_labour` feature only when it can expose:

- the city/state board responsible;
- at least one official BOCW finance or registration source;
- at least one worker-population denominator;
- source confidence labels;
- absence semantics: missing data, not applicable, unavailable, or not yet acquired.

Do not imply that unregistered means absent. In this domain, non-registration is
itself often the core finding.

## Engineering Plan

Phase 1: source inventory.

- Record the ILO/CII/EFI/Avtar report metadata, URL, page count, rights status,
  and hash; do not vendor the PDF into the repo unless permission/licence is
  clear.
- Inventory the five state/UT BOCW boards and labour departments.
- Identify annual reports, dashboards, CAG audits, assembly questions, and RTI
  targets.
- Add tests that assert source rows exist for all five cities.

Phase 2: board finance and registration.

- Parse board-level finance: cess collected, funds available, spend, balances.
- Parse registered workers and beneficiary counts.
- Build confidence labels for city-level versus state-level evidence.

Phase 3: municipal contract joins.

- Link worker welfare to construction activity through municipal and parastatal
  project lists.
- Start with one city where contract data is already strong, likely Ahmedabad or
  Bengaluru.

Phase 4: gendered barriers.

- Use the ILO report to define the interpretive schema.
- Fill city/state values only from official, survey, RTI, union, or credible
  field sources.
- Keep report-derived claims separate from measured city facts.
- Add validation that prevents `sector_frame` sources from satisfying required
  BOCW finance, registration, or benefit evidence.

## Open Questions

- The ILO/CII/EFI/Avtar report is sector-level and does not provide the five
  city-level evidence needed for atlas claims.
- The extracted report text does not materially cover BOCW boards, cess, or
  welfare delivery; those must come from official board/labour sources.
- Are gender-disaggregated BOCW registrations available for all five states?
- Can city-level construction-worker estimates be derived responsibly from
  PLFS/NSS/Census, or should early releases stay state-level?
- Which public works datasets disclose enough contractor/project value detail to
  estimate BOCW cess obligations?
- Can RERA project data provide a private-construction denominator without
  overclaiming worker counts?

## Relationship To Existing Atlas Work

This feature should connect to:

- `docs/the-double-extraction.md` for the labour/rent frame;
- `docs/the-contracted-death.md` for the contract-liability mechanism;
- `scripts/recipes/scope_opencity_for_atlas.py` for the existing `labours`
  source-axis classification;
- city finance/works datasets for contract joins;
- environmental-regulator capacity work only where construction, pollution, and
  labour enforcement overlap.

The core discipline is the same as the pollution-control-board work: pair the
measured burden with the institution that is supposed to act, then ask whether
the institution has the staff, money, and public trail to do so.
