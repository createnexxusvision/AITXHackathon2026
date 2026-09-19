# Curb Fusion — Washington Ave Parking Benefit District

Overlay Houston public datasets on a common unit, **block face × hour of week**, to surface
curb-demand patterns no single dataset records. Deliverable: single-file Leaflet map with a
time-of-week scrubber, layer toggles, and a per-block-face stress score.
Track: Houston Open Data.

## Contents

```
data/
  pbd_boundary.geojson     PBD polygon, WGS84 (data.houstontx.gov, 2013)
  pbd_shapefile/           source shapefile, EPSG:2278
  parcels.geojson          4,203 HCAD parcels. Key field State_Clas:
                             A1 single-family, B1/B2 multifamily, F1 commercial,
                             C1/C2 vacant, X* exempt, Z* misc.
                             Also Acreage, Land_Value, Improvemen, Yr_Impr, Site_addr_
  centerline.geojson       658 road segments: fullname, roadclass,
                             fromleft/toleft/fromright/toright address ranges, onewaydir
  rpp.geojson              63 residential permit parking segments:
                             BLOCK, STREET (includes side), TIME "11PM-5AM", DAYS "WED-SAT", AREA
  adt_major.geojson        15 ADT count stations (location + SEGMENT; no volumes yet)
  adt_local.geojson        1 local-street ADT station
  handshake.txt            collab smoke-test log
scripts/
  pull_corridor_data.py    re-pulls all of the above from live public services; no auth
  hello_collab.py          appends a line to data/handshake.txt; run to confirm repo round-trip
docs/
  HANDOFF.md
```

Deps for scripts: `pip install pyshp shapely pyproj`

## Data sources

| Layer | Endpoint |
|---|---|
| PBD boundary | data.houstontx.gov package `washington-avenue-parking-benefit-district` |
| Parcels | `services.arcgis.com/NummVBqZSIJKUeVR/.../HCAD_Parcels/FeatureServer/0` |
| Centerline | `services.arcgis.com/NummVBqZSIJKUeVR/.../COH_RoadCenterline/FeatureServer/0` |
| Permit parking | `services.arcgis.com/NummVBqZSIJKUeVR/.../Residential_Parking_Permit_3/FeatureServer/6` |
| ADT stations | `geogimstest.houstontx.gov/arcgis/rest/services/TDO/Traffic_gx/MapServer/4,5` |

## Not yet pulled

| Source | How |
|---|---|
| 311 requests (one week, on hand) | drop into data/; join by address to block face via centerline ranges |
| OSM POIs, bus stops | Overpass, bbox = PBD bounds; `overpass-api.de` was 503 today, try `overpass.kumi.systems` |
| METRO stops | GTFS static from ridemetro.org, filter to bbox |
| ADT volumes | TDO layer 3 (Traffic Counts) by StationID, or layer 4 with all fields |
| Loading zones, valet zones | data.houstontx.gov packages `city-of-houston-active-commercial-vehicle-loading-zone-permits`, `city-of-houston-active-annual-valet-zones` (2015 XLS) |
| NAIP / H-GAC aerials | optional single observed-occupancy snapshot |
| ParkHouston meter transactions | not public; state as the intended input in README |
| Waymo trip density | not public; roadmap only |

## Build order

1. **Block faces.** Split centerline segments into L/R faces from the address-range fields.
   Face id: `<STREET>_<BLOCK>_<L|R>`.
2. **Parcels → faces.** Nearest face by centroid, same side. Per face: acreage by State_Clas,
   improvement value, parcel count.
3. **Demand curves.** One 168-entry hour-of-week vector per land-use class
   (F1 peaks Thu–Sat 21:00–02:00; A1/B* peak overnight; office 09:00–17:00).
   `demand[face][h] = Σ class_acres × curve[class][h]`. Lookup table, no ML.
4. **Regulation mask.** Parse rpp TIME/DAYS into a 168-bit mask per face.
   PBD permit hours: Thu–Sun 18:00–02:00.
5. **311 → faces.** Address → face via centerline ranges; bucket by hour of week.
6. **Supply.** `face_length_ft / 22` minus fixed uses (bus stop, loading, valet).
7. **`data/corridor.json`.** One record per face: geometry, demand[168], reg_mask[168],
   complaints[168], adt, supply.
8. **`src/index.html`.** Leaflet from cdnjs, loads corridor.json, hour slider, layer toggles,
   color = `demand − supply + w·complaints`. Two what-if sliders max (permit hours, valet zone on/off).
9. **README.** Track, problem, solution, customer, team. Name meter data as the missing input.

## Judging

Completeness 30, Track Fit 20, Value 25, Frontier 25. Working map on real city data with one
clear insight outscores a partial simulator. Submissions due 19:00.

## Framework (added)

- `docs/CONTRACT.md` — the `corridor.json` schema. Backend and frontend both code against it.
- `scripts/build_corridor.py` — first pass, produces `data/corridor.json` (317 faces, 0.9 MB) from the
  pulled GeoJSON: block faces, parcel land-use per face, demand curves, RPP + PBD regulation mask.
- `src/index.html` — skeleton Leaflet map consuming `corridor.json`: hour-of-week slider, layer toggles,
  one what-if control, hover readout. Serve with `python -m http.server` from repo root, open
  `http://localhost:8000/src/`.

### Split

**Backend** (owns `scripts/`, `data/`): join 311 to faces, fetch ADT volumes, add bus stops /
loading / valet to `fixed`, tune curves, keep `corridor.json` in contract.

**Frontend** (owns `src/`): styling, basemap/aerial layer, legend, side panel charts (per-face 168-hour
sparkline), more what-if controls, demo flow. Never reads anything but `corridor.json`.
