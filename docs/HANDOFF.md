# CurbFusion — Team Trash Pandas

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

## Repo layout (matches SHARED_BUILD_PLAN.md ownership)

```
data/core/{faces.geojson,manifest.json,assumptions.json}   B
data/corridor.json                                        B  (schema 1.0.0 + raccoon fields)
data/*.geojson, data/*_raw.json, data/*.json              B  raw pulls
scripts/pull_corridor_data.py, scripts/core/build_core.py B
docs/MODEL.md, agents/status/core-model.md                B
src/**, data/context/**, data/joins/**                    A
```
Unzip at repo root. Nothing in this zip touches A-owned paths except `src/index.html`, which is B's reference
viewer for the new schema; A may replace it.

## Frontend (B built, A restyles)

- `src/curbfusion.html` — single self-contained file, data inlined, opens by double-click, no server. This is the
  demo candidate. Rebuild after any data change: `python scripts/core/build_html.py`.
- `src/curbfusion.template.html` — the editable source; `__DATA__` is replaced at build. Restyle here.
- `data/corridor_lite.json` — compact UI packet (3.4 MB) written by `build_core.py` → lite step; `corridor.json` stays the contract artifact.
- `src/app.py` — Streamlit alternative reading the full `corridor.json`.
- Restyle freely: colors, raccoon art, panel layout, tiles. Keep the scoring functions (they mirror `scripts/core/model.py`).

## Product

- Team: **Trash Pandas**. Project: **CurbFusion**.
- Pitch: a block-face × hour-of-week fusion engine over Houston open data. Curb mode scores curb pressure for
  planners; Raccoon mode scores the same faces for trash-foraging potential using the same 311 feed. Two modes,
  one engine, proves the layer is data-agnostic. Serious tool, memorable demo.
- Track: Houston Open Data.

## Frontend wants (from the human on team B)

- Raccoon iconography: logo, mode toggle, side-panel mascot, optional raccoon markers on top forage faces at night.
- Zoomed-out default view over the whole rectangle (Heights / Washington / Sixth Ward / near downtown); PBD outline drawn but not the hero.
- Mode switch Curb ⇄ Raccoon swaps `pressure_index` ⇄ `forage_index`, legend, and presets; same scrubber.
- If a layer does not read well at the wide zoom (e.g. per-face lines at z13), aggregate or thin it and say so; do not fake density.
- Hover/click: `display_label`, mode index, components, `confidence`, ADT if present.

## Demo story

1. Raccoon mode, Fri 11 PM: trash-311 hot spots light up in the Heights side streets.
2. Flip to Curb mode, same hour: pressure moves to Washington Ave commercial faces under the permit scenario.
3. Same data, same faces, two users. Then the ask: meter transactions and a complete 311 window turn the scenario into a measurement.
