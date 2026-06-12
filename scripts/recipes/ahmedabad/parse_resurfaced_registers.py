#!/usr/bin/env python3
"""Parse AMC's official 'roads resurfaced' registers (2017-18, 2024-25,
2025-26) into a road-level ledger with contractor names, and aggregate to
ward level for geo-spatial analysis.

Input: text dumps made by mine_amc_road_spend.py's sibling step, in
data/cities/ahmedabad/source/budget/roads/resurfaced_registers/*.txt
(source PDFs live in the twenty27 checkout, data/news/roads/).

The three registers use three encodings (EklG-style legacy Gujarati fonts in
2017-18 and 2024-25; Unicode-with-mangled-conjuncts in 2025-26). Zone, ward
and firm names are decoded via explicit dictionaries; the road description
is preserved raw (plus readable for 2025-26).

Outputs (same directory):
  roads_resurfaced_rows.csv    - one row per road segment
  resurfacing_by_ward.geojson  - ward polygons + per-year segment counts,
                                 est. resurfaced area, dominant contractor
  resurfacing_summary.json     - contractor x year x zone totals
"""

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[3] / "data/cities/ahmedabad"
REG = BASE / "source/budget/roads/resurfaced_registers"
WARDS_GEOJSON = BASE / "layers/wards.geojson"

# ---------------------------------------------------------------- zones ---
ZONES = {
    # legacy 2017-18 (no space) and 2024-25 (with space)
    "W•thÍtul": "North", "W•th Ítul": "North",
    "œrûtKÍtul": "South", "œrûtK Ítul": "South",
    "vrùbÍtul": "West", "vrùb Ítul": "West",
    "bægÍtul": "Central", "bæg Ítul": "Central",
    "ÃþJoÍtul": "East", "ÃþJo Ítul": "East", "vqJo Ítul": "East",
    "W.vrùb Ítul": "North-West", "œ.vrùb Ítul": "South-West",
    # legacy 7-zone era abbreviations
    "W.v.Ítul": "North-West", "œ.v.Ítul": "South-West",
    # unicode 2025-26 (conjunct-mangled; multiple manglings of the same word)
    "ઉĂર ઝોન": "North", "દëણ ઝોન": "South", "દ\x87ëણ ઝોન": "South",
    "પિĖમ ઝોન": "West", "મƚય ઝોન": "Central",
    "ǚૂવ ઝોન": "East", "ȶૂવ½ ઝોન": "East",
    "ઉ.પિĖમ ઝોન": "North-West", "દ.પિĖમ ઝોન": "South-West",
    "દ\x87ëણ પિĖમ": "South-West", "ઉĂર પિĖમ": "North-West",
    # 2025-26 'Road Project' department section (citywide; no zone column)
    "રોડ ̆ોȐકટ": "RoadProject",
}
ZONE_RE = re.compile("(" + "|".join(map(re.escape, sorted(ZONES, key=len, reverse=True))) + ")")

