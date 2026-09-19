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
    if params: url += "?" + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))

# 1. PBD boundary --------------------------------------------------------
PBD_ZIP = ("https://data.houstontx.gov/dataset/76b205f4-af6b-4c69-a50d-2f749ad9a61a/"
           "resource/44ee8e7f-ea31-454a-8221-299bc83956a3/download/washington-ave-pbd.zip")
raw = urllib.request.urlopen(urllib.request.Request(PBD_ZIP, headers=UA), timeout=60).read()
z = zipfile.ZipFile(io.BytesIO(raw))
shp = shapefile.Reader(shp=io.BytesIO(z.read("Washington_Ave_PBD.shp")),
                       dbf=io.BytesIO(z.read("Washington_Ave_PBD.dbf")),
                       shx=io.BytesIO(z.read("Washington_Ave_PBD.shx")))
g = shape(shp.shapes()[0].__geo_interface__)                     # EPSG:2278 (TX South Central, ft)
g = transform(Transformer.from_crs("EPSG:2278", "EPSG:4326", always_xy=True).transform, g)
(DATA / "pbd_boundary.geojson").write_text(json.dumps(
    {"type": "Feature", "properties": {"name": shp.records()[0][1]}, "geometry": mapping(g)}))
bb = g.bounds
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
