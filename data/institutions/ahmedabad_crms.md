# The complaint desk: what AMC's CRMS actually shows you (and what it doesn't)

Ahmedabad Municipal Corporation runs a real, public complaint system: the **Comprehensive
Complaint Redressal System (CCRS)**, branded *AMC Seva 311*, reachable on the **155303** helpline
(toll-free 1800-233-2330), the **amccrs.com** web portal, the **AMC CCRS** mobile app, WhatsApp
(+91 7567855303), SMS, IVR, missed-call and Twitter. Unlike the prior blocked scrape, the portal is
live and partly legible: `ComplaintRegistration.aspx` returned HTTP 200 to a browser-UA curl, and its
public registration form **enumerates the full complaint taxonomy and all 47 wards** — so the
categories below are Tier A, lifted directly from the official form, not invented.

## What CRMS data is actually published (honestly)

**Available (Tier A):** the complaint-category taxonomy; the 47-ward routing list; the registration
channels; a public status-tracker (look up a complaint by number/phone); and a **live dashboard**
(`Dashb.aspx`) that shows aggregate counters. On the snapshot of 2026-06-09 it read **355 registered /
168 closed / 2 reopened today**, and **24,376 registered / 19,973 closed / 136 reopened this month** —
recorded only to prove the dashboard publishes real numbers, **not** as a rate. These are point-in-time
counters; do not extrapolate.

**NOT available — the gap.** There is **no downloadable or historical dataset**: no CSV, no API, no
data.gov.in feed, no per-ward or per-department time series, no annual complaint report on
ahmedabadcity.gov.in, and **no verifiable closed-within-SLA percentage**. The dashboard has widgets
labelled *Within-SLA vs Beyond-SLA*, *Zone-wise*, *Ward-wise*, *Department-wise* and *Top-10 longest-open*
— but they are JS-rendered, non-exportable, and reset to "today / this month." You can see a running
total; you cannot see **which wards are starved or how long the poor wait versus the rich.** The
taxonomy and helpline are open; the accountability numbers are effectively closed.

## The taxonomy — and where your complaint goes

The roughly 90 registration options collapse to ~22 service families, **every one of which routes to an
AMC department**: Water, Drainage, Roads, Streetlight, SWM/garbage, Health (malaria fogging, food
safety, UHCs), Cattle Nuisance Control (stray cows/dogs), Gardens, Crematoria, Estate/encroachment,
unsafe-building demolition, Fire, Property-tax follow-up, Smart/public toilets, libraries, gyms and
pools, the Riverfront and Kankaria lakefronts, ICDS food, shelters. (Full mapping in
`ahmedabad_crms.json`.)

## Your complaint routes to a body you didn't elect — by what's *missing*

The sharp finding is **negative space**. CCRS lets you file only against AMC. The civic functions AMC has
**carved out to unelected bodies have no complaint category at all** — so the system both routes you only
to the elected city *and* renders the unelected city invisible by omission. There is a *Streetlight* box
(the lamp is AMC) but **no electricity box — power is Torrent Power, a private DISCOM**. There is a thin
*Town Planning – Other* stub, but the master plan, TP-schemes and land-use belong to **AUDA, the
state-appointed development authority**. There is no **bus/BRTS** category (AMTS / Janmarg), no
**slum-redevelopment** category (state), and traffic enforcement is **state police**. This maps onto
`function_control_matrix.md`: the elected corporation fully holds only **9 of the Constitution's 18
functions**, and the complaint desk quietly confirms it — you can complain loudly about the broom, and
not at all about the pipes-of-power, the plan, the land, or the bus. The grievance channel is shaped
exactly like the power map: it lets the citizen petition only the half of the city they still elect.
