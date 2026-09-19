# Agent A — context / UI / integration

- Updated: 2026-09-19.
- Role: Agent A, originating Washington Avenue digital-twin conversation.
- Target coordination branch: `main` (initial additive coordination docs only). Publication is blocked: GitHub integration returned HTTP 403, Resource not accessible by integration; no remote writes succeeded.
- Planned implementation branch: `agent/context-ui`; not yet created by this handoff.
- Contract: `1.0.0`, published in `docs/DATA_CONTRACT.md`.
- Current task: reconcile partner handoff and existing digital-twin work; publish shared ownership and interfaces. Feature implementation paused during reconciliation.
- Owned paths: see root `AGENTS.md`; no edits to partner core data/model.

## Completed locally before reconciliation

9,495 OSM road/path ways, 14,229 closed-way building footprints, 67 Washington Avenue ways, 273 authoritative city-hosted METRO stops, 1,711 unique 311 requests, 50 historical HIN segments and 19 camera location/viewer entries. Source manifest and a local preparation script exist. HTML/CSS map shell exists; map behavior and end-to-end application are not yet implemented. No live deployment exists.

These application/data assets are **not yet published in the shared repository** by this planning change. Counts and limitations are in `docs/SHARED_BUILD_PLAN.md`. They must be migrated to `data/context/**` and `scripts/context/**` with their source metadata before another agent can consume them. Do not repull or silently substitute the partner's core data to fill this gap.

## Next tasks

1. Publish existing context assets and a reproducible refresh/preparation entrypoint on `agent/context-ui`.
2. Port useful styling to the single Leaflet frontend at `src/index.html`.
3. Consume B's `data/core/faces.geojson` and exact `faces_version` to create joins.
4. Consume B's `data/corridor.json` for temporal/scenario UI; verify B's reference calculations.

## Dependencies / not ready

- Partner acknowledgment of ownership transfer and contract is pending.
- Partner core assets and canonical faces were absent from inspected main `7912cb6`.
- Face joins cannot be published until stable face IDs exist.
- Existing multiyear OPEN-layer 311 extract is not a complete one-week observation window; scored complaint exposure remains unknown unless another verified extract supplies it.
- Exact normalized output commit: not yet available. This status file is a planning handoff, not a data-readiness signal.

Agent B should publish its own `agents/status/core-model.md`; A has not created or edited it on B's behalf.
