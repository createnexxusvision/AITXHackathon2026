# Demo — CurbFusion / Team Trash Pandas

Track: **Houston Open Data**. Say it in the first sentence. Four minutes, two voices. Submissions 19:00; awards 20:30.

## Checklist (by 18:30)
- [ ] Laptop that will present has `src/curbfusion.html`, `src/recipe_lab.html`, `src/recipe_agent.html` open in tabs, tiles loaded (needs internet).
- [ ] Recipe Agent endpoint chosen: proxy running (`tools/recipe_proxy.py`) or browser key set, or fallback = claude.ai preview tab.
- [ ] Screen recording of the full run (judging criteria list it as backup).
- [ ] README filled: track, problem, solution, customer, team, sources, caveats.
- [ ] One rehearsal on the real screen.

## Script
1. **Hook (30s).** Raccoon family, Wed 22:00, Heights lit. "Best night to be a raccoon in the Heights. The city publishes garbage-day polygons,
   missed pickups, dead-animal calls, tree-trim requests, traffic counts. None mention raccoons. Together they answer the question."
2. **Engine (60s).** Flip to curb pressure, same hour: Washington Ave lights, Heights goes quiet. "Same 3,000 block faces, same 168-hour week,
   same 18 datasets. We changed seven numbers." Click a face: components, sparkline, sources. Corridor switcher: Montrose, Midtown, Heights.
3. **Agent (60s).** Recipe Agent: "delivery driver with a box truck, mornings, hates tickets." Show ticked datasets, signed weights, reasons,
   the time window it chose, and the greyed locked row. "It reached for meter transactions. We don't have them. ParkHouston does. That's the ask."
4. **Point (45s).** Recipe Lab: drag flood to −1, watch the map. "Every planner, driver, resident and raccoon has a recipe. We built the catalog
   and the grid so they write their own." Closing screen: raccoon at a laptop, EAT TRASH · FUSE DATA.
5. **Honesty (15s).** "Scores are proxies and assumptions; every constant is in `assumptions.json`. One dataset turns this from model into
   measurement, and the city already has it."

## If asked
- "Is this real data?" Every layer is a public city/county/federal endpoint, listed in `data/core/manifest.json`; nothing synthetic.
- "How accurate?" Uncalibrated. `confidence` per face. The recipe layer is the product; calibration needs meter data.
- "Surveillance?" No plate readers, by choice. It's on the catalog page as excluded.
- "Business?" Catalog and recipes free; broker licensed data (meters, foot traffic, imagery) through the same picker.
