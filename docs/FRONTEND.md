# Frontend kickoff

**Chosen: Python.** Reference: `src/app.py` (Streamlit + pydeck). `pip install streamlit pydeck && streamlit run src/app.py`.
`src/index.html` is the older Leaflet reference; either may be replaced by A.

Input: `data/corridor.json` only (spec: `docs/DATA_CONTRACT.md` 1.0.0 + `docs/MODEL.md`). Serve the repo root with
`python -m http.server` and open `/src/`. A working skeleton exists at `src/index.html`.

## What to build

1. Map with block faces as thick lines, colored by `pressure_index[h]` / `forage_index[h]` per `modes`; null index → grey.
2. Hour-of-week scrubber (0..167) with play/pause; label from `meta.hour0`.
3. Preset buttons from `presets[]`.
4. Layer toggles: demand, regulation, complaints, supply; markers from `points.metro_stops`, `points.adt_stations`.
5. Click a face → side panel: `label`, `supply`, `fixed`, `landuse`, `adt`, and a 168-bar sparkline of `stress`.
6. Header stat from `summary.over_capacity[h]` / `summary.supply`.
7. What-if controls that mutate `reg` / `fixed` in memory and recompute stress client-side
   (formula in CONTRACT.md). No server.
8. Legend fixed to `ranges.stress`.

Nice-to-have: aerial basemap toggle, animation easing, per-class demand chart from `classes[].curve`.

## Paths

### A. Extend the skeleton (vanilla HTML + Leaflet)
- Already renders. Add a chart lib from cdnjs (Chart.js or uPlot) for the sparkline.
- Fastest to demo; one file; no build step. Recommended if time is short.

### B. Vite + MapLibre GL (+ deck.gl optional)
- GPU line rendering, smooth animation, vector basemaps, 3D extrusion of stress if wanted.
- `npm create vite@latest`, `maplibre-gl`, load faces as a GeoJSON source with `line-color` driven
  by a data expression on the current hour. deck.gl `PathLayer` if you want 1000+ faces animated.
- Best visuals; ~1–2 hours to reach parity with the skeleton.

### C. Python (Streamlit or Dash + pydeck/folium)
- If the team is Python-first. `st.slider` for hour, `pydeck.Layer("PathLayer")` for faces.
- Quick to stand up, weaker animation; fine for judges if the story is clear.

### D. Zero-code fallback
- kepler.gl: load faces as GeoJSON with a `stress_h` column per hour and use its time filter.
- Observable notebook with Plot + Leaflet.

## Colors and states (suggested, not required)

| State | Suggest |
|---|---|
| stress 0 → 1 | blue → yellow |
| stress 1 → max | yellow → red |
| `reg==2` permit-only | dashed stroke |
| `reg==3` no parking | grey, thin |
| bus stop / ADT station | small circle marker, tooltip |

Line weight 5–7 px at z16; scale with zoom. Fit bounds to `meta.bbox` on load.

## Contract changes

If a field is missing, ask backend; do not derive it in the frontend from raw GeoJSON.
Additive keys only; existing keys keep their meaning.
