#!/usr/bin/env python3
"""Geocode Chennai public libraries via Nominatim and assign to wards.

Strategy: the 'Library Name' field embeds a noisy, OCR-garbled address. Full-string
geocoding fails on Nominatim, so we extract a clean locality token + 6-digit pincode
and try a cascade of queries, recording which tier hit (= geocode confidence):
  tier 'locality_pin' > 'locality' > 'pincode' (pincode = centroid only, low conf).
Failures are reported, never fabricated.
"""
import csv, json, re, time, urllib.parse, urllib.request, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "source/corporation/facilities/chennai_libraries.csv")
WARDS = os.path.join(ROOT, "layers/wards.geojson")
OUT_GEO = os.path.join(ROOT, "layers/libraries.geojson")
CACHE = os.path.join(ROOT, "geocode_cache.json")
UA = "sevent4-research/1.0"

# Known Chennai localities (lowercase) to extract from garbled OCR address strings.
LOCALITIES = [
    "egmore","kotturpuram","ashok nagar","alwarpet","ayanavaram","shenoy nagar",
    "adayar","adyar","agaram","villivakkam","triplicane","vyasarpadi","old washermenpet",
    "washermenpet","velachery","velacheri","thiruvanmiyur","k.k. nagar","kk nagar",
    "erukancheri","saligramam","anna nagar","chetput","royapettah","royapetah","guindy",
    "kodambakkam","pudupet","virugambakkam","saidapet","sydapet","west mambalam","mambalam",
    "perambur","teynampet","kolathur","nandanam","mylapore","chindadaripet","chintadripet",
    "nungambakkam","kilpauk","t.nagar","t. nagar","purasaiwakkam","purasawalkam","kannigapuram",
    "choolaimedu","choolamedu","arumbakkam","arambakkam","george town","sowcarpet","royapuram",
    "tondiarpet","thandaiyarpet","sembiyam","madhavaram","choolai","pattinapakkam","raja annamalai puram",
    "santhome","mandaveli","indira nagar","tharamani","vannarpettai","vannarapettai","kosapet",
    "vadapalani","kodungaiyar","saligramam","kannigapuram","new washermenpet","korukkupet",
    "muthialpet","harbour","seven wells","sevenwells","ayanpuram","gandhi nagar adyar","gandhi nagar",
    "kotturpuram","koyambedu","west mambalam","vepery","periamet","periya medu","sembium",
    "kasimedu","thiruvottiyur","thiru vi ka nagar","tondiarpet","mmda colony","vinayagapuram",
    "purasawalkam","kannigapuram","patel nagar","sembium",
]

# OCR-garbled tokens -> canonical locality that Nominatim resolves.
OCR_FIX = {
    "puraisai wakkam": "purasawalkam",
    "puraisaiwakkam": "purasawalkam",
    "purasaiwakkam": "purasawalkam",
    "rayaporam": "royapuram",
    "royapruram": "royapuram",
    "namagvapettai": "vannarpettai",
    "patthlam": "perambur",  # 'pattalam' area -> nearest resolvable
    "new washermenpet": "washermenpet",
}

PIN_RE = re.compile(r"6000?(\d{3})")  # handles 600xxx and OCR'd 6000xxx

def clean_pin(addr):
    m = PIN_RE.search(addr.replace(" ", ""))
    if not m:
        return None
    p = "600" + m.group(1)
    return p if p.isdigit and len(p) == 6 else None

def find_locality(addr):
    a = addr.lower
    hits = [loc for loc in LOCALITIES if loc in a]
    if not hits:
        return None
    return max(hits, key=len)  # longest match = most specific

def load_cache:
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    return {}

def save_cache(c):
    json.dump(c, open(CACHE, "w"), indent=1)

def nominatim(q, cache):
    if q in cache:
        return cache[q]
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"format": "json", "limit": 1, "q": q})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception as e:
        data = []
    time.sleep(1.1)  # rate limit ~1 req/sec
    res = None
    if data:
        d = data[0]
        res = {"lat": float(d["lat"]), "lon": float(d["lon"]),
               "importance": d.get("importance"), "display_name": d.get("display_name")}
    cache[q] = res
    save_cache(cache)
    return res

