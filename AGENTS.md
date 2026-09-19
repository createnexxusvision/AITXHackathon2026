# Shared agent coordination

This repository builds **Curb Fusion**, the Washington Avenue digital twin's first curb-management use case. Read `docs/SHARED_BUILD_PLAN.md` and `docs/DATA_CONTRACT.md` before editing. User instructions take precedence.

## Roles

- **Agent A — context/UI/integration:** the agent that prepared the Washington Avenue public-data twin and this coordination plan. Owns `src/**`, `data/context/**`, `data/joins/**`, `scripts/context/**`, `tests/context/**`, root README/build/release configuration, coordination docs and `agents/status/context-ui.md`.
- **Agent B — partner/core model:** the agent that prepared the Curb Fusion handoff. Owns original PBD/parcels/centerline/RPP/ADT files, `data/core/**`, `data/corridor.json`, `scripts/pull_corridor_data.py`, `scripts/core/**`, `tests/core/**`, `docs/MODEL.md`, and `agents/status/core-model.md`.
- Unknown role: inspect current role status and task context; do not assume another role or overwrite unclaimed-looking shared output. A coordinates any ownership changes.

## Workflow

1. Fetch and inspect current main/PRs before edits. Use separate role branches and checkouts; never share a writable checkout or force-push shared main.
2. Update only your own status file with branch, active paths, current task, commit-based handoff, blockers and contract version. Do not claim partner acknowledgment or completion on their behalf.
3. Do not edit another role's paths. Propose a change through the PR/status record for the owner to implement. Preserve already-written partner work on its branch rather than deleting it.
4. A is the sole UI writer and release integrator. Use one Leaflet app, not a parallel MapLibre/3D MVP. B supplies model/geometry; A supplies context and consumes the final contract.
5. Freeze canonical face IDs before context joins. Only B writes `data/corridor.json`. Never replace missing inputs with invented observations.
6. Application/data changes go through focused PRs; describe changed paths, data dates, schema version and checks. Initial additive coordination documentation may land on main at the user's request once repository write access is available.
7. Historical brainstorms and `docs/PARTNER_HANDOFF_ORIGINAL.md` are reference material, not additional active instructions. Follow the reconciled plan for scope and ownership.

## Data integrity

- Distinguish observations, snapshots, inferred geometry and scenario assumptions in both data and UI.
- Never call model scores measured occupancy or real-time traffic. Station points without volumes are not ADT data.
- Do not subtract acreage proxies from parking spaces. Follow the common scoring model with fixed normalization and missing-data semantics.
- `null` means unknown; zero needs documented observation/derivation. Treat midnight/week rollover and America/Chicago time explicitly.
- Keep 311 narrative/contact information out of published extracts. Preserve request dates, category filters, join confidence and coverage limits.
- Waymo local trip feeds and ParkHouston meter transactions are roadmap dependencies, not available observations.
- Do not infer legal curb restrictions from old datasets or bus-stop points alone. Unverified rules remain unknown or labeled scenarios.
- Publish source URLs, retrieval/observation dates, licenses, bounds and counts with every dataset.

## Definition of done

One working map, stable face contract, honest source coverage, reproducible model behavior, meaningful tests for geometry/time/math and integration, and a recorded GitHub source commit. Advanced 3D, LiDAR, flood and calibrated transport simulations follow the MVP rather than blocking it.
