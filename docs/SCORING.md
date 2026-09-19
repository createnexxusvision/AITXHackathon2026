# Scoring recipes

Every score is the same shape:

```
score[h] = 100 × ( Σ w_i · component_i / Σ|w_i| ) × max( curve_c[h] for c in curves )
```

Components are per-face numbers in 0..1, computed once in `build_core.py` from the joined datasets.
Curves are 168-hour shapes in `corridor.json.curve_table`. A recipe is just weights + curve names
(`data/core/recipes.json`). Adding a persona is a JSON edit, not code.

## Components (per block face)

| Component | Source | Meaning |
|---|---|---|
| `res` | HCAD parcels | residential acres fronting the face (bins on the curb) |
| `com` | HCAD parcels | commercial acres (dumpsters, restaurants, late activity) |
| `trash311` | 311 | trash / dumping / missed pickup / nuisance cases within 300 ft |
| `parking311` | 311 | parking violation / meter cases |
| `missed` | SWM Routeware exceptions | missed-collection reports at the face |
| `roadkill` | SWM dead-animal collection | pickups at the face (danger signal) |
| `trees` | 311 tree trim/removal | big-tree proxy (denning) |
| `adt_low` / `adt_high` | Public Works ADT | traffic volume, inverted or not |
| `stops` | METRO GTFS | bus stops on the face |
| `capacity` | centerline | `floor(length/22)` spaces |
| `restricted` | RPP + PBD scenario | any permit restriction during the week |

## Curves

| Curve | Shape |
|---|---|
| `night_before:<d>` | 1.0 from 20:00 the evening before pickup day `d` through 06:00 of day `d`; from SWM garbage / recycling / yard-waste polygons per face |
| `nocturnal` | raccoon activity, 21:00–05:00 peak, weekends ×1.2 |
| `late` | 22:00–02:00 |
| `commercial` | HCAD F1 demand curve, normalised |
| `flat` | 1.0 |

## Recipes shipped

| id | who | recipe | what it surfaces |
|---|---|---|---|
| `raccoon_bachelor` | 🦝 | trash311 + com + res + missed × (garbage_night ∪ commercial) | bins out tonight, dumpsters always: eat and leave |
| `raccoon_family` | 🦝🦝🦝 | res + trees + adt_low + trash311 + missed × (garbage_night ∪ recycling_night) | two supply nights a week, big trees, quiet street, low roadkill |
| `raccoon_date_night` | 🦝💘 | trash311 + com + missed × (late ∪ nocturnal) | where the other raccoons already are, near the bars |
| `raccoon_buffet` | 🦝🛋️ | res + missed + trash311 × (yard_night ∪ garbage_night) | heavy-trash / yard-waste nights |
| `human_resident_11pm` | 🚗 | capacity + restricted + adt_low × late | where a resident still finds curb after the commercial peak |
| `human_delivery_driver` | 📦 | com + capacity + adt_high × commercial | commercial frontage with room, during business hours |
| `human_311_hotspot` | 🏛️ | parking311 + missed + trash311 × flat | one face, three complaint types, one crew visit |

Plus the two contract indices: `pressure_index` (curb) and `forage_index` (raccoon), which are the same idea with
frozen p95 normalisation.

## Why the raccoons

No dataset in Houston measures "good night for a raccoon." Garbage day is in one polygon layer, missed pickups in
another table, dumpster density is implied by parcel class, tree cover by a 311 category, danger by a dead-animal
pickup log. Each is useless alone. On a shared block-face × hour grid they compose into an answer in one JSON edit.

Swap the weights and the same grid answers a resident at 11 PM, a delivery driver, a solid-waste supervisor, a
planner. That is the product: the grid and the joins. The raccoon is the proof that any question fits.

## Caveats
All components are proxies; all curves are assumptions (`data/core/assumptions.json`). 311 coverage is a
multi-year open-case snapshot, not a complete window. Nothing here is ecological or legal guidance.
