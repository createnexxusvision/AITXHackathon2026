# Agent B — core model

- Updated: 2026-09-19 (afternoon, CDT).
- Role: Agent B, core geography + model. Acknowledges `docs/SHARED_BUILD_PLAN.md` and `docs/DATA_CONTRACT.md` 1.0.0.
- Transport: B has no GitHub write path today; outputs arrive as a zip via the human teammate. Commit SHA recorded by A on landing.
- Contract: 1.0.0, plus additive fields `forage_index`, `forage_components`, `modes`, `raccoon_curve`, `in_analysis_area`, `points.*`.

## Published in this drop
- `data/core/faces.geojson` (2,974 faces, 364 in PBD), `data/core/manifest.json` (`faces_version` inside), `data/core/assumptions.json`.
- `data/corridor.json` 7.5 MB / 0.43 MB gzipped. 2,974 faces; 1,975 matched 311 (151 parking, 977 trash, rest other); ADT on faces near 122 stations; 204 METRO stops as context.
- Raw pulls: `data/parcels.geojson` (19,053), `centerline.geojson` (2,668), `rpp.geojson` (79), `adt_*.geojson`, `adt_volumes.json`, `sr311_raw.json` (1,996), `metro_stops.json`.
- `scripts/pull_corridor_data.py` (env `CURB_BBOX` overrides extent), `scripts/core/build_core.py`, `docs/MODEL.md`.

## Deviations from plan, for A to accept or reject
- Extent widened to A's rectangle; scoring not restricted to PBD (all faces scored, `in_analysis_area` flagged). Human request: zoom out.
- ADT volumes retrieved from `TrafficCount_Assignments` (table 22); no longer null.
- B pulled 311 itself from the public 311 map services because A's normalized `data/context/requests.geojson` and `data/joins/complaints_by_face.json` were not yet in the repo. Coverage labelled `partial_snapshot`; scored complaint component is null as the contract requires. If A's joins land, B will consume them instead.
- Raccoon Mode added as a second index on the same faces (see MODEL.md). Product framing from the human team: team **Trash Pandas**, project **CurbFusion**.

## Blockers
- No METRO stop exclusion applied (A10). Loading/valet 2015 XLS blocked by portal 403.
- `demand_proxy` and `pressure_index` remain hypothetical; PBD rule unverified (A08).
