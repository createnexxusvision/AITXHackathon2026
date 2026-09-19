#!/usr/bin/env python3
"""Agent B core model. Produces, per docs/DATA_CONTRACT.md 1.0.0:

  data/core/faces.geojson      canonical block faces, stable face_id = <centerlineid>:<L|R>
  data/core/manifest.json      faces_version, sources, counts, CRS/measurement method
  data/core/assumptions.json   every constant used below, with ids
  data/corridor.json           merged model output (schema 1.0.0 + additive raccoon fields)

Inputs: data/*.geojson, data/*.json written by scripts/pull_corridor_data.py.
Optional: data/joins/complaints_by_face.json (Agent A). If absent, B's own 311 pull is used and
labelled coverage=partial_snapshot; the scored complaint component stays null either way.

Deps: pip install shapely pyproj
"""
import json, re, math, hashlib, pathlib, datetime, subprocess
from collections import defaultdict
from shapely.geometry import shape, Point, mapping
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"; CORE = DATA / "core"; CORE.mkdir(parents=True, exist_ok=True)
to_ft = Transformer.from_crs("EPSG:4326", "EPSG:2278", always_xy=True).transform   # NAD83 TX South Central, US ft
to_ll = Transformer.from_crs("EPSG:2278", "EPSG:4326", always_xy=True).transform
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
try: COMMIT = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
except Exception: COMMIT = None

def load(name):
    d = json.load(open(DATA / name))
    return d["features"] if isinstance(d, dict) and d.get("type") == "FeatureCollection" else d
H = range(168)

# ---------------------------------------------------------------- assumptions
A = {
  "A01_face_offset_ft":   {"value": 26.0, "note": "display offset from centerline to face line; not a measured curb"},
  "A02_space_length_ft":  {"value": 22.0, "note": "gross_capacity = floor(length_ft/22); rough, not legal inventory"},
  "A03_parcel_join":      {"value": "centroid-nearest face within 400 ft, same side", "note": "fallback method; confidence recorded"},
  "A04_demand_vpa": {"value": {"F1": 40, "A1": 4, "B1": 8, "B2": 12}, "note": "hypothetical vehicles per acre at curve peak"},
  "A05_demand_curves":    {"value": "see classes[]", "note": "hypothetical hour-of-week lookup; F1 treated as generic commercial, NOT verified nightlife"},
  "A06_pressure_weights": {"value": {"D": 0.60, "S": 0.25, "C": 0.15}, "note": "illustrative; C dropped and weights renormalised when complaints coverage != complete_window"},
  "A07_demand_p95":       {"value": None, "note": "frozen at build; 95th percentile of demand_proxy over analysis-area faces"},
  "A08_pbd_permit_rule":  {"value": "THU-SUN 18:00-02:00 permit-only", "note": "UNVERIFIED scenario assumption from houstontx.gov/parking/washingtonavenue.html; not baseline law"},
  "A09_rpp_semantics":    {"value": "start-day", "note": "WED-SAT 23:00-05:00 = Wed 23 .. Thu 04"},
  "A10_bus_stop_exclusion": {"value": None, "note": "no verified length; stops are context only, no supply deduction"},
  "A11_adt_join":         {"value": "same street token, nearest station <= 1500 ft", "note": "context; latest count only"},
  "A12_311_join":         {"value": "nearest face <= 300 ft by lat/lon", "note": "coverage partial_snapshot; report-time bins"},
  "A13_raccoon_trash_re": {"value": "trash|garbage|dump|heavy trash|container|recycl|weeds|nuisance|dead animal", "note": "311 title filter for forage signal"},
  "A14_raccoon_weights":  {"value": {"T": 0.5, "R": 0.3, "F": 0.2}, "note": "trash-311 exposure, residential acres (bins), commercial acres (dumpsters); hypothetical"},
  "A15_raccoon_curve":    {"value": "nocturnal 21:00-05:00 peak, weekend +20%", "note": "raccoon activity assumption; not ecological data"},
}

# ---------------------------------------------------------------- curves
def bump(peaks, floor=0.05):
    v = [floor] * 24
    for s, e, lvl in peaks:
        for h in (range(s, e) if s < e else list(range(s, 24)) + list(range(0, e))): v[h] = max(v[h], lvl)
    return v
def week(wd, we, we_days=(4, 5)):
    return sum(((we if d in we_days else wd) for d in range(7)), [])
CLASSES = {
  "F1": {"label": "Commercial (HCAD F1)", "curve": week(bump([(11,14,.6),(17,23,.8)]), bump([(11,14,.5),(19,2,1.0)]), (3,4,5))},
  "A1": {"label": "Single-family (A1)",   "curve": week(bump([(18,8,.4)]), bump([(0,24,.4)]))},
  "B1": {"label": "Multifamily small (B1)","curve": week(bump([(18,8,.6)]), bump([(0,24,.6)]))},
  "B2": {"label": "Multifamily (B2)",     "curve": week(bump([(18,8,.8)]), bump([(0,24,.8)]))},
}
for k, v in CLASSES.items():
    v["vehicles_per_acre_peak"] = A["A04_demand_vpa"]["value"][k]
    v["curve"] = [round(x * v["vehicles_per_acre_peak"], 3) for x in v["curve"]]
