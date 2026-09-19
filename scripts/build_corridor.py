#!/usr/bin/env python3
"""Build data/corridor.json from data/*.geojson per docs/CONTRACT.md.

First pass: block faces from centerlines, parcels joined by side, land-use demand curves,
permit-parking regulation mask. 311, bus stops, loading/valet, ADT volumes are stubbed.
Deps: pip install shapely pyproj
"""
import json, re, math, pathlib, datetime
from collections import defaultdict
from shapely.geometry import shape, LineString, Point
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
to_ft = Transformer.from_crs("EPSG:4326", "EPSG:2278", always_xy=True).transform
to_ll = Transformer.from_crs("EPSG:2278", "EPSG:4326", always_xy=True).transform
FACE_OFFSET_FT = 26.0   # centerline -> face line
SPACE_FT = 22.0

def load(name):
    return json.load(open(DATA / name))["features"]

pbd = transform(to_ft, shape(json.load(open(DATA / "pbd_boundary.geojson"))["geometry"]))

# ---- demand curves (168 = Mon00..Sun23), relative units per acre ------------
def curve(weekday_profile, weekend_profile, weekend_days=(4, 5)):
    out = []
    for d in range(7):
        prof = weekend_profile if d in weekend_days else weekday_profile
        out += prof
    return out

def bump(peaks):  # peaks: list of (start_hour, end_hour, level); wraps midnight
    v = [0.05] * 24
    for s, e, lvl in peaks:
        hrs = range(s, e) if s < e else list(range(s, 24)) + list(range(0, e))
        for h in hrs: v[h] = max(v[h], lvl)
    return v

CLASSES = {
    "F1": {"label": "Commercial", "curve": curve(bump([(11, 14, 0.6), (17, 23, 0.8)]),
                                                  bump([(11, 14, 0.5), (19, 2, 1.0)]), weekend_days=(3, 4, 5))},
    "A1": {"label": "Single-family", "curve": curve(bump([(18, 8, 0.4)]), bump([(0, 24, 0.4)]))},
    "B1": {"label": "Multifamily (small)", "curve": curve(bump([(18, 8, 0.6)]), bump([(0, 24, 0.6)]))},
    "B2": {"label": "Multifamily", "curve": curve(bump([(18, 8, 0.8)]), bump([(0, 24, 0.8)]))},
    "C1": {"label": "Vacant", "curve": [0.0] * 168},
    "C2": {"label": "Vacant (commercial)", "curve": [0.0] * 168},
}

# ---- regulation: PBD permit hours + residential permit segments -----------
PBD_PERMIT = set()  # Thu-Sun 18:00-02:00
for d in (3, 4, 5, 6):
    for h in list(range(18, 24)) + [0, 1]:
        PBD_PERMIT.add(((d + (1 if h < 2 else 0)) % 7) * 24 + h)

DAYS = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
def parse_rpp(time_s, days_s):
    """'11PM-5AM','WED-SAT' -> set of hour indices"""
    hours = set()
    m = re.match(r"\s*(\d+)(AM|PM)-(\d+)(AM|PM)", (time_s or "").upper())
    if not m: return hours
    def h24(n, ap):
        n = int(n) % 12; return n + (12 if ap == "PM" else 0)
    s, e = h24(m.group(1), m.group(2)), h24(m.group(3), m.group(4))
    span = range(s, e) if s < e else list(range(s, 24)) + list(range(0, e))
    dm = re.match(r"\s*([A-Z]{3})-([A-Z]{3})", (days_s or "").upper())
    if dm and dm.group(1) in DAYS and dm.group(2) in DAYS:
        d0, d1 = DAYS[dm.group(1)], DAYS[dm.group(2)]
        days = list(range(d0, d1 + 1)) if d0 <= d1 else list(range(d0, 7)) + list(range(0, d1 + 1))
    else:
        days = list(range(7))
    for d in days:
        for h in span:
            dd = (d + (1 if h < s and s > e else 0)) % 7
            hours.add(dd * 24 + h)
    return hours

rpp_index = defaultdict(list)  # (STREET_KEY, BLOCK) -> [hourset]
for f in load("rpp.geojson"):
    p = f["properties"]
    key = re.sub(r"\s*\(.*\)", "", (p.get("STREET") or "")).strip().upper()
    try: blk = int(str(p.get("BLOCK")).strip())
    except: continue
    rpp_index[(key, blk)].append(parse_rpp(p.get("TIME"), p.get("DAYS")))

