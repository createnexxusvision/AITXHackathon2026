# Data contract: `data/corridor.json`

Single file the frontend loads. Backend produces it with `scripts/build_corridor.py`.
Change this file before changing either side.

## Top level

```json
{
  "meta": {
    "generated": "2026-09-19T20:10:00",
    "bbox": [minlon, minlat, maxlon, maxlat],
    "hours": 168,
    "hour0": "Monday 00:00",
    "sources": {"parcels": "HCAD_Parcels 2023", "rpp": "...", "311": "..."}
  },
  "classes": {
    "F1": {"label": "Commercial", "curve": [168 floats 0..1]},
    "A1": {"label": "Single-family", "curve": [...]},
    "...": {}
  },
  "faces": [ Face, Face, ... ]
}
```

## Face

```json
{
  "id": "WASHINGTON_2500_L",
  "street": "WASHINGTON AVE",
  "block": 2500,
  "side": "L",
  "geom": [[lon, lat], [lon, lat], ...],
  "length_ft": 412.0,
  "supply": 16,
  "fixed": {"bus_stop": 0, "loading": 0, "valet": 0},
  "landuse": {"F1": 1.85, "A1": 0.0, "B2": 0.3},
  "demand": [168 floats, arbitrary units, comparable across faces],
  "reg": [168 ints: 0 open, 1 metered, 2 permit-only, 3 no-parking],
  "reg_source": "PBD Thu-Sun 18-02",
  "complaints": [168 ints],
  "adt": 18400,
  "stress": [168 floats]
}
```

Rules:
- `geom` is the face line offset ~8 m from the centerline toward that side, WGS84.
- Hour index `h = weekday*24 + hour`, weekday 0 = Monday.
- `supply` = floor(length_ft / 22) − sum(fixed). Never below 0.
- `landuse` values are acres per State_Clas; classes absent from `classes` are ignored by the frontend.
- `demand[h]` = Σ landuse[c] × classes[c].curve[h]. Units are relative; frontend normalizes.
- `stress[h]` = demand[h]/max(supply,1) + w_c × complaints[h]. `w_c` in meta; frontend may recompute.
- `complaints` all zeros until 311 is joined. Frontend must handle absent keys: `adt`, `complaints`, `fixed`.

## Frontend obligations

- Load `data/corridor.json` only. No other network calls except tiles and cdnjs.
- Toggles per layer: demand, regulation, complaints, supply. Slider over `h` 0..167.
- Colour by `stress[h]`; grey out faces where `reg[h] == 3`.
- What-if controls modify `reg` or `fixed` in memory and recompute `stress` client-side using the
  same formula. No backend round-trip.

## Backend obligations

- `build_corridor.py` is idempotent and runs on `data/*.geojson` only.
- New datasets add a key to Face; existing keys keep their meaning.
- Keep the file under 5 MB. Round coordinates to 6 dp, floats to 3 dp.
