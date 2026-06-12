# SevenT4 Gantt Plan

_Status: working schedule. Last updated: 2026-06-08._

This Gantt chart is tied to [the roadmap](roadmap.md). It begins with the
current research and documentation pass, then moves into Ahmedabad hardening,
the reusable governance contract, Delhi NCR special modeling, and national
atlas pilots.

```mermaid
gantt
    title SevenT4 Operational Roadmap
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    tickInterval 1week

    section Doctrine And Research
    Mission and vision document              :done, doc001, 2026-06-08, 2d
    Roadmap and Gantt alignment              :done, doc002, 2026-06-08, 2d
    Ambedkar, CAD, decentralization source index :ref001, 2026-06-10, 12d
    MoHUA, RBI, Planning Commission, WB, IMF corpus :ref002, 2026-06-15, 12d
    Part IXA and municipal-law source spine  :ref003, 2026-06-22, 10d

    section Ahmedabad Baseline
    Ward/AC/PC QA pass                       :qaahd001, 2026-06-12, 7d
    Fix Ellis Bridge AC geometry decision    :bugahd001, 2026-06-14, 5d
    Service-layer freshness audit            :dataahd001, 2026-06-18, 8d
    Representative crosswalk validation      :dataahd002, 2026-06-24, 7d
    AMC budget ingest and parser plan        :budahd001, 2026-06-27, 10d

    section Governance Data Contract
    City-region config schema                :city001, 2026-07-01, 10d
    Authority and finance-channel model      :city002, 2026-07-08, 10d
    Layer provenance model                   :city003, 2026-07-10, 7d
    State-first governance fields            :city004, 2026-07-12, 7d
    Official vs agglomeration boundary model :city005, 2026-07-14, 8d
    Social geography source matrix           :datasoc001, 2026-07-14, 12d

    section Accountability UX
    Who-answers panel prototype              :featacc001, 2026-07-15, 12d
    Devolution-gap labels                    :featacc002, 2026-07-22, 10d
    Boundary explainer component             :featexp001, 2026-07-28, 8d
    Ward-level demand note generator         :featact001, 2026-08-01, 12d
    Print/share public action view           :featact002, 2026-08-10, 10d

    section Delhi NCR Special Model
    NCR constitutional/governance model note :cityncr001, 2026-07-22, 12d
    Delhi NCT/MCD/NDMC/DCB/DDA source inventory :cityncr002, 2026-08-01, 12d
    NCR law/finance/politics/society explainer :cityncr005, 2026-08-05, 10d
    Gurugram Haryana sub-atlas scope         :cityncr003, 2026-08-08, 10d
    Noida and Greater Noida UP sub-atlas scope :cityncr004, 2026-08-14, 10d

    section National Atlas Pilots
    Mumbai/MMR governance model              :citymmr001, 2026-08-05, 12d
    Bengaluru governance model               :cityblr001, 2026-08-12, 10d
    GBA/BBMP/BMLTA/NUTP dossier              :cityblr002, 2026-08-16, 12d
    Hyderabad and Chennai scoping            :citysouth001, 2026-08-20, 12d
    Kolkata, Pune, Surat, Jaipur scoping     :cityrest001, 2026-09-01, 15d

    section Public Release
    Ahmedabad public accountability release  :milestone, relahd001, 2026-08-21, 1d
    Delhi NCR model review                   :milestone, relncr001, 2026-08-31, 1d
    National atlas phase-one review          :milestone, relnat001, 2026-09-18, 1d
```

## Roadmap Mapping

- `DOC-001`, `DOC-002`: mission, roadmap, and Gantt documents.
- `REF-001`: Ambedkar, CAD, decentralization, federalism, and local-state
  source spine.
- `REF-002`: MoHUA, RBI, Planning Commission, NITI Aayog, Finance Commission,
  World Bank, and IMF policy-finance corpus.
- `REF-003`: Part IXA and municipal-law source spine.
- `BUG-AHD-001`, `QA-AHD-001`: Ahmedabad geometry and crosswalk reliability.
- `DATA-AHD-001`, `DATA-AHD-002`, `BUD-AHD-001`: Ahmedabad provenance,
  representative, service, and finance layers.
- `CITY-001` to `CITY-003`: reusable city-region contract.
- `CITY-004`: state-first urban governance fields for state municipal law,
  state urban departments, and devolution orders.
- `CITY-005`: official data boundary, urban agglomeration boundary, and
  source-warning model.
- `FEAT-ACC-001`, `FEAT-ACC-002`, `FEAT-ACT-001`, `FEAT-ACT-002`:
  accountability and public-action surfaces.
- `CITY-NCR-001` to `CITY-NCR-004`: special Delhi NCR model, including Delhi
  NCT, Union-controlled institutions, municipal bodies, Gurugram, Noida, and
  Greater Noida.
- `CITY-NCR-005`: NCR law, finance, politics, culture, economy, and society
  explainer.
- `FEAT-EXP-001`: public website explainer for official limits vs lived
  agglomeration.
- `CITY-MMR-001`, `CITY-BLR-001`, `CITY-SOUTH-001`, `CITY-REST-001`: national
  atlas expansion.
- `CITY-BLR-002`, `CITY-BLR-003`: Greater Bengaluru governance and transport
  authority dossier, including GBA, BBMP transition, BMLTA, NUTP 2006, and UMTA.
