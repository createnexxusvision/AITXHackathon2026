# Curb Fusion data contract — 1.0.0

Owner: Agent A (context/UI/integration). Producer of canonical faces and final corridor model: Agent B. This specification is the initial integration baseline; B acknowledgment is pending. Breaking changes require a version bump and a documented consumer migration before merge.

## Common rules

- UTF-8 JSON; GeoJSON coordinates `[longitude, latitude]` in EPSG:4326. No private contact information or unreviewed narrative text.
- Timestamps are ISO 8601 with offset; retrieval times use UTC. Typical-week vectors use local `America/Chicago`, Monday 00:00 index 0; length exactly 168.
- `null` = unknown/unavailable. `0` = computed or observed zero under documented coverage. Empty data is not evidence of absence.
- IDs are strings. Duplicate IDs fail validation. Provenance links are absolute source URLs.
- All outputs include a manifest recording `schema_version`, `generated_at`, source IDs, source vintage, retrieval date, license/terms URL, geographic scope, feature/row counts, completeness, assumptions and producer Git commit. Missing dates are null, not invented.

## B → A: `data/core/faces.geojson`

GeoJSON FeatureCollection. Each feature has LineString geometry representing the selected left/right face and these properties:

| Field | Type / meaning |
|---|---|
| `face_id` | Stable `<source_segment_id>:L` or `:R` |
| `source_segment_id` | Canonical centerline identifier |
| `side` | `L` or `R`, relative to source geometry order |
| `street`, `display_label` | Human-readable names; not primary keys |
| `address_low`, `address_high` | Integer or null; normalized bounds |
| `address_parity` | `even`, `odd`, `both`, `unknown` |
| `length_ft` | Nonnegative number; measured in verified projected units |
| `in_analysis_area` | Boolean; PBD intersection membership under documented rule |
| `geometry_basis` | Method and any curb offset assumptions |
| `source_version` | Stable identifier/hash of centerline and boundary versions |

Companion `data/core/manifest.json` supplies `faces_version`, source CRS and measurement/conversion method. Never silently regenerate IDs from row position. Splits or direction changes require an ID migration table.

## A-owned context outputs

- `data/context/requests.geojson`: selected request ID, category, status, created/closed timestamp, address and point geometry; no resolution narratives or contact data. Manifest distinguishes multiyear OPEN-layer snapshot from any separate one-week extract.
- `data/context/stops.geojson`: stop ID, name, source route labels and original geometry; route labels are snapshot attributes.
- `data/context/hin.geojson`: historical source segment ID, road name, original geometry and documented source attributes; full-segment measures are not clipped-area counts.
- `data/context/cameras.geojson`: name, location, direction, geometry and official viewer URL; no redistributed imagery/video.
- `data/context/roads.geojson`, `buildings.geojson`, `corridor.geojson`: OSM contextual features with OSM IDs, license attribution and height basis where applicable.
- `data/context/manifest.json`: per-layer source URLs, timestamps, bounds, counts, field mappings and quality/completeness flags. Initial raw-style field names are permitted only when the mapping is documented; the joins below use normalized fields.

## A → B: face joins

`data/joins/complaints_by_face.json` and `transit_by_face.json` are objects with `schema_version`, `faces_version`, `generated_at`, `source_ids`, `coverage` and `records`.

Complaint records contain `face_id`, `counts_by_hour` (168 nonnegative integers or nulls), `observed_weeks_by_hour` (168 nonnegative integers), `category_filter`, `window_start`, `window_end`, `matched_request_count`, `ambiguous_request_count` and `join_method_summary`.

Coverage identifies the extraction type: `complete_window`, `partial_snapshot`, or `unknown`. A multiyear open-case extract **cannot** claim complete observation weeks; its weekly exposure denominator is unknown and its counts must not be represented as incident rates. It may remain an inspection overlay while the scored complaint component is null. Report-time bins are not incident-time bins.

Transit records contain `face_id`, `nearby_stop_ids`, `distances_m` and `join_method`. Proximity is contextual: it does not assign an unverified bus-stop exclusion length. B owns physical supply exclusions.

Both files include total matched/unmatched/ambiguous records in coverage. Every output face ID must exist in the exact `faces_version`. No positional joins.

## B → A: `data/corridor.json`

Top-level object:

```text
schema_version: "1.0.0"
generated_at: ISO timestamp
faces_version: string
timezone: "America/Chicago"
hour_origin: "Monday 00:00"
analysis_boundary: relative path + version
source_manifest: relative path
assumptions_version: string
normalization: fixed baseline population, reference percentiles, weights
coverage: completeness and limitations
faces: array of records below
```

Each face record:

| Field | Type / interpretation |
|---|---|
| `face_id`, `street`, `display_label`, `side` | Copied from canonical faces |
| `geometry` | GeoJSON LineString |
| `length_ft` | Number ≥ 0 |
| `parcel_summary` | Parcel count, acreage by original class, join quality; no raw owners |
| `demand_proxy` | 168 numbers ≥ 0 or null; explicitly hypothetical units |
| `regulation_mask` | 168 booleans or null; active restriction, not occupied curb |
| `regulation_rules` | Source text, verified status, start-day semantics and eligible user class |
| `complaints` | 168 counts or null; source window and coverage accompany record |
| `gross_capacity_spaces` | Nonnegative integer or null, with geometric assumption |
| `fixed_exclusions` | Verified interval union plus source; unknown exclusions remain flagged |
| `eligible_supply_spaces` | 168 nonnegative numbers or null for declared user class |
| `adt` | Null or station ID, measured volume, units, measurement period and source; station alone is not ADT |
| `nearby_stop_ids` | Array of authoritative source stop IDs |
| `pressure_index` | 168 numbers 0–100 or null; uncalibrated relative index |
| `components` | Demand/supply/complaint terms, weights used and missing inputs |
| `confidence` | `high`, `medium`, `low`, `unknown`, plus reasons; not statistical confidence |
| `source_ids`, `assumption_ids` | Links to provenance and assumption records |

## Scenarios and ownership

B defines the scoring formula, baseline references, allocation rules and at least three reference calculations in `docs/MODEL.md` / `data/core/assumptions.json`. A implements browser calculations for the two permitted controls and checks against B's reference cases; A does not invent a competing model. If shared executable scoring logic is needed, B owns `scripts/core/model.js` as a pure module; A imports it rather than editing it.

Scenario state stays separate from observed baseline data and resets cleanly. Changing permit hours means a **hypothetical policy scenario**, never a claim that a legal rule changed. Unverified valet/loading data can only support a clearly hypothetical allocation. Report baseline and scenario assumptions together.

## Validation / readiness

B validates faces, lengths, arrays, rules, math and final output; A validates context, joins, contract compatibility and UI behavior. Reject unknown schema versions rather than silently guessing. Neither agent should populate placeholder values to satisfy the schema.

Ready sequence: B publishes faces version → A publishes joins referencing it → B publishes corridor version → A integrates UI and compares reference calculations → release. Each producer records its exact output commit in its own status file.
