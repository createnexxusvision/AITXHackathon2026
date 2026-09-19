# AITX Hackathon 2026

Project repo for the [Houston AITX Community Hackathon](https://common-scooter-829.notion.site/Houston-AITX-Community-Hackathon-3d81e636288e80d7bf5fc5950e9ac998) (Sep 19, 2026, POST Houston).

Full event details, tracks, and judging criteria are captured in [docs/hackathon-info.md](docs/hackathon-info.md).

## Shared build coordination

Start with [the shared build plan](docs/SHARED_BUILD_PLAN.md), [the data contract](docs/DATA_CONTRACT.md), and [agent ownership rules](AGENTS.md). The MVP is Curb Fusion: a block-face × hour-of-week curb model for Washington Avenue, with one Leaflet interface. Agent A owns context data and UI; Agent B owns core geography and modeling. The plan records current readiness and the larger digital-twin roadmap.

## Track

- [ ] Agents Track
- [x] Houston Open Data Track
- [ ] Most Commercializable Track

## Project

**Name:** CurbFusion — Team Trash Pandas

**One-liner:** Overlays Houston public datasets on a common unit — block face × hour of week — to surface curb-parking demand *and* raccoon-foraging patterns no single dataset records.

**Problem:** Curb-parking conflicts on corridors like Washington Ave (residents vs. commercial visitors vs. permit parking) aren't visible in any single city dataset — you have to cross-reference parcels, permits, road data, and complaints by hand. Meanwhile the same 311 trash/complaint data that describes curb pressure also describes where a raccoon would have a great night.

**Solution:** Pulls Houston's open parcel, road centerline, residential permit parking, traffic count, and solid-waste/311 data, builds a per-block-face model across all 168 hours of the week, and renders it as an interactive map (`src/curbfusion.html`) with a time-of-week scrubber, a Curb ⇄ Raccoon ⇄ Combined-risk mode switch, and a Streets/Satellite basemap toggle that visually shifts from day to evening to night as you scrub through the week. The map now covers **four real Houston corridors** you can switch between (Washington Ave, Westheimer/Montrose, 19th St/Heights, Main St/Midtown), plus an address search box that jumps anywhere in Houston and honestly says whether that block is modeled yet.

**Who's the user / customer:** City planners, PBD/civic districts, and residents/businesses trying to understand or negotiate curb-parking regulation changes — built so a non-technical city official can search their block, drag a slider, and get a plain-English read instead of raw scores.

See [docs/HANDOFF.md](docs/HANDOFF.md) for the full data contract, build order, and current status, and [docs/FRONTEND.md](docs/FRONTEND.md) for what's left to build on the map UI.

### Corridors & scaling beyond one street

Washington Ave has the deep dataset (311, solid-waste schedules, ADT, Raccoon mode — pulled by a teammate's own process). The other three corridors (`scripts/core/build_new_corridor.py`) are built from a generalized, bbox-parameterized version of the same real pipeline (HCAD parcels, road centerlines, residential permit parking — all live Houston/ArcGIS endpoints, no auth) and prove the model isn't hardcoded to one street. They deliberately don't fake Raccoon mode or a permit-district scenario they have no data for — the UI shows a "not pulled yet for this corridor" note instead of inventing numbers. Adding another corridor anywhere in Houston is one command:

```bash
python scripts/core/build_new_corridor.py <slug> "<Label>" <minlon> <minlat> <maxlon> <maxlat>
# then add an entry to data/areas.json pointing at data/areas/<slug>/corridor_lite.json
python scripts/core/build_html.py
```

## Getting Started

```bash
# clone
git clone https://github.com/createnexxusvision/AITXHackathon2026.git
cd AITXHackathon2026

# backend deps (re-pulling data / rebuilding the model)
pip install pyshp shapely pyproj

# re-pull source data from Houston open data endpoints (data/*.geojson already committed)
python scripts/pull_corridor_data.py

# rebuild data/core/*.json + data/corridor.json + data/corridor_lite.json
python scripts/core/build_core.py

# inline the data into a single self-contained demo file (no server needed to view it)
python scripts/core/build_html.py
# double-click src/curbfusion.html, or:
python -m http.server
# open http://localhost:8000/src/curbfusion.html
```

`src/app.py` is a Streamlit/pydeck alternative viewer: `pip install streamlit pydeck && streamlit run src/app.py`.

## Repo Structure

```
.
├── agents/     # agent status/coordination files (see AGENTS.md)
├── data/       # Washington Ave data + corridor.json/corridor_lite.json; areas.json lists all corridors
│   └── areas/  # per-corridor data + corridor_lite.json for the non-Washington-Ave corridors
├── docs/       # hackathon info, build plan, data contract, model + scoring notes, handoff notes
├── scripts/    # data pull + model build scripts (scripts/core/ is the current pipeline;
│               #   build_new_corridor.py adds any new corridor from a bounding box)
├── src/        # curbfusion.html (main demo), app.py (Streamlit alt), index.html (older reference)
├── tests/      # automated tests
├── AGENTS.md   # agent/collaborator ownership rules
└── README.md
```

## Demo

- [ ] Live demo runs end to end without crashing
- [ ] Recording as backup (judges prefer live)

## Submission Checklist

- [ ] Project submitted before 7:00 PM deadline
- [ ] Track selected and clearly stated
- [ ] README explains problem, solution, and customer/user
- [ ] Demo works live
- [ ] Team members listed below

## Team

- TBD