RACCOON_CURVE = [round(x, 3) for x in week(bump([(21,5,1.0),(5,7,.4)], .1), [min(1.0, x*1.2) for x in bump([(21,5,1.0),(5,7,.4)], .1)])]

# ---------------------------------------------------------------- regulation
DAYS = {"MON":0,"TUE":1,"WED":2,"THU":3,"FRI":4,"SAT":5,"SUN":6}
def hours_for(time_s, days_s):
    m = re.match(r"\s*(\d+)(AM|PM)-(\d+)(AM|PM)", (time_s or "").upper())
    if not m: return set()
    h24 = lambda n, ap: int(n) % 12 + (12 if ap == "PM" else 0)
    s, e = h24(m.group(1), m.group(2)), h24(m.group(3), m.group(4))
    span = list(range(s, e)) if s < e else list(range(s, 24)) + list(range(0, e))
    dm = re.match(r"\s*([A-Z]{3})-([A-Z]{3})", (days_s or "").upper())
    if dm and dm.group(1) in DAYS and dm.group(2) in DAYS:
        d0, d1 = DAYS[dm.group(1)], DAYS[dm.group(2)]
        days = list(range(d0, d1+1)) if d0 <= d1 else list(range(d0, 7)) + list(range(0, d1+1))
    else: days = list(range(7))
    out = set()
    for d in days:
        for h in span: out.add(((d + (1 if (s > e and h < s) else 0)) % 7) * 24 + h)   # start-day semantics
    return out
PBD_PERMIT = hours_for("6PM-2AM", "THU-SUN")
rpp = defaultdict(list)
for f in load("rpp.geojson"):
    p = f["properties"]; key = re.sub(r"\s*\(.*\)", "", (p.get("STREET") or "")).strip().upper()
    try: rpp[(key, int(str(p["BLOCK"]).strip()))].append({"hours": hours_for(p.get("TIME"), p.get("DAYS")), "text": f"{p.get('STREET')} {p.get('BLOCK')} {p.get('TIME')} {p.get('DAYS')}", "src": "Residential_Parking_Permit_3/6"})
    except Exception: pass

