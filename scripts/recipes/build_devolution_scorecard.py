#!/usr/bin/env python3
"""Devolution scorecard — TWO complementary cuts of the same service map.

1. DEVOLUTION ("who runs it"): of the resident-facing 12th-Schedule services, how many
   does the ELECTED corporation actually run vs a board/SPV/state/private firm?
   (Electricity & police excluded — never municipal functions; shown as context.)

2. DECIDED_BY ("who decided it"): of ALL the city's service arrangements (electricity and
   police INCLUDED), how many were decided/controlled by the elected city vs the state or
   the centre? This is the sharper axis — the point is not which functions are municipal,
   but whether the elected city decided the arrangement at all. A private electricity
   licensee (Torrent/Adani) is not a "devolution failure" (electricity was never the city's
   to lose) but it IS state-decided, not city-decided — so it counts here.

decided_by is derived deterministically from each service's `type`:
   corporation -> city · state_board/state_dept/spv/private -> state · railways -> centre.
(Even an in-house corporation function sits under a STATE-enacted municipal law, so "city"
here means "the elected corporation is the decision-locus", the closest thing to local control.)
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SP = ROOT / "data/institutions/service_providers.json"

# --- cut 1: devolution (who runs it) ---
ELECTED = {"corporation"}
CONTEXT_ONLY = {"electricity", "police"}  # not 12th-Schedule; excluded from cut 1 only

# --- cut 2: decided_by (who decided the arrangement) ---
DECIDER = {"corporation": "city", "state_board": "state", "state_dept": "state",
           "spv": "state", "private": "state", "railways": "centre"}

LABEL = {"water": "Water supply", "sewerage": "Sewerage / sanitation", "electricity": "Electricity",
         "city_bus": "City bus", "brt": "BRT", "metro": "Metro", "roads": "Roads",
         "development_authority": "Urban planning / land", "solid_waste": "Solid waste",
         "street_lighting": "Street lighting", "storm_water": "Storm-water drains",
         "parks": "Parks / open spaces", "public_health": "Public health",
         "police": "Police", "fire": "Fire services"}
TYPELABEL = {"corporation": "your elected corporation", "state_board": "a state board",
             "spv": "a state SPV", "state_dept": "the state govt", "private": "a private firm",
             "railways": "Indian Railways", "na": "—"}


def main():
    data = json.loads(SP.read_text(encoding="utf-8"))
    rows = []
    for cid, svc in data.items():
        if cid.startswith("_"):
            continue
        name = cid.title()
        scored, elected, taken = [], 0, []
        dec = {"city": 0, "state": 0, "centre": 0}
        dtotal = 0
        for k, v in svc.items():
            if k.startswith("_") or not isinstance(v, dict):
                continue
            t = v.get("type")
            if t == "na":
                continue
            # cut 2 — decided_by: ALL real services, including electricity & police
            dec[DECIDER.get(t, "state")] += 1
            dtotal += 1
            # cut 1 — devolution: exclude the non-municipal context functions
            if k in CONTEXT_ONLY:
                continue
            scored.append(k)
            if t in ELECTED:
                elected += 1
            else:
                taken.append((LABEL.get(k, k), v.get("provider", ""), t))
        n = len(scored)
        pct = round(100 * elected / n) if n else 0
        pct_city = round(100 * dec["city"] / dtotal) if dtotal else 0
        rows.append({"id": cid, "name": name, "elected": elected, "n": n, "pct": pct,
                     "taken": taken, "decided": dec, "dtotal": dtotal, "pct_city": pct_city})

    # printed cut 1
    rows.sort(key=lambda r: r["pct"])
    print("CUT 1 — DEVOLUTION: resident-facing services run by the ELECTED corporation")
    print(f"{'city':<14}{'elected/total':>14}{'%':>6}")
    for r in rows:
        print(f"{r['name']:<14}{(str(r['elected'])+'/'+str(r['n'])):>14}{r['pct']:>5}%")

    # printed cut 2
    rows.sort(key=lambda r: r["pct_city"])
    print("\nCUT 2 — DECIDED_BY: of ALL arrangements (incl. electricity/police), share the elected CITY decided")
    print(f"{'city':<14}{'city/total':>12}{'%city':>7}   (state / centre)")
    for r in rows:
        d = r["decided"]
        print(f"{r['name']:<14}{(str(d['city'])+'/'+str(r['dtotal'])):>12}{r['pct_city']:>6}%   ({d['state']} / {d['centre']})")

    # data product
    sc = {r["id"]: {"name": r["name"],
                    "elected": r["elected"], "n": r["n"], "pct": r["pct"],
                    "decided": {**r["decided"], "total": r["dtotal"], "pct_city": r["pct_city"]},
                    "taken": [{"service": lab, "provider": prov, "by": TYPELABEL.get(t, t)} for lab, prov, t in r["taken"]]}
          for r in rows}
    scpath = ROOT / "public/cities/scorecard.json"
    scpath.parent.mkdir(parents=True, exist_ok=True)
    scpath.write_text(json.dumps(sc, ensure_ascii=False, indent=1), encoding="utf-8")

    n_gov = 0
    for r in rows:
        gp = ROOT / f"data/cities/{r['id']}/layers/governance.json"
        if gp.exists():
            g = json.loads(gp.read_text(encoding="utf-8"))
            g["devolution"] = {"elected": r["elected"], "total": r["n"], "pct": r["pct"]}
            g["decided_by"] = {**r["decided"], "total": r["dtotal"], "pct_city": r["pct_city"]}
            gp.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
            n_gov += 1
    print(f"\nwrote {scpath} (both cuts) + injected into {n_gov} governance.json files")


if __name__ == "__main__":
    main()
