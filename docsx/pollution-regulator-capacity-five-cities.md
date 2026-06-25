# Pollution-regulator capacity: the five ready cities

_Acquisition note, 2026-06-16. Pairs the atlas's pollution **burden** layer (CPCB
AQI stations) with the **capacity** of the body meant to act on it — the State
Pollution Control Board / Pollution Control Committee. Data files:
`data/cities/<city>/source/pollution/{sources.json,capacity.json}` and
`data/national/pollution/`. Companion to `docs/the-hollow-regulator.md`._

## The question

A monitoring station measures pollution. It does not regulate it. The body that
grants consents, inspects industry, and enforces standards is the SPCB (or, for
Delhi, the PCC). So the accountability question for every pollution reading is:
**who is left to act on it, and do they have the staff, money, and labs to do so?**

## What we acquired, per city

| City | Board | Hard capacity finding (this pull) | Source role |
|---|---|---|---|
| **Delhi** | DPCC | **218 of 343 posts vacant (~64%) as of 1 Aug 2021** (primary DPCC RTI); **no regional offices**. Sanctioned 184 (2009-10) → 343 (2020-21, +86%) while consents 3,224 → 11,698 (**+263%**) — workload outran a two-thirds-empty board. | DPCC RTI (primary) + CPR |
| **Kolkata** | WBPCB | **309 sanctioned / 122 vacant (~39%) in 2023**; sanctioned *fell* from 328 (2009) while vacancies *rose* from 86. Primary roster: **146 named officers incl. ~69 technical (51 engineers + 18 scientists), Apr 2022**. Receipts **₹154→137→95 cr** vs spend **₹69→47→78 cr** (FY19-21) — ₹85 cr unspent in FY19. | WBPCB RTI/roster (primary) + Rajya Sabha |
| **Bengaluru** | KSPCB | **709 sanctioned / 375 vacant (~53%)** — only 47% filled, vacancies include environmental + scientific officers; board outsourcing to contract hires. | Deccan Herald (board official) |
| **Chennai** | TNPCB | 57% administrative staff (CSE 2009); NGT review: working strength < half of sanctioned. Hard sanctioned/vacant counts still to pull. | CSE / NGT (secondary) |
| **Ahmedabad** | GPCB | No clean sanctioned/vacant table found this pull; GSSSB advertised **105 Senior Scientific Assistant posts (2025)** — an indirect shortfall signal. NGT review: working strength < half of sanctioned. | Recruitment / NGT (indirect) |

## The national frame (secondary baseline, all five cities)

CPR's **The State of India's Pollution Control Boards** (Shibani Ghosh, Annanya
Mahajan, Arunesh Karkun, Sharon Mathew, Prannv Dhawan, Bhargav Krishna; CPR,
2022–2023) — an RTI study of 9 SPCBs + Delhi PCC across the Indo-Gangetic Plain.
Of our five it covers **Delhi and West Bengal directly**; Gujarat, Karnataka and
Tamil Nadu sit outside its frame.

- **≥40%** of posts vacant across the studied boards; up to **84% (Jharkhand)**.
- **7 of 8** SPCBs have ≥40% technical-staff vacancy. In 4 of 7 states an
  environmental engineer has **less than one day** to process a consent
  application; some regional offices issue up to 800 consents per engineer.
- **₹2,893 crore** parked in fixed deposits across the 10 boards (31 Mar 2021)
  while labs and R&D starve; pay is >50% (some >80%) of spend. Without interest
  income, 6 of 10 boards would post a loss.
- Only **11 of 30** statutorily-required annual reports were actually published.
- Rajya Sabha (Feb 2023, MoS Choubey): **~49%** of all SPCB/PCC posts vacant
  nationally. **12 expert committees 1984–2010** recommended strengthening the
  boards; none was implemented.

## Why it matters (the analytic)

The mechanism is the unelected-city mechanism in another face. From the corpus:
Dasgupta & Kapur, *The Political Economy of Bureaucratic Overload* (2020) — 42%
of sanctioned posts vacant, and politicians under-invest in bureaucracy precisely
because there is **no electoral incentive** to staff it. A pollution board has no
voter. And the silence is itself evidence: DPCC reported its *total* 218 vacancies
but pushed CPR to its website for the technical split; WBPCB never gave a clean
technical sheet at all (we reconstructed ~69 technical officers from its public
roster) — Ambedkar's *institutional silence as calculated inaction*. The honest
reading of the air layer is two-sided: here is the pollution, here are the
stations — **and here is the regulator that is 39–64% empty, sitting on tens of
crores of unspent surplus, and cannot act on the reading.**

## Provenance note

The primary records came from the CPR study's released RTI bundle
(`SPCB-RTI-responses-for-upload-270423.zip`). The DPCC vacancy sheet and the
WBPCB finance sheet were scanned images, OCR'd locally (ocrmypdf); the WBPCB
employee roster carried a clean text layer. Originals are held under each city's
`source/pollution/raw/` (gitignored). The DPCC finance sheet OCR'd too poorly for
line items and awaits a manual read.

## Source discipline (per `docsx/source-policy-and-readiness.md`)

- `official_record` (board RTI/annual report, Rajya Sabha answer) is first-class.
- `court_record` (NGT/HC/SC) carries the capacity-criticism orders.
- `secondary_research` (CPR, CSE) frames and cross-checks — it does **not**
  substitute for a board's own figure where one exists.
- `news_corroboration` is a lead, flagged for primary upgrade.
- Missing data is recorded as `not_found` / `partial` with a null value — never
  inferred.

## Open acquisition (next pull)

1. **GPCB & TNPCB** hard sanctioned/filled/vacant — from the board annual reports,
   RTI Section-4, or the **primary state-wise Rajya Sabha annexure** (one source
   fills Gujarat, Karnataka and Tamil Nadu at once).
2. **Budgets** (₹ receipts/expenditure) for all five — GPCB/KSPCB/TNPCB official;
   DPCC/WBPCB exact totals from the CPR finances annexure.
3. **Labs + NABL, inspections, CTE/CTO, notices, prosecutions** per board.
4. **NGT/HC/SC capacity orders** per city; CAQM for Delhi.
5. Upgrade the CPCB/all-India totals in `docs/the-hollow-regulator.md` and the
   Rajya Sabha figures from news to the **primary parliamentary Q&A**.
6. Add the CPR working-paper PDFs to Zotero (not in the partial-recall index).
