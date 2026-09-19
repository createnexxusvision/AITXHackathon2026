# Curb Fusion / Washington Avenue Digital Twin — shared build plan

**Coordination baseline: 2026-09-19. Track: Houston Open Data.**

This is the shared implementation plan for the two collaborating agents in `createnexxusvision/AITXHackathon2026`. It combines the user's digital-twin request and expanded dataset roadmap with the partner's Curb Fusion handoff. The original handoff is preserved in `docs/PARTNER_HANDOFF_ORIGINAL.md` as source material, not as a second active task list. This plan defines the division of work requested by the user; the partner agent has not yet acknowledged it.

## 1. One product and one MVP

**Curb Fusion** is the first use case of the Washington Avenue digital twin: an interactive map of the Washington Avenue Parking Benefit District (PBD), organized by **block face × hour of week**, to explore modeled curb pressure alongside actual land use, parking rules, transit access, service requests, and historical safety context.

Primary users: district managers, city planners, and neighborhood stakeholders investigating where curb uses may conflict. The demo should answer: **Which block faces warrant investigation on a selected evening, what evidence supports that, and how does a clearly labeled allocation scenario change the model?**

Build one static Leaflet application at `src/index.html`, supported by generated JSON/GeoJSON. Keep the partner's lightweight frontend architecture; Agent A ports useful styling from its local MapLibre shell into this interface. Do not continue two independent map apps. The broader 3D digital twin remains a staged extension.

The MVP is an evidence explorer with an **uncalibrated scenario model**, not measured parking occupancy, a live traffic simulator, or a forecast of congestion/revenue. Dataset availability constrains claims.

### Scope boundaries

- The partner's PBD polygon is the canonical scoring/aggregation boundary after source validation. Preserve its 2013 source vintage; do not imply the district has unchanged legal boundaries today.
- Agent A's existing contextual extract uses WGS84 bounds `[-95.433, 29.758, -95.367, 29.786]`, covering Washington Avenue and nearby streets. It is a retrieval rectangle, not the PBD or an official neighborhood boundary.
- Show context outside the PBD, but compute face-level summaries only for the declared analysis area. Preserve partially intersecting segments and explain clipping/aggregation treatment.
- MVP controls: one hour-of-week scrubber, layer toggles, block-face selection, and at most two what-if controls: scenario permit hours and a selected hypothetical valet/loading allocation.
- No blockchain, authentication, Supabase, LLM agent, or revenue predictor is required for this MVP. Earlier brainstorm documents remain future concepts, not additional implementation requirements.

## 2. What exists now — do not rebuild it blindly

Verified shared-repository baseline at inspection: `main` at `7912cb6`, with README, scaffold, hackathon information, and brainstorm documents. The partner's listed data/scripts were **not present on that inspected main branch**. Both agents must fetch again before beginning work; this is a time-stamped observation, not a claim about later commits.

| Asset | Status at reconciliation | Next action / owner |
|---|---|---|
| PBD polygon + EPSG:2278 shapefile | Partner reports completed; not verified in shared main | B publishes existing files with source metadata |
| 4,203 HCAD parcels | Partner reports completed | B verifies source, date, schema and counts; publishes |
| 658 centerline segments | Partner reports completed | B publishes; this is the block-face geometry source |
| 63 residential-permit segments | Partner reports completed | B publishes raw time/day attributes and provenance |
| 15 major + 1 local ADT stations | Partner reports locations; no measured volumes yet | B retains null volumes; retrieves counts if available |
| `pull_corridor_data.py`, collaboration smoke test | Partner reports existing locally | B publishes; smoke test optional, not a prerequisite |
| 9,495 OSM street/path ways; 67 Washington Avenue ways | A downloaded and converted locally | A publishes under `data/context/`; context only, not replacement centerlines |
| 14,229 closed OSM building ways | A converted locally | A publishes; relation footprints missing; 3D postponed |
| 273 city-hosted METRO stop points | A downloaded and verified locally | A publishes stop snapshot and source metadata |
| 1,776 source 311 rows → 1,711 unique request IDs | A downloaded/deduplicated locally | A audits duplicates and publishes normalized 311 plus join adapter |
| 50 High Injury Network source segments | A downloaded locally | A publishes historical layer; full segments may extend beyond bounds |
| 19 TranStar camera index entries | A extracted locally | A publishes locations and official viewer links, not camera pixels |
| Source manifest and data-preparation script | A created locally | A publishes in owned context paths, preserving known limitations |
| Dark map UI HTML/CSS | A created locally | A reuses styling in the single Leaflet frontend |
| Working map, time scrubber, scoring engine, end-to-end demo | **Not built/verified at reconciliation** | Follow milestones below |
| Hosting | A registered an unpublished private Site; no deployment exists | A alone owns release; shared GitHub remains source of truth |

