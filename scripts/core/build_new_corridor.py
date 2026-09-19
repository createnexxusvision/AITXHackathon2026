#!/usr/bin/env python3
"""Pull + build a new CurbFusion corridor for an arbitrary bounding box, anywhere Houston's
open GIS layers cover (in practice: anywhere inside the 610 loop and well beyond it).

This is a generalized, curb-pressure-only sibling of scripts/core/pull_corridor_data.py +
scripts/core/build_core.py. Those two scripts are Washington-Ave-specific: they read a real
legal Parking Benefit District polygon and apply its unique Thu-Sun 18:00-02:00 permit-only
scenario. Most Houston streets have no such PBD, so inventing one would violate this project's
own data-integrity rule (AGENTS.md: "Never replace missing inputs with invented observations").
Instead, a new corridor's only regulation signal is real Residential Parking Permit segments
actually on file for that street/block -- if none exist, the block is simply left unregulated.

Sources pulled here (same live, no-auth Houston/ArcGIS endpoints as pull_corridor_data.py):
  - HCAD_Parcels, COH_RoadCenterline, Residential_Parking_Permit_3  (services.arcgis.com)
Deliberately NOT pulled (no verified public endpoint on hand for these beyond the Washington Ave
demo bundle a teammate hand-delivered): 311 service requests, Solid Waste pickup-day polygons,
ADT traffic-count volumes, METRO stops. So new corridors get Curb-pressure mode only --
Raccoon mode and Combined risk stay hidden for them in the UI (see hasRaccoon in the frontend),
rather than faking a forage score with no trash data behind it.

Usage:
  python scripts/core/build_new_corridor.py <slug> "<Label>" <minlon> <minlat> <maxlon> <maxlat>

Writes data/areas/<slug>/*.geojson (raw pulls) and data/areas/<slug>/corridor_lite.json
(frontend-ready), then you add an entry to data/areas.json pointing at it and rerun
scripts/core/build_html.py to fold it into the demo.

Deps: pip install shapely pyproj (already required by build_core.py)
"""
import json, re, sys, math, hashlib, pathlib, datetime, urllib.request, urllib.parse
from collections import defaultdict
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer

if len(sys.argv) != 7:
    print(__doc__); sys.exit(1)
SLUG, LABEL, MINLON, MINLAT, MAXLON, MAXLAT = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7])

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AREA_DIR = ROOT / "data" / "areas" / SLUG
AREA_DIR.mkdir(parents=True, exist_ok=True)
to_ft = Transformer.from_crs("EPSG:4326", "EPSG:2278", always_xy=True).transform
to_ll = Transformer.from_crs("EPSG:2278", "EPSG:4326", always_xy=True).transform
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
UA = {"User-Agent": "aitx-curb/0.1"}
ENV = json.dumps({"xmin": MINLON, "ymin": MINLAT, "xmax": MAXLON, "ymax": MAXLAT, "spatialReference": {"wkid": 4326}})

# ---------------------------------------------------------------- 1. pull (live, no-auth)
def get(url, params=None, timeout=90):
    if params: url += "?" + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))

def pull(url, out_name, fields="*"):
    out_path = AREA_DIR / out_name
    if out_path.exists():
        print(f"  {out_name} already pulled, skipping"); return
    feats, off = [], 0
    while True:
        d = get(f"{url}/query", {"geometry": ENV, "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                                  "spatialRel": "esriSpatialRelIntersects", "outFields": fields, "outSR": 4326,
                                  "f": "geojson", "resultOffset": off, "resultRecordCount": 2000})
        f = d.get("features", []); feats += f
        if len(f) < 2000: break
        off += 2000
    out_path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    print(f"  {out_name}: {len(feats)} features")

COH = "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services"
print(f"Pulling {LABEL} ({SLUG}) bbox=({MINLON},{MINLAT},{MAXLON},{MAXLAT})")
pull(f"{COH}/HCAD_Parcels/FeatureServer/0", "parcels.geojson",
     "HCAD_NUM,Site_addr_,Site_addr1,State_Clas,Yr_Impr,Acreage,Land_Value,Improvemen")
pull(f"{COH}/COH_RoadCenterline/FeatureServer/0", "centerline.geojson",
     "centerlineid,roadclass,fullname,fromleft,toleft,fromright,toright,onewaydir")
pull(f"{COH}/Residential_Parking_Permit_3/FeatureServer/6", "rpp.geojson")

# ---------------------------------------------------------------- 2. build (curb pressure only)
def load(name):
    d = json.load(open(AREA_DIR / name))
    return d["features"] if isinstance(d, dict) and d.get("type") == "FeatureCollection" else d

H = range(168)
def bump(peaks, floor=0.05):
    v = [floor] * 24
    for s, e, lvl in peaks:
        for hh in (range(s, e) if s < e else list(range(s, 24)) + list(range(0, e))): v[hh] = max(v[hh], lvl)
    return v
def week(wd, we, we_days=(4, 5)):
    return sum(((we if d in we_days else wd) for d in range(7)), [])
VPA = {"F1": 40, "A1": 4, "B1": 8, "B2": 12}
CLASSES = {
  "F1": {"label": "Commercial (HCAD F1)", "curve": week(bump([(11,14,.6),(17,23,.8)]), bump([(11,14,.5),(19,2,1.0)]), (3,4,5))},
  "A1": {"label": "Single-family (A1)",   "curve": week(bump([(18,8,.4)]), bump([(0,24,.4)]))},
  "B1": {"label": "Multifamily small (B1)","curve": week(bump([(18,8,.6)]), bump([(0,24,.6)]))},
  "B2": {"label": "Multifamily (B2)",     "curve": week(bump([(18,8,.8)]), bump([(0,24,.8)]))},
}
for k, v in CLASSES.items(): v["curve"] = [round(x * VPA[k], 3) for x in v["curve"]]

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
        for hh in span: out.add(((d + (1 if (s > e and hh < s) else 0)) % 7) * 24 + hh)
    return out
