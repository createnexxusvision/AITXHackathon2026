# Agent B — core model

- Updated: 2026-09-19 15:45 CDT.
- Role: Agent B, core geography + model + recipe system. Acknowledges `docs/SHARED_BUILD_PLAN.md` and `docs/DATA_CONTRACT.md` 1.0.0.
- Transport: B has no GitHub write path; drops arrive as `curbfusion_handoff_YYYYMMDD_HHMM.zip` (UTC) via the human teammate. Unzip at repo root, replace B-owned paths wholesale. A records the landing commit.

## Lanes (effective now)

| A owns | B owns |
|---|---|
| `src/curbfusion.template.html` — skin, theme, icons, day/night, basemaps, layout | `data/**`, `scripts/**`, `docs/MODEL.md`, `docs/SCORING.md`, `docs/HANDOFF.md`, this file |
| `data/context/**`, `data/joins/**` | `src/recipe_lab.template.html` — Recipe Lab page |
| README, AGENTS.md, DATA_CONTRACT.md, release | `data/core/recipes.json` (A may PR new recipes) |

B will not edit `src/curbfusion.template.html` again. Anything B needs there goes in this file as a request.
A should not hand-edit `corridor.json`, `corridor_lite.json`, or `src/*.html` build outputs; edit templates and rerun `python scripts/core/build_html.py`.

## In this drop
- `src/recipe_lab.template.html` + built `recipe_lab.html`: compose a recipe from the component catalog (signed sliders −1..+1, curve picks), live preview, export `recipes.json`.
- Packet additions (`corridor_lite.json`): `component_catalog`, `curve_catalog`, `points.events` (💀 dead-animal 386, 🗑️ missed collection 3,111, 🚯 dumping 61).
- `curbfusion.template.html` last B edits (already delivered, A owns from here): sky tint + clock, basemap switch (dark / satellite / none), event icon layer, details docked in left panel.

## Coming from B (plan around it, nothing changes shape)
- Possible new components appended to `comp` and `component_catalog`: flood zone (FEMA/HCFCD), TABC alcohol licenses (real nightlife layer), bike lanes, bayou proximity. Additive keys only; existing keys keep meaning.
- Possible new recipes in `recipes.json`. Additive.
- No further changes to `faces.geojson` / `faces_version` today.

## Requests to A
- Link Recipe Lab from the main app (button or nav). Optional: embed it as a panel.
- `scrollWheelZoom` decision is A's; human preference leaned toward page scroll.
- Event icons: consider clustering or hiding below zoom 15.

## Merge note (this drop)
Base = A's tree at `e0fab3e` (four corridors, skinned UI). Overlaid B lane only: `scripts/core/build_core.py`, `model.py`,
`pull_corridor_data.py`, `data/core/recipes.json`, raw layers (`flood_nfhl`, `bikeways`, `parks`, `stop_signs`,
`traffic_signals`, wide `parcels`), `src/recipe_lab.*`, `src/recipe_agent.*`, `src/app.py`, docs. `build_html.py` is
merged: A's `__AREAS__` fold for `curbfusion.html` plus B's two recipe pages. `src/curbfusion.template.html`,
`build_new_corridor.py`, `data/areas/**`, `data/areas.json`, `index.html` untouched.
New packet keys (additive): `comp.{vacant,stop_ctl,flood,bike_lane,park,dark311}`, `licensed_catalog`, `component_catalog`,
`points.events`, `scores`, `curve_table` incl. `win:*`. Recipes may carry `window`.

## Lanes from here (B → A)

- **A owns** `src/curbfusion.template.html` and everything visual: theme, day/night treatment, icons, satellite, clustering. B will not edit it again.
- **B owns** `src/recipe_lab.template.html`, `data/core/recipes.json`, `scripts/core/**`, `data/**`. Recipe Lab is a separate page; A may link it from the main app or fold the panel in later; do not merge by hand yet.
- Shared: `corridor_lite.json` is the UI packet. Additive keys only. If A needs a field, ask; B adds it in `build_core.py` and reships.
- Rebuild after any data change: `python scripts/core/build_core.py && python scripts/core/build_html.py`. Both pages inline the packet.

## Incoming from B (so A can plan, not react)

1. `recipes.json` may gain a few recipes; no schema change.
2. Possible new components (candidates: TABC alcohol licenses, FEMA/HCFCD flood zones, tree canopy, bike lanes, BARC animal 311). Each lands as one more key in `comp` and one entry in `component_catalog`; A's sliders and hover render them automatically if they iterate the catalog.
3. No further changes to `pressure_index` / `forage_index` semantics today.

## Blockers
- Loading/valet 2015 XLS: portal 403. Overpass OSM POIs: timeouts. Neither blocks the demo.
- Complaints coverage `partial_snapshot`; scored complaint component stays null per contract.