# ---------------------------------------------------------------- faces
pbd_ll = shape(json.load(open(DATA / "pbd_boundary.geojson"))["geometry"]); pbd = transform(to_ft, pbd_ll)
faces, geoms = [], []
strip = lambda n: re.sub(r"\s+(AVE|ST|BLVD|DR|RD|LN|PKWY|WAY|CT|PL)$", "", n)
for f in load("centerline.geojson"):
    p = f["properties"]; line = transform(to_ft, shape(f["geometry"]))
    name = (p.get("fullname") or "UNNAMED").strip().upper(); cid = str(p.get("centerlineid") or p.get("OBJECTID"))
    for side, lo, hi in (("L", p.get("fromleft"), p.get("toleft")), ("R", p.get("fromright"), p.get("toright"))):
        try: off = line.parallel_offset(A["A01_face_offset_ft"]["value"], "left" if side == "L" else "right", join_style=2)
        except Exception: continue
        if off.is_empty or off.geom_type != "LineString": continue
        lo_i = int(lo) if isinstance(lo, (int, float)) and lo else None; hi_i = int(hi) if isinstance(hi, (int, float)) and hi else None
        block = (lo_i // 100) * 100 if lo_i else None
        parity = "unknown"
        if lo_i is not None and hi_i is not None: parity = "even" if lo_i % 2 == 0 and hi_i % 2 == 0 else "odd" if lo_i % 2 and hi_i % 2 else "both"
        rules = rpp.get((strip(name), block), []) if block is not None else []
        faces.append({"face_id": f"{cid}:{side}", "source_segment_id": cid, "side": side, "street": name,
                      "display_label": f"{name.title()} {block or ''} block, {'left' if side=='L' else 'right'} side".replace("  ", " "),
                      "address_low": lo_i, "address_high": hi_i, "address_parity": parity,
                      "length_ft": round(off.length, 1), "in_analysis_area": bool(off.intersects(pbd)),
                      "_ft": off, "rules": rules, "landuse": defaultdict(float), "parcels": 0,
                      "complaints": [0]*168, "trash": [0]*168, "other311": 0, "stops": [], "adt": None})
        geoms.append(off)
tree = STRtree(geoms)
faces_version = hashlib.sha1("".join(f["face_id"] for f in faces).encode()).hexdigest()[:10]

# ---------------------------------------------------------------- joins
for f in load("parcels.geojson"):
    p = f["properties"]; cls = p.get("State_Clas")
    if cls not in CLASSES and cls not in ("C1", "C2"): continue
    try: c = transform(to_ft, shape(f["geometry"])).centroid
    except Exception: continue
    i = tree.nearest(c)
    if geoms[i].distance(c) <= 400:
        faces[i]["landuse"][cls] += float(p.get("Acreage") or 0); faces[i]["parcels"] += 1

for s in load("metro_stops.json"):
    c = Point(to_ft(s["lon"], s["lat"])); i = tree.nearest(c); d = geoms[i].distance(c)
    if d <= 150: faces[i]["stops"].append({"id": s["id"], "distance_ft": round(d, 1)})

adt = [(Point(to_ft(a["lon"], a["lat"])), a) for a in load("adt_volumes.json") if a.get("adt")]
for fc in faces:
    best = None
    for pt, a in adt:
        tok = strip(re.sub(r"[, ].*", "", a["address"].split(" ", 1)[1]).upper()) if " " in a["address"] else ""
        if tok and tok in fc["street"]:
            d = fc["_ft"].distance(pt)
            if d <= 1500 and (best is None or d < best[0]): best = (d, a)
    if best: fc["adt"] = {"station": best[1]["station"], "volume": int(best[1]["adt"]), "units": "vehicles/day",
                          "measured": best[1]["date"], "distance_ft": round(best[0], 1), "source": best[1]["source"]}

PARK_RE = re.compile(r"park|vehicle|driveway|tow|abandon|meter", re.I)
TRASH_RE = re.compile(A["A13_raccoon_trash_re"]["value"], re.I)
sr_pts = []; joins_file = DATA / "joins" / "complaints_by_face.json"
complaints_cov = "partial_snapshot"
for r in load("sr311_raw.json"):
    if not (r.get("Latitude") and r.get("Longitude") and r.get("CreatedDate")): continue
    typ = re.split(r"\s+-\s+\d", r.get("Title") or "")[0].strip() or (r.get("CaseType") or "")
    t = datetime.datetime.fromtimestamp(r["CreatedDate"]/1000)  # container is UTC; server stamps local — treated as local
    h = t.weekday()*24 + t.hour
    c = Point(to_ft(r["Longitude"], r["Latitude"])); i = tree.nearest(c)
    if geoms[i].distance(c) > 300: continue
    kind = "parking" if PARK_RE.search(typ) else "trash" if TRASH_RE.search(typ) else "other"
    if kind == "parking": faces[i]["complaints"][h] += 1
    elif kind == "trash": faces[i]["trash"][h] += 1
    else: faces[i]["other311"] += 1
    sr_pts.append({"case": r.get("CaseNumber"), "type": typ, "kind": kind, "lon": r["Longitude"], "lat": r["Latitude"],
                   "h": h, "date": t.date().isoformat(), "face_id": faces[i]["face_id"]})

# ---------------------------------------------------------------- recipes (personas)
# score = 100 × Σ(w·component)/Σw × max(curve[h]) ; components are 0..1, defined in build; curves are 0..1 over 168 h.
RECIPES = json.load(open(ROOT / "data" / "core" / "recipes.json")) if (ROOT / "data" / "core" / "recipes.json").exists() else {}

# ---------------------------------------------------------------- waste schedules & extra points
DAYNUM = {"MONDAY":0,"TUESDAY":1,"WEDNESDAY":2,"THURSDAY":3,"FRIDAY":4,"SATURDAY":5,"SUNDAY":6,
          "MO":0,"TU":1,"WE":2,"TH":3,"FR":4,"SA":5,"SU":6}
def daynum(s):
    if not s: return None
    t = str(s).upper().replace("YW_","")
    for k, v in DAYNUM.items():
        if t.startswith(k): return v
    # recycling codes like NWMO-A-01 / MONDAY-A
    m = re.search(r"(MO|TU|WE|TH|FR)", t)
    return DAYNUM[m.group(1)] if m else None
def poly_index(name, field):
    polys, vals = [], []
    for f in load(name):
        try: g = transform(to_ft, shape(f["geometry"]))
        except Exception: continue
        polys.append(g); vals.append(f["properties"].get(field))
    return STRtree(polys), polys, vals
sched = {}
for key, fname, field in [("garbage","waste_garbage.geojson","DAY"), ("recycling","waste_recycling.geojson","NEW_DAY"),
                          ("heavy","waste_heavy.geojson","SERVICE_DA"), ("yard","waste_yard.geojson","YW_DAY")]:
    try: sched[key] = poly_index(fname, field)
    except FileNotFoundError: sched[key] = None
for fc in faces:
    mid = fc["_ft"].interpolate(0.5, normalized=True); fc["sched"] = {}
    for key, idx in sched.items():
        if not idx: fc["sched"][key] = None; continue
        t, polys, vals = idx
        hit = [i for i in t.query(mid) if polys[i].contains(mid)]
        raw = vals[hit[0]] if hit else None
        fc["sched"][key] = {"raw": raw, "day": daynum(raw)}
    fc["missed"] = 0; fc["dead_animals"] = 0; fc["tree311"] = 0
for name, key, maxd in [("waste_missed.geojson","missed",300), ("dead_animals.geojson","dead_animals",300)]:
    try:
        for f in load(name):
            p = f["properties"]
            if not (p.get("Latitude") and p.get("Longitude")): continue
            c = Point(to_ft(p["Longitude"], p["Latitude"])); i = tree.nearest(c)
            if geoms[i].distance(c) <= maxd: faces[i][key] += 1
    except FileNotFoundError: pass
# stop signs / signals within 100 ft (no-parking-near-control rule proxy), flood zones at midpoint, bikeway on face, park frontage
def _pts(name):
    try: return [Point(to_ft(*f["geometry"]["coordinates"])) for f in load(name) if f.get("geometry")]
    except FileNotFoundError: return []
ctl = _pts("traffic_signals.geojson") + _pts("stop_signs.geojson"); ctl_tree = STRtree(ctl) if ctl else None
try:
    fl = [(transform(to_ft, shape(f["geometry"])), f["properties"]) for f in load("flood_nfhl.geojson")]
except FileNotFoundError: fl = []
fl_tree = STRtree([g for g, _ in fl]) if fl else None
try: bk = [transform(to_ft, shape(f["geometry"])) for f in load("bikeways.geojson")]
except FileNotFoundError: bk = []
bk_tree = STRtree(bk) if bk else None
try: pk = [transform(to_ft, shape(f["geometry"])) for f in load("parks.geojson")]
except FileNotFoundError: pk = []
pk_tree = STRtree(pk) if pk else None
for fc in faces:
    mid = fc["_ft"].interpolate(0.5, normalized=True)
    fc["ctl"] = int(bool(ctl_tree and any(ctl[i].distance(fc["_ft"]) <= 100 for i in ctl_tree.query(fc["_ft"].buffer(100))))) if ctl_tree else 0
    fc["flood"] = 0.0
    if fl_tree:
        for i in fl_tree.query(mid):
            if fl[i][0].contains(mid):
                z = fl[i][1].get("FLD_ZONE", ""); fc["flood"] = 1.0 if fl[i][1].get("SFHA_TF") == "T" else (0.5 if "X" in z and "0.2" in (fl[i][1].get("ZONE_SUBTY") or "") else 0.0); break
    fc["bike"] = int(bool(bk_tree and any(bk[i].distance(fc["_ft"]) <= 40 for i in bk_tree.query(fc["_ft"].buffer(40))))) if bk_tree else 0
    fc["park"] = int(bool(pk_tree and any(pk[i].distance(fc["_ft"]) <= 60 for i in pk_tree.query(fc["_ft"].buffer(60))))) if pk_tree else 0
    fc["light311"] = 0
for pt in sr_pts:
    if re.search(r"street ?light|lighting", pt["type"], re.I):
        for fc in faces:
            if fc["face_id"] == pt["face_id"]: fc["light311"] += 1; break
for pt in sr_pts:
    if re.search(r"tree", pt["type"], re.I):
        for fc in faces:
            if fc["face_id"] == pt["face_id"]: fc["tree311"] += 1; break

# ---------------------------------------------------------------- model
W = A["A06_pressure_weights"]["value"]; WR = A["A14_raccoon_weights"]["value"]
recs = []
for fc in faces:
    lu = {k: round(v, 3) for k, v in fc["landuse"].items() if v > 0}
    demand = [round(sum(lu.get(c, 0) * CLASSES[c]["curve"][h] for c in lu if c in CLASSES)) for h in H] if any(c in CLASSES for c in lu) else None
    gross = max(0, int(fc["length_ft"] // A["A02_space_length_ft"]["value"]))
    mask = [False]*168; rule_text = []; verified = False
    for r in fc["rules"]:
        for h in r["hours"]: mask[h] = True
        rule_text.append(r["text"]); verified = True
    if not fc["rules"] and fc["in_analysis_area"]:
        for h in PBD_PERMIT: mask[h] = True
        rule_text.append(A["A08_pbd_permit_rule"]["value"] + " (scenario, unverified)")
    fc.update(lu=lu, demand=demand, gross=gross, mask=mask, rule_text=rule_text, rule_verified=verified,
              trash_total=sum(fc["trash"]), res_acres=lu.get("A1",0)+lu.get("B1",0)+lu.get("B2",0), com_acres=lu.get("F1",0))

pop = [f for f in faces if f["in_analysis_area"] and f["demand"]]
pct = lambda xs, q: sorted(xs)[min(len(xs)-1, int(q*len(xs)))] if xs else 1.0
D_P95 = pct([max(f["demand"]) for f in pop], .95) or 1.0
T_P95 = pct([f["trash_total"] for f in faces if f["trash_total"]], .95) or 1.0
R_P95 = pct([f["res_acres"] for f in faces if f["res_acres"]], .95) or 1.0
F_P95 = pct([f["com_acres"] for f in faces if f["com_acres"]], .95) or 1.0
A["A07_demand_p95"]["value"] = round(D_P95, 3)

for fc in faces:
    wD, wS = W["D"], W["S"]; norm = wD + wS   # C dropped: coverage != complete_window
    if fc["demand"]:
        pressure = []
        for h in H:
            D = min(1.0, fc["demand"][h] / D_P95)
            S = 0.0 if fc["mask"][h] else 1.0     # eligible supply for a non-resident visitor
            pressure.append(round(100 * (wD*D + wS*(1-S)) / norm))
    else: pressure = None
    T = min(1.0, fc["trash_total"] / T_P95); R = min(1.0, fc["res_acres"] / R_P95); F = min(1.0, fc["com_acres"] / F_P95)
    base = WR["T"]*T + WR["R"]*R + WR["F"]*F
    forage = [round(100 * base * RACCOON_CURVE[h]) for h in H] if base > 0 else None
    # ---- components (0..1) for recipe scoring ----
    def night_before(day):     # curve: 1.0 from 20:00 the evening before pickup day until 06:00 that day
        v = [0.0]*168
        if day is None: return v
        for h in range(20, 24): v[((day-1) % 7)*24 + h] = 1.0
        for h in range(0, 7):  v[day*24 + h] = 1.0
        return v
    comp = {
        "trash311": T, "res": R, "com": F,
        "parking311": min(1.0, sum(fc["complaints"]) / 3),
        "adt_low": 1.0 - min(1.0, (fc["adt"]["volume"] if fc["adt"] else 0) / 30000),
        "adt_high": min(1.0, (fc["adt"]["volume"] if fc["adt"] else 0) / 30000),
        "missed": min(1.0, fc["missed"] / 3),
        "roadkill": min(1.0, fc["dead_animals"] / 2),
        "trees": min(1.0, fc["tree311"] / 2),
        "stops": min(1.0, len(fc["stops"]) / 2),
        "capacity": min(1.0, fc["gross"] / 20),
        "restricted": 1.0 if any(fc["mask"]) else 0.0,
        "vacant": min(1.0, (fc["landuse"].get("C1", 0) + fc["landuse"].get("C2", 0)) / 1.0),
        "stop_ctl": float(fc["ctl"]), "flood": fc["flood"], "bike_lane": float(fc["bike"]), "park": float(fc["park"]),
        "dark311": min(1.0, fc["light311"] / 2),
    }
    curves = {
        "nocturnal": RACCOON_CURVE,
        "garbage_night": night_before(fc["sched"]["garbage"]["day"] if fc["sched"].get("garbage") else None),
        "recycling_night": night_before(fc["sched"]["recycling"]["day"] if fc["sched"].get("recycling") else None),
        "yard_night": night_before(fc["sched"]["yard"]["day"] if fc["sched"].get("yard") else None),
        "flat": [1.0]*168,
        "commercial": [min(1.0, x/40) for x in CLASSES["F1"]["curve"]],
        "late": [1.0 if (h%24) >= 22 or (h%24) <= 2 else 0.2 for h in H],
    }
    # scores are factored: score[h] = 100 × base × max(CURVE_TABLE[c][h] for c in curve_ids). Frontend or model.py expands.
    def curve_id(c):
        if c in ("garbage_night", "recycling_night", "yard_night"):
            day = fc["sched"][c.split("_")[0]]["day"] if fc["sched"].get(c.split("_")[0]) else None
            return None if day is None else f"night_before:{day}"
        return c
    scores = {}
    for rid, r in RECIPES.items():
        w = r["weights"]; tot = sum(abs(v) for v in w.values()) or 1
        base_r = max(0.0, sum(w[k] * comp.get(k, 0) for k in w) / tot)
        ids = [i for i in (curve_id(c) for c in r.get("curves", [])) if i]
        if r.get("window"): ids.append("win:" + ",".join(map(str, r["window"]["days"])) + f":{r['window']['start']}:{r['window']['end']}")
        ids = ids or ["flat"]
        scores[rid] = {"base": round(base_r, 3), "curves": ids} if base_r > 0 else None
    conf = "low" if not fc["rule_verified"] else "medium"
    if not fc["demand"]: conf = "unknown"
    recs.append({
        "face_id": fc["face_id"], "street": fc["street"], "display_label": fc["display_label"], "side": fc["side"],
        "in_analysis_area": fc["in_analysis_area"],
        "geometry": {"type": "LineString", "coordinates": [[round(x,6), round(y,6)] for x, y in transform(to_ll, fc["_ft"]).coords]},
        "length_ft": fc["length_ft"],
        "parcel_summary": {"count": fc["parcels"], "acres_by_class": fc["lu"], "join": A["A03_parcel_join"]["value"]},
        "demand_proxy": fc["demand"],
        "regulation_mask": fc["mask"] if any(fc["mask"]) else None,
        "regulation_rules": {"text": fc["rule_text"], "verified": fc["rule_verified"], "semantics": "start-day", "user_class": "non-resident visitor"},
        "complaints": fc["complaints"] if sum(fc["complaints"]) else None,
        "gross_capacity_spaces": gross if False else fc["gross"],
        "fixed_exclusions": {"intervals": [], "unknown": True, "note": A["A10_bus_stop_exclusion"]["note"]},
        "eligible_supply_spaces": [0 if fc["mask"][h] else fc["gross"] for h in H] if any(fc["mask"]) else None,   # null = constant gross_capacity all week
        "adt": fc["adt"],
        "nearby_stop_ids": [s["id"] for s in fc["stops"]],
        "pressure_index": pressure,
        "confidence": conf,
        # ---- Raccoon Mode (additive, hypothetical) ----
        "forage_index": forage,
        "forage_components": {"T": round(T,3), "R": round(R,3), "F": round(F,3), "trash_311_total": fc["trash_total"], "other_311": fc["other311"]},
        "components": {k: round(v, 3) for k, v in comp.items()} | {"D_weights": {"D": wD, "S": wS, "C": None}, "demand_p95": round(D_P95, 3), "missing": ["C: complaints coverage partial_snapshot"]},
        "schedule": {k: (v["raw"] if v else None) for k, v in fc["sched"].items()},
        "extras": {"missed_collections": fc["missed"], "dead_animals": fc["dead_animals"], "tree_311": fc["tree311"]},
        "scores": scores,
        "source_ids": "manifest", "assumption_ids": "assumptions.json",
    })
    if not fc["demand"] and not fc["rules"] and not fc["trash_total"] and not sum(fc["complaints"]): recs.pop()  # empty face

# ---------------------------------------------------------------- write
keep = {r["face_id"] for r in recs}
faces_fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": r["geometry"],
            "properties": {k: r[k] for k in ("face_id","street","display_label","side","length_ft","in_analysis_area")}
                          | {"source_segment_id": r["face_id"].split(":")[0], "geometry_basis": f"centerline parallel_offset {A['A01_face_offset_ft']['value']} ft, EPSG:2278"}}
            for r in recs]}