# ---------------------------------------------------------------- wards ---
# token (as extracted) -> canonical ward Name in layers/wards.geojson
WARDS = {
    # 2017-18 / 2024-25 legacy
    "lhtuzt": "12 NARODA",
    "vtjze": "30 PALDI", "5tjze": "30 PALDI",
    "lJhkdvwht": "18 NAVRANGPURA", "lJhkdÃþht": "18 NAVRANGPURA",
    "atkœFuzt": "03 CHANDKHEDA", "atk>Fuzt": "03 CHANDKHEDA",
    "htKev": "05 RANIP",
    "bKeldh": "37 MANINAGAR",
    "cnuhtbvwht": "35 BAHERAMPURA", "cnuhtbÃþht": "35 BAHERAMPURA",
    "lthKvwht": "09 NARANPURA", "lthKÃþht": "09 NARANPURA",
    "FtuFht": "44 KHOKHRA",
    "Rmlvwh": "45 ISANPUR", "Rmlvwh ": "45 ISANPUR",
    "JxJt": "47 VATVA",
    "JtmKt": "31 VASNA",
    "œtKejebzt": "36 DANILIMDA",
    "RLîvwhe": "42 INDRAPURI",
    "lJt": "06 NEW WADAJ",       # 'lJt Jtzs' - first token
    "jtkCt": "46 LAMBHA",
    "Mxurzgb": "10 S.P.STADIUM", "Mxuzegb": "10 S.P.STADIUM",
    "mhœthldh": "11 SARDARNAGAR",
    "mtchb<e": "04 SABARMATI",
    "ymthJt": "15 ASARWA",
    "htbtuj": "48 RAMOL HATHIJAN",
    "JMºttj": "41 VASTRAL",
    "rlftuj": "24 NIKOL",
    "CtRvwht": "43 BHAIPURA HATKESHWAR", "CtRÃþht": "43 BHAIPURA HATKESHWAR",
    "dtub<evwh": "38 GOMTIPUR", "dtub<eÃþh": "38 GOMTIPUR",
    "ybhtRJtze": "39 AMRAIWADI",
    "ytuZJ": "40 ODHAV",
    "Jehtxldh": "25 VIRATNAGAR",
    "ctvwldh": "26 BAPUNAGAR", "ctÃþldh": "26 BAPUNAGAR",
    "Xffhctvtldh": "23 THAKKARBAPANAGAR",
    "RLzegtftujtule": "22 INDIA COLONY",
    "fwcuhldh": "14 KUBERNAGR",
    "musvwh": "13 SAIJPUR BOGHA", "musÃþh": "13 SAIJPUR BOGHA",
    "mhmvwh": "27 SARASPUR-RAKHIYAL", "mhmÃþh": "27 SARASPUR-RAKHIYAL",
    "Ftzegt": "28 KHADIA",
    "sbtjvwh": "29 JAMALPUR", "sbtjÃþh": "29 JAMALPUR",
    "œhegtvwh": "21 DARIYAPUR", "œhegtÃþh": "21 DARIYAPUR",
    "NtnÃþh": "17 SHAHPUR", "Ntnvwh": "17 SHAHPUR",
    "Ntnectd": "16 SHAHIBAG",
    "Dtxjtuzegt": "07 GHATLODIA",
    "&j<us": "08 THALTEJ",
    "ctuzfœuJ": "19 BODAKDEV",
    "ò^vwh": "20 JODHPUR", "ò^Ãþh": "20 JODHPUR", "stu^vwh": "20 JODHPUR",
    "atkœjturzgt": "02 CHANDLODIA", "&j<us/ctuzf": "08 THALTEJ",
    "Jusjvwh": "32 VEJALPUR", "JusjÃþh": "32 VEJALPUR",
    "mhFus": "33 SARKHEJ",
    "bf<bvwht": "34 MAKTAMPURA", "bf<bÃþht": "34 MAKTAMPURA",
    "dtuºte": "01 GOTA", "dtu<t": "01 GOTA",
    "atkœjtuzegt": "02 CHANDLODIA",
    # 2025-26 unicode (mangled conjuncts as pypdf renders them)
    "નરોડા": "12 NARODA",
    "પાલડ\x8e": "30 PALDI", "પાલડી": "30 PALDI",
    "ચાંદખેડા": "03 CHANDKHEDA",
    "નવરંગȶુરા": "18 NAVRANGPURA",
    "રાણીપ": "05 RANIP",
    "સરદારનગર": "11 SARDARNAGAR", "સરદારનગરઉĂર": "11 SARDARNAGAR",
    "જમાલȶુર": "29 JAMALPUR",
    "નારણȶુરા": "09 NARANPURA",
    "વાસણા": "31 VASNA",
    "નવા": "06 NEW WADAJ",
    "સરસȶુર": "27 SARASPUR-RAKHIYAL",
    "ખાડ\x8eયા": "28 KHADIA",
    "શાહȶુર": "17 SHAHPUR",
    "સાબરમતી": "04 SABARMATI",
    "ƨટ°ડ\x8eયમ": "10 S.P.STADIUM",
    "ઇ\x8cƛડયાકોલો": "22 INDIA COLONY", "ઇ\x8cƛડયા": "22 INDIA COLONY",
    "ઠïરનગર": "23 THAKKARBAPANAGAR",
    "બાȶુનગર": "26 BAPUNAGAR",
    "અસારવા": "15 ASARWA",
    "ખોખરા": "44 KHOKHRA",
    "મણ\x8eનગર": "37 MANINAGAR", "મણીનગર": "37 MANINAGAR",
    "બહેરામȶુરા": "35 BAHERAMPURA",
    "દાણીલીમડા": "36 DANILIMDA",
    "ઘાટલોડ\x8eયા": "07 GHATLODIA",
    "ગોતા": "01 GOTA",
    "ચાંદલોડ\x8eયા": "02 CHANDLODIA",
    "વેજલȶુર": "32 VEJALPUR",
    "સરખેજ": "33 SARKHEJ",
    "મïમȶુરા": "34 MAKTAMPURA",
}