Agent A's context snapshot was prepared at `2026-09-19T19:12:14Z`. Its 311 created dates span **2023-06-05 to 2026-05-28**; only the service's OPEN layer returned records in the rectangle. This is neither a fresh last-week feed nor a complete historical archive. The partner reports a separate one-week 311 extract; preserve it separately and compare provenance before merging. The source manifest and counts describe local work until the corresponding GitHub commits land.

## 3. Exclusive ownership — two agents, no overlapping files

**Agent A = this conversation's digital-twin/context/UI agent.**
**Agent B = the partner's Curb Fusion/core-model agent.**

| Deliverable / path | Sole writer | Other agent's interface |
|---|---|---|
| `src/**` — single Leaflet UI, controls, inspection, scenario display | A | B supplies `corridor.json` and model explanations |
| `data/context/**` — stops, 311, HIN, cameras, OSM, imagery metadata | A | B reads normalized outputs; never repulls these sources independently |
| `scripts/context/**`, `tests/context/**` | A | B consumes published schema and snapshot manifest |
| `data/joins/complaints_by_face.json`, `data/joins/transit_by_face.json` | A | B reads these to assemble corridor artifact |
| `data/pbd_boundary.geojson`, `data/pbd_shapefile/**`, `data/parcels.geojson`, `data/centerline.geojson`, `data/rpp.geojson`, `data/adt_major.geojson`, `data/adt_local.geojson` | B | A reads; does not rewrite/reclip in place |
| `scripts/pull_corridor_data.py`, `scripts/core/**`, `tests/core/**` | B | A invokes documented entrypoints only |
| `data/core/**` — faces, parcel joins, regulations, supply, demand assumptions | B | A reads geometry and IDs for context joins |
| `data/corridor.json` — final merged model output | B | A consumes; requests schema changes through contract document |
| `docs/MODEL.md`, `data/core/assumptions.json` | B | A displays model assumptions verbatim or faithfully summarized |
| `docs/SHARED_BUILD_PLAN.md`, `docs/DATA_CONTRACT.md`, `docs/DATA_SOURCES.md`, root `AGENTS.md`, README | A (integration owner) | B proposes contract changes in its PR; no simultaneous edits |
| `agents/status/context-ui.md` | A | B reads readiness and blockers |
| `agents/status/core-model.md` | B | A reads readiness and blockers |
| Build/package/deployment config and release | A | B supplies model/data, never creates a second Site |
| Loading/valet historical datasets and ADT volume follow-up | B | A renders only verified or explicitly historical data |
| Future LiDAR/flood/pedestrian context acquisition | A | B consumes after new milestone is activated |

The partner's handoff originally included UI work. **This plan transfers UI ownership to A** so B can finish the model without a competing renderer. B should publish any already-written UI on its branch for A to reuse, then stop editing `src/**`. Do not discard someone else's unmerged work.

### Git coordination protocol