json.dump(faces_fc, open(CORE / "faces.geojson", "w"), separators=(",", ":"))
json.dump({"faces_version": faces_version, "schema_version": "1.0.0", "generated_at": NOW, "producer_commit": COMMIT,
           "crs_measure": "EPSG:2278 (US survey ft)", "face_count": len(recs), "in_analysis_area": sum(r["in_analysis_area"] for r in recs),
           "bbox": list(transform(to_ll, pbd).bounds), "sources": {
             "centerline": "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/COH_RoadCenterline/FeatureServer/0",
             "parcels": "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/HCAD_Parcels/FeatureServer/0",
             "rpp": "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/Residential_Parking_Permit_3/FeatureServer/6",
             "pbd": "https://data.houstontx.gov/dataset/washington-avenue-parking-benefit-district (2013)",
             "adt": "https://geogimstest.houstontx.gov/arcgis/rest/services/TDO/Traffic_gx/MapServer/4 + table 22",
             "metro": "METRO GTFS static stops.txt (metro.resourcespace.com ref 4835)",
             "sr311": "https://mycity2.houstontx.gov/pubgis01/rest/services/311 (OPEN + recent layers)"}},
          open(CORE / "manifest.json", "w"), indent=1)
json.dump(A, open(CORE / "assumptions.json", "w"), indent=1)
doc = {"schema_version": "1.0.0", "generated_at": NOW, "faces_version": faces_version, "timezone": "America/Chicago",
       "hour_origin": "Monday 00:00", "analysis_boundary": "data/pbd_boundary.geojson (2013)", "source_manifest": "data/core/manifest.json",
       "assumptions_version": hashlib.sha1(json.dumps(A, sort_keys=True).encode()).hexdigest()[:10],
       "normalization": {"demand_p95": round(D_P95,3), "trash_p95": T_P95, "res_acres_p95": round(R_P95,3), "com_acres_p95": round(F_P95,3), "weights": W, "raccoon_weights": WR},
       "coverage": {"complaints": complaints_cov, "complaints_window": "311 OPEN+recent layers, multi-year, report-time bins", "scored_complaint_component": None,
                    "adt_faces": sum(1 for r in recs if r["adt"]), "faces_with_parcels": sum(1 for r in recs if r["demand_proxy"])},
       "classes": CLASSES, "raccoon_curve": RACCOON_CURVE,
       "modes": {"curb": {"index": "pressure_index", "label": "Curb pressure (uncalibrated)"},
                 "raccoon": {"index": "forage_index", "label": "Raccoon forage potential (hypothetical)"}}
                | {rid: {"index": f"scores.{rid}", "label": r["label"], "blurb": r["blurb"], "audience": r["audience"]} for rid, r in RECIPES.items()},
       "recipes": RECIPES,
       "curve_table": {"nocturnal": RACCOON_CURVE, "flat": [1.0]*168, "late": [1.0 if (h%24) >= 22 or (h%24) <= 2 else 0.2 for h in H],
                       "commercial": [round(min(1.0, x/40), 3) for x in CLASSES["F1"]["curve"]]}
                      | {f"night_before:{d}": [1.0 if (((h//24) == (d-1) % 7 and h%24 >= 20) or ((h//24) == d and h%24 < 7)) else 0.0 for h in H] for d in range(7)}
                      | {("win:" + ",".join(map(str, r["window"]["days"])) + f":{r['window']['start']}:{r['window']['end']}"):
                         [1.0 if ((h//24) in r["window"]["days"] and ((r["window"]["start"] <= h%24 < r["window"]["end"]) if r["window"]["start"] < r["window"]["end"] else (h%24 >= r["window"]["start"] or h%24 < r["window"]["end"]))) else 0.0 for h in H]
                         for r in RECIPES.values() if r.get("window")},
       "score_formula": "score[h] = round(100 * scores[rid].base * max(curve_table[c][h] for c in scores[rid].curves))",
       "presets": [{"h": 4*24+22, "mode": "curb", "label": "Fri 10 PM — commercial peak"},
                   {"h": 5*24+1, "mode": "curb", "label": "Sat 1 AM — permit hours"},
                   {"h": 4*24+23, "mode": "raccoon", "label": "Fri 11 PM — prime foraging"},
                   {"h": 1*24+3, "mode": "raccoon", "label": "Tue 3 AM — quiet trash night"}],
       "points": {"metro_stops": load("metro_stops.json"), "adt_stations": [a for a in load("adt_volumes.json") if a.get("adt")], "sr311": sr_pts},
       "faces": recs}
out = DATA / "corridor.json"; json.dump(doc, open(out, "w"), separators=(",", ":"))
print(f"faces={len(recs)} in_area={sum(r['in_analysis_area'] for r in recs)} faces_version={faces_version} "
      f"311={len(sr_pts)} (parking {sum(p['kind']=='parking' for p in sr_pts)}, trash {sum(p['kind']=='trash' for p in sr_pts)}) "
      f"size={out.stat().st_size/1e6:.1f} MB")

# ---------------------------------------------------------------- UI packet (compact)
def _events():
    """Singular, icon-worthy events: dead-animal pickups, missed collections, dumping/dumpster 311."""
    ev = []
    try:
        for f in load("dead_animals.geojson"):
            q = f["properties"]
            if q.get("Latitude") and q.get("Longitude"): ev.append({"t": "roadkill", "lon": round(q["Longitude"],5), "lat": round(q["Latitude"],5), "d": (q.get("ArrivalTime") or "")[:10] if isinstance(q.get("ArrivalTime"), str) else None})
    except FileNotFoundError: pass
    try:
        for f in load("waste_missed.geojson"):
            q = f["properties"]
            if q.get("Latitude") and q.get("Longitude"):
                ev.append({"t": "missed", "lon": round(q["Longitude"],5), "lat": round(q["Latitude"],5), "m": (q.get("MaterialType") or "")[:20], "d": None})
    except FileNotFoundError: pass
    for p in sr_pts:
        if re.search(r"dump", p["type"], re.I): ev.append({"t": "dumping", "lon": round(p["lon"],5), "lat": round(p["lat"],5), "d": p["date"]})
    return ev
def _bits(m): return "".join("1" if x else "0" for x in m) if m else None
COMPONENT_CATALOG = {
    "res":       {"label": "Residential frontage", "desc": "Acres of A1/B1/B2 parcels on the face. Bins on the curb, residents needing parking.", "src": "HCAD"},
    "com":       {"label": "Commercial frontage", "desc": "Acres of F1 parcels. Dumpsters, customers, deliveries, late activity.", "src": "HCAD"},
    "trash311":  {"label": "Trash-related 311", "desc": "Trash, dumping, missed pickup, nuisance cases within 300 ft.", "src": "311"},
    "parking311":{"label": "Parking-related 311", "desc": "Parking violation and meter complaints within 300 ft.", "src": "311"},
    "missed":    {"label": "Missed collections", "desc": "Solid Waste missed-pickup exceptions logged at the face.", "src": "SWM Routeware"},
    "roadkill":  {"label": "Dead-animal pickups", "desc": "Solid Waste dead-animal collection calls at the face. Danger signal.", "src": "SWM"},
    "trees":     {"label": "Big-tree proxy", "desc": "311 tree trim/removal requests. Canopy, denning, shade.", "src": "311"},
    "adt_low":   {"label": "Quiet street", "desc": "Inverse of traffic volume (1 = no traffic).", "src": "Public Works ADT"},
    "adt_high":  {"label": "Busy street", "desc": "Traffic volume (1 = 30k+ vehicles/day).", "src": "Public Works ADT"},
    "stops":     {"label": "Bus stops", "desc": "METRO stops on the face.", "src": "METRO GTFS"},
    "capacity":  {"label": "Curb capacity", "desc": "floor(length/22) spaces, 1 = 20+.", "src": "COH centerline"},
    "restricted":{"label": "Permit-restricted", "desc": "Any residential permit or PBD restriction during the week.", "src": "RPP / PBD"},
    "vacant":    {"label": "Vacant lots", "desc": "Acres of vacant parcels (C1/C2) on the face.", "src": "HCAD"},
    "stop_ctl":  {"label": "Stop sign / signal nearby", "desc": "Traffic control within 100 ft; no-parking-near-intersection rule proxy.", "src": "TDO"},
    "flood":     {"label": "Flood zone", "desc": "1 = FEMA special flood hazard area (AE), 0.5 = 500-yr, 0 = outside.", "src": "FEMA NFHL"},
    "bike_lane": {"label": "Bike lane on face", "desc": "Existing bikeway within 40 ft; replaces curb parking.", "src": "COH Bikeways"},
    "park":      {"label": "Park frontage", "desc": "City park within 60 ft.", "src": "COH Parks"},
    "dark311":   {"label": "Streetlight outages", "desc": "311 streetlight/lighting cases at the face.", "src": "311"},
}
LICENSED_CATALOG = {
    "meters":       {"label": "Meter transactions", "desc": "Pay-by-plate occupancy by space and hour. Turns pressure from model into measurement.", "src": "ParkHouston (data agreement)", "price": "city partnership"},
    "waymo":        {"label": "Robotaxi pickup/dropoff density", "desc": "Rideshare curb demand by block and hour.", "src": "Waymo", "price": "partner API"},
    "foot_traffic": {"label": "Foot-traffic panel", "desc": "Anonymized visits by venue and hour.", "src": "Advan / Placer", "price": "from ~$500/mo"},
    "popular_times":{"label": "Popular times", "desc": "Busy-ness curve per venue.", "src": "Google Places", "price": "API usage"},
    "satellite":    {"label": "Daily satellite imagery", "desc": "Count parked cars from orbit, daily revisit.", "src": "Planet / Maxar", "price": "per km²"},
    "tabc":         {"label": "Licensed bars & restaurants", "desc": "TABC licenses geocoded to the face (public, needs geocoding work).", "src": "TABC", "price": "free, not yet joined"},
}
CURVE_CATALOG = {
    "flat": "all hours equal", "nocturnal": "raccoon hours, 21:00–05:00, weekends stronger", "late": "22:00–02:00",
    "commercial": "business + evening commercial hours", "garbage_night": "evening before garbage day (per face)",
    "recycling_night": "evening before recycling day (per face)", "yard_night": "evening before yard-waste day (per face)",
}
lite = {"generated_at": NOW, "component_catalog": COMPONENT_CATALOG, "licensed_catalog": LICENSED_CATALOG, "curve_catalog": CURVE_CATALOG, "faces_version": faces_version, "modes": doc["modes"], "recipes": RECIPES, "curve_table": doc["curve_table"],
        "classes": {k: {"label": v["label"], "curve": v["curve"]} for k, v in CLASSES.items()}, "raccoon_curve": RACCOON_CURVE,
        "normalization": doc["normalization"], "presets": doc["presets"],
        "points": {"sr311": [{"kind": p["kind"], "lon": p["lon"], "lat": p["lat"], "h": p["h"], "type": p["type"][:40]} for p in sr_pts],
                   "events": _events(),
                   "metro_stops": doc["points"]["metro_stops"], "adt_stations": [{k: a[k] for k in ("lon","lat","adt","segment")} for a in doc["points"]["adt_stations"]]},
        "faces": [{"id": r["face_id"], "label": r["display_label"], "g": [[round(x,5), round(y,5)] for x, y in r["geometry"]["coordinates"]], "pbd": r["in_analysis_area"],
                   "cap": r["gross_capacity_spaces"], "lu": r["parcel_summary"]["acres_by_class"], "mask": _bits(r["regulation_mask"]), "rules": r["regulation_rules"]["text"],
                   "adt": r["adt"]["volume"] if r["adt"] else None, "conf": r["confidence"],
                   "fb": (r["forage_components"]["T"]*WR["T"] + r["forage_components"]["R"]*WR["R"] + r["forage_components"]["F"]*WR["F"]) if r["forage_index"] else None,
                   "sc": r["scores"], "comp": {k: v for k, v in r["components"].items() if not isinstance(v, (dict, list))}, "sched": r["schedule"], "x": r["extras"]} for r in recs]}
lp = DATA / "corridor_lite.json"; json.dump(lite, open(lp, "w"), separators=(",", ":"))
print(f"corridor_lite.json {lp.stat().st_size/1e6:.1f} MB")