# ---- block faces ---------------------------------------------------------
faces = []
face_geoms = []
for f in load("centerline.geojson"):
    p = f["properties"]
    line = transform(to_ft, shape(f["geometry"]))
    if not line.intersects(pbd): continue
    name = (p.get("fullname") or "UNNAMED").strip().upper()
    for side, lo, hi in (("L", p.get("fromleft"), p.get("toleft")), ("R", p.get("fromright"), p.get("toright"))):
        try: block = (int(lo) // 100) * 100
        except: block = 0
        try:
            off = line.parallel_offset(FACE_OFFSET_FT, "left" if side == "L" else "right", join_style=2)
        except Exception:
            continue
        if off.is_empty or off.geom_type != "LineString": continue
        base = re.sub(r"\s+(AVE|ST|BLVD|DR|RD|LN|PKWY)$", "", name)
        reg = [0] * 168
        for hset in rpp_index.get((base, block), []):
            for h in hset: reg[h] = 2
        if any(reg):
            reg_src = "RPP"
        else:
            for h in PBD_PERMIT: reg[h] = 1  # metered/PBD
            reg_src = "PBD Thu-Sun 18-02"
        faces.append({
            "id": f"{base.replace(' ', '_')}_{block}_{side}",
            "street": name, "block": block, "side": side,
            "_geom_ft": off, "length_ft": round(off.length, 1),
            "fixed": {"bus_stop": 0, "loading": 0, "valet": 0},
            "landuse": defaultdict(float), "reg": reg, "reg_source": reg_src,
            "complaints": [0] * 168,
        })
        face_geoms.append(off)

tree = STRtree(face_geoms)

# ---- parcels -> nearest face on the same side ----------------------------
for f in load("parcels.geojson"):
    p = f["properties"]
    cls = p.get("State_Clas")
    if cls not in CLASSES: continue
    try: c = transform(to_ft, shape(f["geometry"])).centroid
    except Exception: continue
    if not pbd.contains(c): continue
    idx = tree.nearest(c)
    faces[idx]["landuse"][cls] += float(p.get("Acreage") or 0)

# ---- finalize --------------------------------------------------------------
W_C = 0.5
out_faces = []
for fc in faces:
    lu = {k: round(v, 3) for k, v in fc["landuse"].items() if v > 0}
    if not lu and fc["reg_source"] != "RPP": continue   # drop empty faces
    supply = max(0, int(fc["length_ft"] // SPACE_FT) - sum(fc["fixed"].values()))
    demand = [round(sum(lu.get(c, 0) * CLASSES[c]["curve"][h] for c in lu), 3) for h in range(168)]
    stress = [round(demand[h] / max(supply, 1) + W_C * fc["complaints"][h], 3) for h in range(168)]
    ll = transform(to_ll, fc["_geom_ft"])
    out_faces.append({
        "id": fc["id"], "street": fc["street"], "block": fc["block"], "side": fc["side"],
        "geom": [[round(x, 6), round(y, 6)] for x, y in ll.coords],
        "length_ft": fc["length_ft"], "supply": supply, "fixed": fc["fixed"],
        "landuse": lu, "demand": demand, "reg": fc["reg"], "reg_source": fc["reg_source"],
        "complaints": fc["complaints"], "stress": stress,
    })

bb = transform(to_ll, pbd).bounds
doc = {
    "meta": {"generated": datetime.datetime.now().isoformat(timespec="seconds"),
             "bbox": [round(v, 6) for v in bb], "hours": 168, "hour0": "Monday 00:00", "w_c": W_C,
             "sources": {"parcels": "HCAD_Parcels (COH GIS)", "centerline": "COH_RoadCenterline",
                         "rpp": "Residential_Parking_Permit_3 layer 6", "pbd": "data.houstontx.gov 2013"}},
    "classes": CLASSES,
    "faces": out_faces,
}
(DATA / "corridor.json").write_text(json.dumps(doc, separators=(",", ":")))
print(f"faces={len(out_faces)} size={(DATA/'corridor.json').stat().st_size/1e6:.2f} MB")