rpp = defaultdict(list)
strip = lambda n: re.sub(r"\s+(AVE|ST|BLVD|DR|RD|LN|PKWY|WAY|CT|PL)$", "", n)
for f in load("rpp.geojson"):
    p = f["properties"]; key = re.sub(r"\s*\(.*\)", "", (p.get("STREET") or "")).strip().upper()
    try: rpp[(key, int(str(p["BLOCK"]).strip()))].append({"hours": hours_for(p.get("TIME"), p.get("DAYS")),
                                                            "text": f"{p.get('STREET')} {p.get('BLOCK')} {p.get('TIME')} {p.get('DAYS')}"})
    except Exception: pass

faces, geoms = [], []
for f in load("centerline.geojson"):
    p = f["properties"]; line = transform(to_ft, shape(f["geometry"]))
    name = (p.get("fullname") or "UNNAMED").strip().upper(); cid = str(p.get("centerlineid") or p.get("OBJECTID"))
    for side, lo in (("L", p.get("fromleft")), ("R", p.get("fromright"))):
        try: off = line.parallel_offset(26.0, "left" if side == "L" else "right", join_style=2)
        except Exception: continue
        if off.is_empty or off.geom_type != "LineString": continue
        lo_i = int(lo) if isinstance(lo, (int, float)) and lo else None
        block = (lo_i // 100) * 100 if lo_i else None
        rules = rpp.get((strip(name), block), []) if block is not None else []
        faces.append({"id": f"{cid}:{side}", "street": name,
                      "label": f"{name.title()} {block or ''} block, {'left' if side=='L' else 'right'} side".replace("  ", " "),
                      "length_ft": round(off.length, 1), "_ft": off, "rules": rules, "lu": defaultdict(float)})
        geoms.append(off)
tree = STRtree(geoms)
geom_idx = {id(g): i for i, g in enumerate(geoms)}  # shapely 1.x STRtree.nearest() returns a geometry, not an index

for f in load("parcels.geojson"):
    p = f["properties"]; cls = p.get("State_Clas")
    if cls not in CLASSES: continue
    try: c = transform(to_ft, shape(f["geometry"])).centroid
    except Exception: continue
    nearest = tree.nearest(c)
    i = geom_idx[id(nearest)]
    if geoms[i].distance(c) <= 400: faces[i]["lu"][cls] += float(p.get("Acreage") or 0)

recs = []
for fc in faces:
    lu = {k: round(v, 3) for k, v in fc["lu"].items() if v > 0}
    if not lu and not fc["rules"]: continue  # nothing to show for this face
    demand = [round(sum(lu.get(c, 0) * CLASSES[c]["curve"][h] for c in lu)) for h in H] if lu else None
    mask = [False] * 168; rule_text = []
    for r in fc["rules"]:
        for h in r["hours"]: mask[h] = True
        rule_text.append(r["text"])
    recs.append({"fc": fc, "lu": lu, "demand": demand, "mask": mask, "rule_text": rule_text,
                 "gross": max(0, int(fc["length_ft"] // 22))})

pop = [r["demand"] for r in recs if r["demand"]]
D_P95 = (sorted(max(d) for d in pop)[min(len(pop)-1, int(.95*len(pop)))] if pop else 1.0) or 1.0

out_faces = []
for r in recs:
    fc = r["fc"]
    out_faces.append({
        "id": fc["id"], "label": fc["label"],
        "g": [[round(x, 5), round(y, 5)] for x, y in transform(to_ll, fc["_ft"]).coords],
        "pbd": True, "cap": r["gross"], "lu": r["lu"],
        "mask": "".join("1" if x else "0" for x in r["mask"]) if any(r["mask"]) else None,
        "rules": r["rule_text"], "adt": None, "conf": "low" if r["rule_text"] else "unknown",
        "fb": None, "sc": {},
        "comp": {"trash311": 0, "parking311": 0}, "sched": {"garbage": None, "recycling": None, "heavy": None},
        "x": {"missed_collections": 0, "dead_animals": 0, "tree_311": 0},
        "demand": r["demand"],
    })
lite = {
    "generated_at": NOW, "faces_version": hashlib.sha1("".join(f["id"] for f in out_faces).encode()).hexdigest()[:10],
    "modes": {"curb": {"index": "pressure_index", "label": "Curb pressure (uncalibrated)"}},
    "recipes": {}, "curve_table": {}, "classes": {k: {"label": v["label"], "curve": v["curve"]} for k, v in CLASSES.items()},
    "raccoon_curve": [0] * 168, "normalization": {"demand_p95": round(D_P95, 3)},
    "presets": [{"h": 4*24+22, "mode": "curb", "label": "Fri 10 PM — commercial peak"},
                {"h": 5*24+1, "mode": "curb", "label": "Sat 1 AM — late night"}],
    "points": {"sr311": [], "metro_stops": [], "adt_stations": []},
    "faces": [{k: v for k, v in f.items() if k != "demand"} for f in out_faces],
}
out = AREA_DIR / "corridor_lite.json"
out.write_text(json.dumps(lite, separators=(",", ":")))
print(f"faces={len(out_faces)} (of {len(faces)} centerline sides) size={out.stat().st_size/1e6:.2f} MB -> {out}")