# ------------------------------------------------------------ contractors ---
# regex -> canonical firm label. ALL these names appear in AMC's own
# published registers; transliterations to be HITL-verified against MCA.
# Matched case-insensitively with whitespace/punctuation collapsed (see firm_of).
# Each pattern is a set of distinctive substrings across the 3 encodings; the
# legacy font maps the same word several ways (m/M, RL£t/EL£t, fLmx/fLMx,
# RLVt[rcÕx/RLV[trcÕx), hence the alternations.
FIRMS = [
    (r"yul\.?me\.?me\.?\s*rl£t|n\.?c\.?c\.?\s*infra", "N.C.C. Infra Pvt Ltd"),
    (r"yt[nr]e?»?t[ne]?\s*rl£tftul|ytr»tn\s*rl£tftul|ashish\s*infra", "Ashish Infracon Pvt Ltd"),
    (r"fu\.?[re]\.?me\.?yuj|k\.?e\.?c\.?l", "K.E.C.L."),
    (r"yuj\.?\s*s\.?\s*ati\^?he|એલ\.?ĥ\.?ચૌધર|એલ\s*\.?\s*s\.?\s*ati|l\.?\s*g\.?\s*chaudhar", "M/s L.G. Chaudhary"),
    (r"yu[5v]u?û?t\s*«tuxu[ff¾]x?|એપેë\s*̆ોટ°ક|અપેë\s*̆ોટ°ક|apex\s*prot", "Apex Protech LLP"),
    (r"[fr]e?mxtul\s*rl£tmx|fe\s*mxtul|ક-?ƨટોન\s*ઇƛ̇ા|કƨટોન\s*ઇƛ̇ા|ક\x8e\s*ƨટોન|keystone", "Keystone Infrastructure Pvt Ltd"),
    (r"yth\.?fu\.?me\.?\s*rlv?t?\[?rcõx|yth\.?fu\.?me\.?\s*rl£tceõ|આર\.ક°\.સી\.?\s*ઇƛ̇ા\s*\x87?બƣ[ડટ]|r\.?k\.?c\.?\s*infra", "R.K.C. Infrabuild Pvt Ltd"),
    (r"lh\s*lthtgk\s*[re]l£t|lhlthtg[t]?k\s*[re]l£t|નર\s*નારાયણ\s*ઇƛ̇ા|નરનારાયણ\s*ઇƛ̇ા|nar\s*narayan", "Nar Narayan Infrastructure Pvt Ltd"),
    (r"btyr?<e?\s*rl£t[¢f]e?yunl|માȿુિત\s*ઇƛ̇ા|માĮિત\s*ઇƛ̇ા|maruti\s*infracreat", "Maruti Infracreation Pvt Ltd"),
    (r"btyr?<e?\s*flm?x\[?[f¾]nl|માĮિત\s*કƛƨ˼કશન|માȿુિત\s*કƛƨ˼કશન|માyિત\s*કƛƨ˼કશન|maruti\s*const", "Maruti Construction"),
    (r"rœnt\s*fl?mx|rœnt\s*rl£t|િદશા\s*કƛƨ˼કશન|disha\s*const", "Disha Construction"),
    (r"yu5uût\s*fl?mx\[?fnl|yu5uût\s*flmx|એપેë\s*કƛƨ˼કશન|apex\s*const", "Apex Construction (verify relation to Apex Protech)"),
    (r"\bhalt\s*(?:f?l?mx|rl£t)|halt\s*fkl?mx", "(?) Construction & Infrastructure (gap-year firm, verify)"),
    (r"rjbj\s*fl[mn]?mx?\[?[¾f]nl|rjbj\s*fkLmx|િવમલ\s*કƛƨ˼કશન|vimal\s*const", "Vimal Construction"),
    (r"vtuhå?gwl\s*rcõzmo|ફોƍȻુ½?ન\s*\x87?બƣડસ|fortune\s*build", "Fortune Builders"),
    (r"rbjl\s*htuz|િમલન\s*રોડ\s*\x87?બƣડટ°ક|milan\s*road\s*build", "Milan Road Buildtech LLP"),
    (r"\x88દƊવીજય\s*કƛƨ˼કશન|ઇƛƊવીજય\s*કƛƨ˼કશન|indravijay\s*const", "Indravijay Construction (verify)"),
    (r"અ\x8aƛવયા\s*કƛƨ˼કશન|અનવયા\s*કƛƨ˼કશન|anavya\s*const", "Anavya Construction (verify)"),
    (r"ઇƛ̇ાકોન\s*એલ\.એલ\.પી", "(?) Infracon LLP (verify prefix)"),
    (r"વĮણ\s*̆ોકોન|ણ\s*̆ોકોન\s*̆ા\.લી|̆ોȐકશન\s*̆ા", "(?)n Prokon Pvt Ltd (verify prefix)"),
    (r"ાƨપેસ\s*̆ા\.લી", "(?) -space Pvt Ltd (verify prefix)"),
    (r"tem\s*rl£tftul", "(?) Infracon variant (verify)"),
]
CONSULTANTS = [
    (r"btNo\s*Ãjtlekd", "Marsh Planning & Engineering Services Pvt Ltd"),
    (r"કƛસલટƛસી", "(consultancy - verify name)"),
]

