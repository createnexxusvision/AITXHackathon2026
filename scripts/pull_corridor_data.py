#!/usr/bin/env python3
"""Pull Houston open data for the Washington Ave Parking Benefit District extent.

Sources (all public, no auth):
  - data.houstontx.gov  : PBD boundary shapefile (2013)
  - services.arcgis.com/NummVBqZSIJKUeVR (City of Houston GIS org):
        HCAD_Parcels, COH_RoadCenterline, Residential_Parking_Permit_3
  - geogimstest.houstontx.gov TDO/Traffic_gx : ADT count stations

Usage:  python scripts/pull_corridor_data.py
Writes GeoJSON (WGS84) into data/. Re-runnable; overwrites.
Deps:   pip install pyshp shapely pyproj
"""
import json, io, zipfile, pathlib, urllib.request, urllib.parse
import shapefile
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
UA = {"User-Agent": "aitx-curb/0.1"}

def get(url, params=None, timeout=90):
    data = None
    if params:
        q = urllib.parse.urlencode(params)
        if len(q) < 1500: url += "?" + q
        else: data = q.encode()          # POST for long queries (ArcGIS accepts either)
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data, headers=UA), timeout=timeout))

# 1. PBD boundary --------------------------------------------------------
PBD_ZIP = ("https://data.houstontx.gov/dataset/76b205f4-af6b-4c69-a50d-2f749ad9a61a/"
           "resource/44ee8e7f-ea31-454a-8221-299bc83956a3/download/washington-ave-pbd.zip")
try:
    raw = urllib.request.urlopen(urllib.request.Request(PBD_ZIP, headers=UA), timeout=60).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    (DATA / "pbd_shapefile").mkdir(exist_ok=True)
    for n in z.namelist(): (DATA / "pbd_shapefile" / n).write_bytes(z.read(n))
except Exception as e:
    print("PBD download failed (portal sometimes 403s); using data/pbd_shapefile/ copy:", str(e)[:60])
shp = shapefile.Reader(str(DATA / "pbd_shapefile" / "Washington_Ave_PBD.shp"))
g = shape(shp.shapes()[0].__geo_interface__)                     # EPSG:2278 (TX South Central, ft)
g = transform(Transformer.from_crs("EPSG:2278", "EPSG:4326", always_xy=True).transform, g)
(DATA / "pbd_boundary.geojson").write_text(json.dumps(
    {"type": "Feature", "properties": {"name": shp.records()[0][1]}, "geometry": mapping(g)}))
bb = g.bounds
# Analysis rectangle (matches Agent A context extract); PBD polygon stays the scoring boundary.
import os
RECT = [float(x) for x in os.environ.get("CURB_BBOX", "-95.433,29.758,-95.367,29.786").split(",")]
bb = tuple(RECT)
env = json.dumps({"xmin": bb[0], "ymin": bb[1], "xmax": bb[2], "ymax": bb[3], "spatialReference": {"wkid": 4326}})
print("PBD bounds", bb)

# 2. ArcGIS feature layers clipped to the PBD envelope --------------------
def pull(url, out, fields="*"):
    feats, off = [], 0
    while True:
        d = get(url + "/query", {"geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                                 "spatialRel": "esriSpatialRelIntersects", "outFields": fields, "outSR": 4326,
                                 "f": "geojson", "resultOffset": off, "resultRecordCount": 2000})
        f = d.get("features", []); feats += f
        if len(f) < 2000: break
        off += 2000
    (DATA / out).write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    print(out, len(feats))

COH = "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services"
pull(f"{COH}/HCAD_Parcels/FeatureServer/0", "parcels.geojson",
     "HCAD_NUM,Site_addr_,Site_addr1,State_Clas,Yr_Impr,Acreage,Land_Value,Improvemen")
pull(f"{COH}/COH_RoadCenterline/FeatureServer/0", "centerline.geojson",
     "centerlineid,roadclass,fullname,fromleft,toleft,fromright,toright,onewaydir")