def geocode(addr, cache):
    loc = find_locality(addr)
    pin = clean_pin(addr)
    attempts = []
    if loc and pin:
        attempts.append(("locality_pin", f"{loc}, {pin}, Chennai, Tamil Nadu, India"))
    if loc:
        attempts.append(("locality", f"{loc}, Chennai, Tamil Nadu, India"))
    if pin:
        attempts.append(("pincode", f"{pin}, Chennai, Tamil Nadu, India"))
    for tier, q in attempts:
        r = nominatim(q, cache)
        if r:
            r["confidence"] = tier
            r["query"] = q
            r["locality"] = loc
            r["pincode"] = pin
            return r
    return None

# ---- ray casting point in polygon ----
def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def point_in_feature(x, y, geom):
    t = geom["type"]
    polys = geom["coordinates"] if t == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        if not poly:
            continue
        if point_in_ring(x, y, poly[0]):
            if not any(point_in_ring(x, y, hole) for hole in poly[1:]):
                return True
    return False

def assign_ward(lon, lat, wards):
    for f in wards["features"]:
        if point_in_feature(lon, lat, f["geometry"]):
            return f["properties"]["ward_no"], f["properties"].get("Name")
    return None, None

def main:
    cache = load_cache
    wards = json.load(open(WARDS))
    rows = list(csv.DictReader(open(SRC)))
    features = []
    stats = {"total": 0, "geocoded": 0, "failed": 0, "by_tier": {}, "fail_rows": []}
    for row in rows:
        name = (row.get("Library Name") or "").strip
        if not name:
            continue
        stats["total"] += 1
        sl = row.get("Sl No")
        r = geocode(name, cache)
        if not r:
            stats["failed"] += 1
            stats["fail_rows"].append(f"#{sl}: {name[:60]}")
            continue
        stats["geocoded"] += 1
        stats["by_tier"][r["confidence"]] = stats["by_tier"].get(r["confidence"], 0) + 1
        wno, wname = assign_ward(r["lon"], r["lat"], wards)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "sl_no": sl,
                "name": name,
                "type": (row.get("Type") or "").strip,
                "authority": (row.get("Authority") or "").strip,
                "geocode_confidence": r["confidence"],
                "geocode_query": r["query"],
                "geocode_locality": r["locality"],
                "geocode_pincode": r["pincode"],
                "nominatim_importance": r["importance"],
                "nominatim_match": r["display_name"],
                "ward_no": wno,
                "ward_name": wname,
            },
        })
    fc = {"type": "FeatureCollection", "features": features}
    json.dump(fc, open(OUT_GEO, "w"), indent=1)

    # ward stats
    per_ward = {f["properties"]["ward_no"]: 0 for f in wards["features"]}
    out_of_bounds = 0
    for f in features:
        w = f["properties"]["ward_no"]
        if w is None:
            out_of_bounds += 1
        else:
            per_ward[w] = per_ward.get(w, 0) + 1
    zero = sorted([w for w, c in per_ward.items if c == 0])
    nonzero = {w: c for w, c in per_ward.items if c > 0}

    print("=== GEOCODING ===")
    print("total rows:", stats["total"])
    print("geocoded:", stats["geocoded"])
    print("failed:", stats["failed"])
    print("by tier:", stats["by_tier"])
    print("success rate: %.1f%%" % (100 * stats["geocoded"] / stats["total"]))
    print("\n=== WARD ASSIGNMENT ===")
    print("libraries placed in a ward:", sum(nonzero.values))
    print("libraries outside all ward polygons:", out_of_bounds)
    print("wards WITH >=1 library:", len(nonzero))
    print("ZERO-library wards (of 200):", len(zero))
    print("zero wards:", zero)
    print("\nfail rows:")
    for fr in stats["fail_rows"]:
        print("  ", fr)

    json.dump({"per_ward": per_ward, "zero_wards": zero, "stats": {k: v for k, v in stats.items if k != "fail_rows"},
               "fail_rows": stats["fail_rows"], "out_of_bounds": out_of_bounds},
              open(os.path.join(ROOT, "library_ward_stats.json"), "w"), indent=1)

if __name__ == "__main__":
    main
