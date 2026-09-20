# Loom script — CurbFusion MVP overview (target: ~4 min, flexible 2-5 min)

Merged from the team's pitch script + the earlier draft. Read the SAY lines like you're talking
to a person — pause at line breaks. ON SCREEN tells you what to click right before/during that
line. `[bracketed]` notes are production notes or optional cuts, not spoken.

**Production note before you hit record:** the Recipe Agent needs a live API key or the local
proxy running to actually call Claude — if that's not wired up yet, click one of the **"start
from"** saved-recipe chips (e.g. "Raccoon family — settle down") instead of typing a live prompt
in section 5. It loads instantly and shows the same weighted, reasoned result without depending
on a network call going out during the recording.

---

## 1. Cold open (0:00–0:15)

**ON SCREEN:** Team on camera or a title card, then cut to the map already loaded.

**SAY:**
> "Trash Pandas. CurbFusion — built in a day. It turns Houston's public data into an answer for
> whatever you're trying to decide."

## 2. The pitch (0:15–0:45)

**SAY:**
> "Houston publishes hundreds of datasets — parcels, 311 calls, garbage pickup days, traffic
> counts, flood zones, bus stops. Each one answers nothing on its own.
>
> We pulled eighteen of them, snapped every one onto the same grid — block face by hour of the
> week — and let an agent weight them for whatever question you ask. We tested it against the
> hardest customer we could think of: a raccoon."

## 3. Live demo — the flip (0:45–1:45)

**ON SCREEN:** Map open, Raccoon mode, Washington Ave, Wed ~22:00. Let it sit a beat.

**SAY:**
> "Raccoon family, Wednesday 10 PM — the Heights lights up. Why? Garbage pickup is Thursday, so
> bins are on the curb tonight — that's the city's Solid Waste polygons. Tree-trim requests from
> 311 mean big trees to den in. Dead-animal pickups, also 311, mark the dangerous blocks, so those
> score down. Quiet streets, from the traffic counts.
>
> None of those datasets mention raccoons. Together, they answer the question."

**ON SCREEN:** Flip the mode dropdown to Curb pressure, same hour.

**SAY:**
> "Same grid, same hour — we changed seven numbers. Now it's a parking planner's map: commercial
> frontage, permit hours, capacity. Washington Ave lights up, the Heights goes quiet."

## 4. Scale — this isn't one street (1:45–2:10)

**ON SCREEN:** Open the corridor dropdown, flip through 2-3 wards quickly (e.g. Third Ward, Fifth
Ward), letting the map redraw each time.

**SAY:**
> "And it's not just Washington Ave. The same grid runs on nine real Houston corridors — all six
> historic wards, plus three commercial strips — built from the same live city data, no synthetic
> numbers anywhere. Adding the next one is one command, not a rewrite."

## 5. Recipe Agent — where it surprises people (2:10–3:00)

**ON SCREEN:** Click "Recipe Agent" in the nav. Click a "start from" chip `[or type a live
prompt only if the key/proxy is confirmed working]`.

**SAY:**
> "This is where the agent comes in. You describe the need in a sentence — it picks the datasets,
> signs them, weights them, and sets when it applies, with a reason for every one it chose. Bus
> stops negative, bike lanes negative, commercial frontage positive, seven to ten AM. Tick, drag,
> save — it's a mode on the map.
>
> Notice the greyed-out rows: parking citations, meter transactions, rideshare pickups from
> Waymo. The agent wanted them. We don't have them. The city does. That's the ask, and that's the
> business."

## 6. Built to be used, not decoded (3:00–3:30)

**ON SCREEN:** Back on the map. Search a real address, let it jump and zoom in. Click a block.
Click "Copy briefing."

**SAY:**
> "Search any Houston address — it jumps straight there. Click a block, you get a plain-English
> read instead of a wall of numbers. And this — copy briefing — turns it into a report you can
> paste into an email or a 311 ticket today, not a dashboard someone else has to translate."

## 7. How it's built (3:30–4:05)

**SAY:**
> "Python hits the city's ArcGIS endpoints directly, no keys. Parcels, 311 cases, pickup
> polygons, traffic counts, FEMA flood zones, bikeways, parks, stop signs. Every dataset becomes a
> number from zero to one, per block face. A recipe is signed weights and a time window — scoring
> is a dot product, computed live in the browser. The agent gets the catalog and your sentence,
> and returns JSON.
>
> The hardest part was the city's own servers throttling deep pages, so we tiered the data
> honestly: live, located, licensed — nothing invented to fill a gap."

## 8. Close (4:05–4:30)

**SAY:**
> "Compiling the data was a day. Asking it a new question is a sentence. Planners, delivery
> drivers, homebuyers, city crews, and yes — raccoons — all on the same grid.
>
> Next: citywide tiles, nightly refresh, and the datasets the city already has to turn this from
> a model into a measurement.
>
> Track: Houston Open Data. Eat trash, fuse data."

---

## Timing cheat sheet

| Section | Target time | Cumulative |
|---|---|---|
| Cold open | 15s | 0:15 |
| The pitch | 30s | 0:45 |
| The flip (demo) | 60s | 1:45 |
| Scale | 25s | 2:10 |
| Recipe Agent | 50s | 3:00 |
| Usability | 30s | 3:30 |
| How it's built | 35s | 4:05 |
| Close | 25s | 4:30 |

Runs ~4:30 read straight. To hit ~3:00, cut section 6 (usability) entirely and trim section 7
(how it's built) to two sentences — both are the most cuttable since sections 2-5 carry the
core insight, the scale proof, and the frontier feature. To stretch past 4:30, let natural
pauses/ad-libs happen while clicking rather than adding more script.