NUM_RE = re.compile(r"(?<![\d.])(\d{2,4}(?:\.\d{1,2})?)(?![\d])")
DATE_RE = re.compile(r"\b(\d{2}[-.]\d{2}[-.](?:\d{4}|\d{2}))\b")
GUJ_DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")


# ward keys sorted longest-first so e.g. 'lthKvwht' beats 'lJt'
_WARD_KEYS = sorted(WARDS, key=len, reverse=True)
_FILLER = {"ઝોન", "Ítul", "Ðtul", "પિĖમ", "ઉĂર", "દëણ", "દ\x87ëણ", "મƚય"}


def resolve_ward(after):
    """Scan the first few whitespace tokens after the zone for a known ward,
    matching by prefix and ignoring zone-filler words and trailing punctuation."""
    toks = after.split()[:4]
    for raw in toks:
        t = raw.strip(",-/").strip()
        if not t or t in _FILLER:
            continue
        if t in WARDS:
            return t, WARDS[t]
        for key in _WARD_KEYS:
            if t.startswith(key) or key.startswith(t) and len(t) >= 4:
                return raw, WARDS[key]
    return (toks[0] if toks else ""), ""


def firm_of(chunk, bank):
    norm = re.sub(r"\s+", " ", chunk)
    for pat, name in bank:
        if re.search(pat, norm, re.IGNORECASE):
            return name
    return ""