1. Read root `AGENTS.md`, this plan, and `docs/DATA_CONTRACT.md`; fetch `origin` and inspect current branches/PRs.
2. Use separate branches/checkouts: suggested A branch `agent/context-ui`, B branch `agent/curb-model`. Reuse an existing role branch if already active. Never share a writable checkout.
3. Each agent publishes its own status file with role, active branch, owned paths, current task, output commit SHA, contract version, blockers and next handoff. Only that agent edits its status file.
4. Commit narrowly and open PRs with changed paths, data vintage, schema version and validation results. Never force-push shared main or overwrite another agent's files to resolve a conflict.
5. A coordinates integration. The initial coordination documents may land directly on main at the user's request; application/data work goes through role branches. A does not merge breaking changes silently.
6. Cross-owner changes: describe the need in the PR or status file; the owner implements it. A dependency wait is not permission to edit the owner's output.
7. Missing artifacts remain missing. Work against the contract with clearly labeled test fixtures under tests; never publish fixture records as observed data.
8. Announce readiness via a committed status record/PR. Do not send external messages or act as if the partner has acknowledged this plan when it has not.

## 4. Shared contract and critical modeling corrections

The exact handoff is specified in `docs/DATA_CONTRACT.md`, version **1.0.0**. A owns the contract document; B owns generation of the final model.

### Face identity and geometry

- Use a stable source segment identifier plus `L`/`R` relative to stored centerline direction: `<source_segment_id>:<L|R>`. Store the source and direction. The handoff's `<STREET>_<BLOCK>_<L|R>` becomes a display label because it can collide when a block is split into several segments.
- Preserve left/right address ranges and parity where reliable; do not assume an even/odd side convention globally. If geometry is reversed, side labels/ranges must reverse with it.
- Derive face display geometry consistently and measure length in a suitable local projected CRS. Verify EPSG:2278's units before conversion; never measure feet directly from longitude/latitude.
- Parcels join by frontage/address plus spatial side when possible. Centroid-nearest is a fallback with recorded confidence; corner lots, large parcels and ambiguous frontages must not silently duplicate acreage onto multiple faces.

### Time and regulations

- All 168-entry vectors use **Monday 00:00 = index 0**, local `America/Chicago` wall-clock time. They represent a typical week, not a dated forecast. Convert actual request timestamps to local time before bucketing; repeated DST hours share a bin, and dates/coverage remain available.
- Parse overnight rules across midnight. Under start-day semantics, WED 23:00–05:00 means Wednesday hour 23 and Thursday hours 0–4. Validate the source's intended day semantics before activating a rule.
- Preserve RPP `WED–SAT 23:00–05:00` from the handoff separately from its asserted PBD `THU–SUN 18:00–02:00`. They are different claims, not interchangeable rules. The latter is **unverified**, not the baseline law. Until verified, it may be a labeled scenario assumption only.
- Restriction, resident eligibility and physical supply are separate concepts. An active residential restriction does not remove the physical curb for eligible residents. Unknown rules are not “unrestricted.” This is not legal parking guidance.

### Demand, supply and pressure

- HCAD `F1` commercial does not identify restaurant, nightlife or office use on its own. Preserve raw classifications; use validated POIs or an explicit commercial proxy. The proposed nightlife/office curves are hypothetical lookup assumptions, not observations or ML predictions.
- **Do not compute acreage-based demand minus parking spaces.** Either calibrate demand to common units or use a transparent dimensionless relative index for the MVP.
- Suggested MVP index: `D = min(1, demand_proxy / fixed_baseline_p95)`; `S = eligible_supply / max(gross_capacity, 1)`; `C = min(1, observed_category_count / fixed_baseline_complaint_p95)`; `pressure = 100 × (0.60 D + 0.25 (1 − S) + 0.15 C)`. Weights and baseline reference population belong in assumptions. They are illustrative, not validated.
- When the complaint component is unavailable, use `null`, remove its weight and renormalize the remaining weights; lower the reported coverage. Zero means observed zero in a documented window. Handle zero reference percentiles explicitly; if essential demand/supply are unknown, pressure is null.
- Freeze normalization against a declared baseline version; do not recompute it as sliders move, which would hide real scenario differences. Display component values and weight choices on selection.
- `floor(usable_curb_ft / 22)` is a rough capacity assumption, not an inventory of legal spaces. Exclude measured fixed-use intervals only after verification, union overlapping exclusions, and clamp results at zero. A bus-stop point alone does not define a no-parking length.
- Unknown loading/valet dimensions and unverified regulations lower confidence. Scenario allocations use user-visible hypothetical dimensions. No numerical occupancy, revenue, crash reduction or congestion prediction is claimed.

