---
repo: sevent4
cockpit: docs/STATUS.md
roadmap: docs/roadmap.md
unit_of_progress: city builds — each rostered city taken scaffolded → console-built → cut-complete (ward+AC+PC) → sourced → published on GitHub Pages
---

_sevent4's PM profile, read by the generic `/pm` engine. sevent4 is the PUBLIC municipal-power
atlas (GitHub Pages), not a campaign evidence-funnel — so /pm measures city builds, not facts.
Mission outcomes O1–O7 live in `docs/roadmap.md`._

## Stage discipline
**rostered ≠ scaffolded ≠ console-built ≠ cut-complete ≠ sourced ≠ published.**
"cut-complete" = all three boundary layers exist AND carry features, verified this run.
Data-trust tiers: AMC/GTFS/ECI/Census authoritative; OSM unfit for authoritative claims.

## 1. Count commands (exact, auditable)
```
python3 -c "import json;print('rostered:',len(json.load(open('public/cities/registry.json'))))"
for d in data/cities/*/; do echo "$(basename $d): $(ls $d/layers/*.geojson 2>/dev/null|wc -l|tr -d ' ') layers"; done
ls -d public/cities/*/index.html 2>/dev/null | wc -l   # consoles built
```

## 1a. Integrity check — the CUT SPINE (load-bearing)
Every city must be sliceable by ward / assembly (AC) / parliament (PC). A missing cut is a break:
```
for c in $(ls data/cities); do
  w=$([ -s data/cities/$c/layers/wards.geojson ] && echo Y || echo -)
  a=$([ -s data/cities/$c/layers/acs.geojson ] && echo Y || echo -)
  p=$([ -s data/cities/$c/layers/pcs.geojson ] && echo Y || echo -)
  echo "$c ward:$w ac:$a pc:$p"
done
```
Produce the **cut-gap list**; where OpenCity lacks a cut, name the fallback (ECI/DataMeet/Census)
from `docs/opencity-atlas-scope.md`.

## 1b. Provenance audit (public-repo obligation)
sevent4 is public — every ingested layer must cite its source. For each city, confirm
`source/**/sources.json` + `CREDITS.md` cover the built layers; a console layer with no provenance
row is a **debt**. List them (cite _publisher → source-portal → sevent4 (processed)_).

## 2. Freshness gates
Per city's key layers: boundary vintage current (delimitation year)? finance/spend the latest year
(cross-check the OpenCity catalogue `last_modified`)? `governance.json` officer/council status still
in post? Produce the **stale-layer list**. 🔴 on an annual budget = urgent; on a decadal
delimitation = structural.

## 3. Live-ops check
```
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -iE 'python|http' || echo "no preview servers"
ls -d /Volumes/m1-storage >/dev/null 2>&1 && echo "m1-storage mounted" || echo "m1-storage ABSENT"
```
A stale `python -m http.server` left running is the zombie-daemon analogue — kill or flag.
Raw OpenCity archives live on `m1-storage`; in-repo `data/sources/` is gitignored.

## 4. Roadmap source + gates
`docs/roadmap.md` — mission outcomes O1 jurisdiction · O2 devolution · O3 social geography ·
O4 comparative · O5 street-ready · O6 state-first · O7 agglomeration. Mark phase outputs
met/partial/unmet against artefacts. Phase-complete is Aakash's verdict, not /pm's.

## 5. Report template
```
## /pm — SevenT4 — [date]
Cities: N rostered · M consoles built · K cut-complete (ward+AC+PC)
Cut gaps: [city → missing AC/PC → fallback source]
Provenance debt: [city/layer with no sources.json]
Stale layers: [city/layer → newer vintage exists]  ← refresh priorities
Live ops: [:PORT city preview | none] · m1-storage [mounted/absent]
Roadmap: Phase X — [outputs met / unmet]
Commit gap: [N untracked on <branch> → staged-commit recommendation]
On track? [honest yes/no + the one thing that decides it]
```

## Discipline (repo-specific)
- **Public-repo OPSEC:** `notes/`, `memory/`, `WORKING.md`, agent configs, statute PDFs, `.secrets/`
  gitignored; `data/cities/**` IS tracked (the atlas is public); `data/sources/` is NOT (working index).
  Never stage internal-brain files.
- **Defamation discipline:** structural/concentration claims are provable; named-individual partisan
  claims stay tier-B unless documented (the road-money template).
- Report against spec, not effort; reserve "done" for verified, published work.