def parse_register(path, year):
    txt = path.read_text()
    txt = txt.translate(GUJ_DIGITS)
    txt = re.sub(r"--- page \d+ ---", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    # rows begin "<serial> <zone-token>"
    starts = [m for m in re.finditer(r"(?:^|\s)(\d{1,3})\s+" + ZONE_RE.pattern, txt)]
    rows = []
    for k, m in enumerate(starts):
        end = starts[k + 1].start() if k + 1 < len(starts) else len(txt)
        chunk = txt[m.start():end]
        serial = int(m.group(1))
        zone = ZONES[m.group(2)]
        after = chunk[m.end() - m.start():].strip()
        ward_token, ward = resolve_ward(after)
        # numbers: first two plausible figures = length(m), width(m)
        nums = [float(n) for n in NUM_RE.findall(after)]
        length = nums[0] if nums else None
        width = nums[1] if len(nums) > 1 else None
        date = (DATE_RE.search(after) or [None]) and (DATE_RE.search(after).group(1) if DATE_RE.search(after) else "")
        contractor = firm_of(chunk, FIRMS)
        consultant = firm_of(chunk, CONSULTANTS)
        desc = after[:240]
        rows.append({
            "register_year": year, "serial": serial, "zone": zone,
            "ward_token": ward_token, "ward": ward,
            "length_m": length, "width_m": width, "dlp_or_completion_date": date,
            "contractor": contractor, "consultant": consultant,
            "road_desc_raw": desc,
        })
    return rows


def main():
    all_rows = []
    for fname, year in [("resurfaced_2017-18.txt", "2017-18"),
                        ("resurfaced_2018-19.txt", "2018-19"),
                        ("resurfaced_2019-20.txt", "2019-20"),
                        ("resurfaced_2020-21.txt", "2020-21"),
                        ("resurfaced_2022-23.txt", "2022-23"),
                        ("resurfaced_2024-25.txt", "2024-25"),
                        ("resurfaced_2025-26.txt", "2025-26")]:
        rows = parse_register(REG / fname, year)
        ok_ward = sum(1 for r in rows if r["ward"])
        ok_firm = sum(1 for r in rows if r["contractor"])
        print(f"{year}: {len(rows)} rows | ward mapped {ok_ward} | contractor mapped {ok_firm}")
        all_rows.extend(rows)

    with open(REG / "roads_resurfaced_rows.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)

    # ---- ward aggregation ----
    agg = defaultdict(lambda: defaultdict(lambda: {
        "segments": 0, "length_m": 0.0, "area_m2": 0.0, "contractors": Counter()}))
    for r in all_rows:
        if not r["ward"]:
            continue
        a = agg[r["ward"]][r["register_year"]]
        a["segments"] += 1
        if r["length_m"]:
            a["length_m"] += r["length_m"]
            if r["width_m"] and r["width_m"] < 61:  # sanity: width <= 200ft
                a["area_m2"] += r["length_m"] * r["width_m"]
        if r["contractor"]:
            a["contractors"][r["contractor"]] += 1

    wards = json.loads(WARDS_GEOJSON.read_text())
    for feat in wards["features"]:
        name = feat["properties"]["Name"]
        for year in ("2017-18", "2018-19", "2019-20", "2020-21", "2022-23", "2024-25", "2025-26"):
            a = agg.get(name, {}).get(year)
            suffix = year.replace("-", "_")
            feat["properties"][f"resurf_{suffix}_segments"] = a["segments"] if a else 0
            feat["properties"][f"resurf_{suffix}_km"] = round(a["length_m"] / 1000, 2) if a else 0
            feat["properties"][f"resurf_{suffix}_top_contractor"] = (
                a["contractors"].most_common(1)[0][0] if a and a["contractors"] else "")
    (REG / "resurfacing_by_ward.geojson").write_text(json.dumps(wards, ensure_ascii=False))

    summary = {
        "contractor_totals": Counter(r["contractor"] for r in all_rows if r["contractor"]),
        "by_year_zone": defaultdict(Counter),
        "rows_total": len(all_rows),
        "rows_ward_mapped": sum(1 for r in all_rows if r["ward"]),
        "rows_contractor_mapped": sum(1 for r in all_rows if r["contractor"]),
    }
    for r in all_rows:
        summary["by_year_zone"][r["register_year"]][r["zone"]] += 1
    summary["contractor_totals"] = dict(summary["contractor_totals"].most_common())
    summary["by_year_zone"] = {k: dict(v) for k, v in summary["by_year_zone"].items()}
    (REG / "resurfacing_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary["contractor_totals"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