### 311, safety and imagery

- A matches 311 to B's immutable face IDs using normalized street name, address ranges and available coordinates. Record method/confidence/distance; ambiguous requests stay unmatched. Keep all-category maintenance context separate from a documented parking/curb complaint subset used in scores.
- Report time is not the time the physical problem occurred. Old open-status cases are not current observations. Do not silently mix the existing multiyear open extract with the partner's one-week extract.
- Safety segments summarize historical 2018–2022 source data, not point crashes today. Overlap with a face establishes context, not causation.
- NAIP is aerial orthophotography, not live satellite imagery. No parking occupancy is inferred from it without visible acquisition time, adequate resolution and manual validation.
- Waymo trips and ParkHouston transactions are unavailable inputs. Keep them in the roadmap; never fabricate feeds.

## 5. Build sequence and handoffs

| Gate | Agent B | Agent A | Done when |
|---|---|---|---|
| G0 — acknowledge ownership | Publish status; surface any active conflicting files | Publish plan/contract; inventory local work | Both role status files identify branches; conflicts resolved |
| G1 — publish existing evidence | Publish original six core datasets and pull script with metadata | Publish existing context snapshots and preparation/refresh scripts | Files exist in GitHub with counts, source URLs, dates and licenses |
| G2 — freeze faces | Generate faces, stable IDs, PBD boundary and parcel/regulation joins | Port UI shell to Leaflet; load available context independently | `faces.geojson` passes geometry/ID tests; no competing UI |
| G3 — enrich faces | Build demand/supply assumptions; retrieve ADT volumes if feasible | Produce complaint and transit joins against frozen face version | Join files have matching face IDs, coverage and ambiguous/unmatched counts |
| G4 — assemble and interact | Generate final `corridor.json` and model report | Connect time scrubber, pressure styling, inspection and two scenarios | Changing hour/scenario changes model deterministically; observations remain unchanged |
| G5 — validate and release | Validate core math/time rules; deliver model caveats | Validate combined app, source disclosure, mobile/desktop; package/release | Single working demo, GitHub source commit, no mislabeled live or fabricated data |

**Fallback:** if G3 is blocked, ship the real-data map and an explicitly incomplete model, with null pressure where inputs are missing. Do not replace missing observations with invented data. Freeze optional additions before they jeopardize the working demo. The repo lists a 19:00 submission deadline; use current event confirmation for any deadline decision.

## 6. Dataset roadmap — retained, prioritized, assigned