pull(f"{COH}/Residential_Parking_Permit_3/FeatureServer/6", "rpp.geojson")
TDO = "https://geogimstest.houstontx.gov/arcgis/rest/services/TDO/Traffic_gx/MapServer"
pull(f"{TDO}/4", "adt_major.geojson")
pull(f"{TDO}/5", "adt_local.geojson")

# 3. ADT volumes from the related assignments table --------------------------
import datetime
st = json.load(open(DATA / "adt_major.geojson"))["features"] + json.load(open(DATA / "adt_local.geojson"))["features"]
rows = []
for i in range(0, len(st), 40):
    chunk = st[i:i+40]
    where = " OR ".join(f"LocationID='{f['properties']['GlobalID']}'" for f in chunk)
    d = get(f"{TDO}/22/query", {"where": where, "outFields": "LocationID,Date,ADT,Status,Direction", "f": "json"})
    rows += [r["attributes"] for r in d.get("features", [])]
by = {}
for a in rows:
    if a.get("ADT"): by.setdefault(a["LocationID"], []).append(a)
out = []
for f in st:
    p = f["properties"]; recs = sorted(by.get(p["GlobalID"], []), key=lambda a: a.get("Date") or 0)
    latest = recs[-1] if recs else None
    out.append({"station": p["StationID"], "address": p["ADDRESS"], "segment": (p.get("SEGMENT") or "").strip(),
                "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1],
                "adt": latest["ADT"] if latest else None,
                "date": datetime.datetime.fromtimestamp(latest["Date"]/1000, datetime.timezone.utc).date().isoformat() if latest and latest.get("Date") else None,
                "n_counts": len(recs),
                "source": f"{TDO}/22"})
json.dump(out, open(DATA / "adt_volumes.json", "w"), indent=1)
print("adt_volumes.json", len(out), "with volume:", sum(1 for o in out if o["adt"]))

# 4. 311 cases (public city feed) --------------------------------------------
allf = []
for svc, lid in [("311/D365_SR311_PROD", 0), ("311/D365_SR311_PROD", 1), ("311/D365_SR311_PROD", 2), ("311/Houston311_RecentServiceRequests", 4)]:
    u = f"https://mycity2.houstontx.gov/pubgis01/rest/services/{svc}/MapServer/{lid}/query"
    off = 0
    while True:
        try:
            d = get(u, {"geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                        "outFields": "CaseNumber,IncidentAddress,Latitude,Longitude,Status,CreatedDate,ClosedDate,Title,CaseType,Department",
                        "returnGeometry": "false", "f": "json", "resultOffset": off, "resultRecordCount": 2000})
        except Exception as e:
            print(svc, lid, "err", str(e)[:80]); break
        f = d.get("features", []); allf += [x["attributes"] for x in f]
        if len(f) < 2000: break
        off += 2000
seen = {}
for a in allf:
    k = a.get("CaseNumber") or a.get("CaseNumber365")
    if k and k not in seen: seen[k] = a
json.dump(list(seen.values()), open(DATA / "sr311_raw.json", "w"))
print("sr311_raw.json", len(seen))

# 5. METRO stops (GTFS static, official producer URL via mobilitydatabase.org) --
try:
    import csv
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(
        "https://metro.resourcespace.com/pages/download.php?ref=4835&ext=zip", headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read()))
    stops = []
    for r in csv.DictReader(io.TextIOWrapper(z.open("stops.txt"), encoding="utf-8-sig")):
        lon, lat = float(r["stop_lon"]), float(r["stop_lat"])
        if bb[0] <= lon <= bb[2] and bb[1] <= lat <= bb[3]:
            stops.append({"id": r["stop_id"], "name": r["stop_name"], "lon": lon, "lat": lat})
    json.dump(stops, open(DATA / "metro_stops.json", "w"), indent=1)
    print("metro_stops.json", len(stops))
except Exception as e:
    print("gtfs err", str(e)[:80])
