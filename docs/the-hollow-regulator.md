# The hollow regulator: who is left to act on the data

A note for the SevenT4 atlas. We pulled **87 real CPCB air-quality monitoring
stations** across our cities (Mumbai 23, Hyderabad 13, Bengaluru/Ahmedabad 8 each,
Chennai/Kolkata 7…), each geocoded with PM2.5/PM10/NO₂ readings. But monitoring is
not regulation. The body meant to *act* on those readings — the Central and State
Pollution Control Boards — is, by its own and independent accounting, hollowed out.
This is the air-and-water analogue of the unelected-city finding: the institution
exists on paper; the capacity to enforce does not.

## The numbers

- **CPCB (central):** of **669 sanctioned posts, 203 are vacant (~30%)** — only 466
  filled.
- **State Pollution Control Boards (national):** of **12,213 sanctioned posts,
  6,165 are vacant (~50%).** Bihar and Jharkhand exceed **75%** vacancy.
- **CPR, *The State of India's Pollution Control Boards*** (working papers, 2022 — a
  deep study of 9 SPCBs + the Delhi PCC): a **minimum 40% vacancy across all posts**;
  **technical-post vacancy up to 84% (Jharkhand)**, over 75% in Bihar and Haryana.
  The consequence is concrete: in Jharkhand, Punjab, UP and Bihar, **engineers have
  less than one day** to inspect, evaluate, and approve each industrial consent
  application. Leadership is part-time and transient — chairpersons and member
  secretaries holding additional charge in other departments, and tenures as short
  as **18 days** (Chhattisgarh chair) and **15 days** (Haryana/UP member secretary).
- **Odisha** (Bhubaneswar's regulator) is the pattern in miniature: sanctioned
  strength rose 220 → 369 (2005–2023), but **actual staff went only 170 → 188** —
  the gap *widened* even as the mandate grew.
- Down To Earth: the boards have been **weakened over 14 years**, with the
  environment ministry lacking a roadmap.

## Why it matters for the atlas

The mechanism is the same one that produces the unelected city. From the corpus:
**Dasgupta & Kapur, *The Political Economy of Bureaucratic Overload* (2020)** —
**42% of sanctioned posts vacant** in surveyed blocks, and politicians *under-invest
in the bureaucracy precisely because there is no electoral incentive* to staff it.
A pollution board has no voter; a starved bus route has no councillor; a suspended
council has no election. Same logic, three faces. And **the audits that catch it
are toothless** (the corpus's CAG-on-Jharkhand-mining item; Garg: "the CAG system is
too centralised to audit these agencies").

So the honest reading of the air layer is two-sided: *here is the pollution, here
are the monitoring stations* — **and here is the regulator that is 30–84% empty and
cannot act on the reading.** Data without an enforcer is the environmental version
of responsibility without power.

## Coverage & gaps (honest)

The CPR 9-state study directly covers only **Kanpur (UP)** and **Kolkata (WB)** of
our cities. National figures cover the rest in aggregate; **per-state SPCB vacancy/
budget for Maharashtra (MPCB), Tamil Nadu (TNPCB), Karnataka (KSPCB), Telangana
(TSPCB), Andhra (APPCB), Gujarat (GPCB), Kerala, Rajasthan** still need pulling
(state-wise tables exist in the parliamentary/CPCB record). Direct WebFetch to
cprindia.org and the gov portals is blocked from this environment; data.gov.in (the
CPCB station API) works. Next step: a per-state SPCB-capacity field on each city's
`governance.json`, so the atlas pairs every monitoring station with its regulator's
fill rate.

## Sources
CPR *Environmentality* (cprindia.org); CPCB (cpcb.nic.in); Mongabay-India (Nov 2022);
Scroll; Deccan Herald; ETV Bharat; Down To Earth; The Tribune; corpus: Dasgupta &
Kapur (2020), Kapur (2020), CAG-toothlessness item, Garg (2006), Samdub (2022) /
Mihir Shah Committee on CWC+CGWB.