| Priority / dataset | Purpose | Owner | Gate / current limitation |
|---|---|---|---|
| MVP PBD, parcels, official centerlines | Canonical analysis geography and land-use context | B | Publish partner's existing work; verify 2013 boundary vintage |
| MVP RPP + historical loading/valet permits | Timed curb-use evidence | B | Keep 2015 spreadsheets historical; validate current applicability |
| MVP 311 + METRO stops | Service needs and transit access | A | Snapshots exist; face joins pending |
| MVP HIN + camera locations | Safety context and access to public traffic views | A | Existing snapshots; no camera-derived counts |
| MVP ADT stations and available counts | Traffic context | B | Station locations are not measured traffic volumes |
| Next: TxGIO LiDAR + orthophotos | Terrain, building heights, canopy and later shade | A | Check local survey date, classification, datum, units and rights |
| Next: footprints / 3D massing | Extend twin to 3D after curb MVP | A | OSM footprints exist; tagged/derived/default heights distinguished; do not restart a second app |
| Next: sidewalks, crossings and pedestrian paths | Walking connections to stops and destinations | A | Missing mapped line does not prove missing sidewalk or ADA noncompliance |
| Next: FEMA / Harris County floodplains | Flood exposure context | A | Not real-time inundation; verify effective map dates |
| Next: drainage/elevation and flood-related 311 | Investigate recurrent maintenance patterns | A | No flood-depth forecast without hydrologic calibration |
| Next: H-GAC counts, speeds and vehicle classes | Calibrate transport scenarios | B | Location/time coverage unverified; observed intervals required |
| Later: METRO realtime + TranStar live traffic | Live situational context | A access/adapters; B model consumption | Registration/agency access required; no client-side keys |
| Later: ParkHouston meter transactions | Calibrate actual occupancy/turnover/revenue proxies | B | Not public in the handoff; authorized data partnership required |
| Later: Waymo trip/sensor data | Optional mobility context | A | No verified public corridor feed; non-commercial research terms are separate |
| Later: event/POI classification | Improve commercial demand assumptions | B | Validate actual POI use and opening hours; do not label all F1 nightlife |
| Later: calibrated policy simulation | Test bus priority, crossings and lane/curb allocation | B model; A UI | Requires validated baseline, uncertainty and adequate traffic/curb observations |

Source entry points: [TxGIO](https://www.tnris.org/research-distribution-center/), [StratMap](https://tnris.org/stratmap/index.html), [Houston Vision Zero](https://www.houstontx.gov/visionzero/), [Harris County flood maps](https://www.harriscountyfemt.org/), [H-GAC Data Lab](https://datalab.h-gac.com/), [H-GAC planning map](https://datalab.h-gac.com/planning/), [METRO developer portal](https://api-portal.ridemetro.org/), [TranStar API](https://traffic.houstontranstar.org/api/api_doc.aspx), [Washington Avenue Corridor Study](https://engage.h-gac.com/wacs).

## 7. Acceptance checks and demo

Core: stable unique face IDs; correct left/right orientation; projected lengths/units; no duplicate parcel acreage; midnight/week rollover tests; arrays exactly 168 entries; supply never negative; null/zero distinguished; complete source/version metadata; scores finite and reproducible where eligible.

Context: deduplication audit; geographic bounds; source schema checks; no narrative/contact fields in 311 extracts; per-source pagination/completeness; no unmatched face IDs; timestamp conversion and observed-week coverage; authoritative stops remain distinguishable from any OSM alternative.

Interface: one map opens on real data; hour and scenario controls work; selecting a face explains observed versus assumed inputs; empty/error/unknown states are explicit; source/vintage panel available; mobile and keyboard controls usable; no UI claims that station locations are ADT volumes or models are live measurements.

Demo: open the PBD → select an actual face → inspect parcels, rules, stops and complaint coverage → compare daytime with a weekend evening's **modeled** demand → change one hypothetical allocation → show component changes and uncertainty → identify a field-validation question. Report an actual discovered insight only after the data supports it.

## 8. Immediate next tasks

**B:** read this plan and contract; publish `agents/status/core-model.md`; push existing core data/scripts; generate stable `faces.geojson`; confirm regulatory semantics and dimensions before scoring. Do not build the UI or independently fetch A-owned context sources.

**A:** publish coordination docs and a status file first; migrate already-created context assets into owned GitHub paths; port the local shell into the single Leaflet frontend; wait for frozen faces before publishing face joins. Do not replace B's centerlines, derive competing faces, or edit B's model output.

Neither agent is expected to implement every roadmap dataset before the MVP. Ownership is effective as the user's requested coordination plan; partner acknowledgment and data publication remain explicit checkpoints.
