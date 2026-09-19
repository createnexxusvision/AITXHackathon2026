# Model — Agent B (core)

Producer: `scripts/core/build_core.py`. Constants: `data/core/assumptions.json`. Contract: `docs/DATA_CONTRACT.md` 1.0.0.
Extent: rectangle `[-95.433, 29.758, -95.367, 29.786]`; `in_analysis_area` marks PBD intersection.

## Faces
`face_id = <centerlineid>:<L|R>`, side relative to stored centerline direction. Display geometry = centerline
`parallel_offset` 26 ft in EPSG:2278. `length_ft` measured in EPSG:2278. `faces_version` = sha1 of ordered ids.

## Curb mode — `pressure_index` (0–100, uncalibrated)
```
D = min(1, demand_proxy[h] / demand_p95)            demand_p95 frozen over in-area faces
S = eligible_supply[h] / gross_capacity              = 0 when regulation_mask[h] (non-resident visitor), else 1
C = null                                            complaints coverage is partial_snapshot → dropped
pressure[h] = 100 × (0.60·D + 0.25·(1−S)) / 0.85
```
`demand_proxy[h] = Σ acres[class] × curve[class][h]`, curves in `classes[]`, vehicles-per-acre in A04. Hypothetical.
`gross_capacity = floor(length_ft / 22)`. No fixed exclusions applied (A10). Regulation: RPP rows (verified text,
start-day semantics) else, inside PBD only, the A08 scenario THU–SUN 18–02 (unverified, `confidence: low`).

## Raccoon mode — `forage_index` (0–100, hypothetical)
```
T = min(1, trash_311_total / trash_p95)      311 titles matching A13 within 300 ft, multi-year snapshot
R = min(1, residential_acres / res_p95)      A1+B1+B2 acres on the face  (bins proxy)
F = min(1, commercial_acres / com_p95)       F1 acres (dumpster proxy)
forage[h] = 100 × (0.5·T + 0.3·R + 0.2·F) × raccoon_curve[h]
```
`raccoon_curve`: nocturnal 21:00–05:00 peak, weekend ×1.2 (A15). Same faces, same scrubber, different index.
Raccoon mode exists to show the fusion layer is data-agnostic; nothing in it is an ecological claim.

## Reference calculations
1. Face with 1.0 acre F1, length 220 ft, no RPP, in PBD, Fri 22:00 (h=118): demand = 1.0×curve_F1[118] = 40;
   D = min(1, 40/demand_p95); S = 0 (PBD scenario active) → pressure = 100×(0.6D+0.25)/0.85.
2. Same face Mon 09:00 (h=9): curve_F1[9] = 0.05×40 = 2 → D = 2/demand_p95; S = 1 → pressure = 100×0.6D/0.85.
3. Face with trash_311_total = trash_p95, res_acres = 0, com_acres = 0, Fri 23:00 (h=119):
   T = 1 → forage = 100×0.5×raccoon_curve[119] = 100×0.5×1.2 → clamped by curve to ≤100 → 60.
Values of `demand_p95`, `trash_p95` are in `corridor.json.normalization`.

## Nulls
`demand_proxy`, `pressure_index`, `forage_index`: null when inputs absent. `regulation_mask`,
`eligible_supply_spaces`: null when no restriction all week (supply = gross_capacity). `complaints`: null when zero
matched; never a rate. `adt`: null or station+volume+date.
