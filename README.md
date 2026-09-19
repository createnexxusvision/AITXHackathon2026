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

**Name:** Curb Fusion

**One-liner:** Overlays Houston public datasets on a common unit — block face × hour of week — to surface curb-parking demand patterns no single dataset records.

**Problem:** Curb-parking conflicts on corridors like Washington Ave (residents vs. commercial visitors vs. permit parking) aren't visible in any single city dataset — you have to cross-reference parcels, permits, road data, and complaints by hand.

**Solution:** Pulls Houston's open parcel, road centerline, residential permit parking, and traffic count data for the Washington Ave Parking Benefit District, builds a per-block-face demand/supply/regulation model across all 168 hours of the week (`data/corridor.json`), and renders it as an interactive Leaflet map (`src/index.html`) with a time-of-week scrubber and what-if controls.

**Who's the user / customer:** City planners, the Washington Ave PBD, and residents/businesses trying to understand or negotiate curb-parking regulation changes.

See [docs/HANDOFF.md](docs/HANDOFF.md) for the full data contract, build order, and current status, and [docs/FRONTEND.md](docs/FRONTEND.md) for what's left to build on the map UI.

## Getting Started

```bash
# clone
git clone https://github.com/createnexxusvision/AITXHackathon2026.git
cd AITXHackathon2026

# backend deps (re-pulling data / rebuilding the model)
pip install pyshp shapely pyproj

# re-pull source data from Houston open data endpoints (data/*.geojson already committed)
python scripts/pull_corridor_data.py

# rebuild data/corridor.json from the pulled GeoJSON
python scripts/build_corridor.py

# serve the map
python -m http.server
# open http://localhost:8000/src/
```

## Repo Structure

```
.
├── agents/     # agent status/coordination files (see AGENTS.md)
├── data/       # Houston open data extracts + built corridor.json model
├── docs/       # hackathon info, build plan, data contract, handoff notes
├── scripts/    # data pull + model build scripts
├── src/        # Leaflet map frontend (index.html)
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
