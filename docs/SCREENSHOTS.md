# Screenshots

Two sets below: what's actually running in this repo today, and a preview of work your partner
has in progress that hasn't landed here yet. Kept separate deliberately — this project's whole
premise is not claiming things that aren't real yet.

## The live app

### Map — Raccoon mode, Sixth Ward, Wednesday 10 PM

![Raccoon mode lighting up the Heights side streets on garbage night](screenshots/map-raccoon-mode.png)

Garbage pickup is Thursday, so bins are out tonight — Solid Waste polygons, 311 tree-trim
requests, dead-animal calls, and quiet-street traffic counts combine into one foraging score.
None of those datasets mention raccoons individually.

### Map — Curb pressure, Third Ward

![Curb pressure mode covering Third Ward, University of Houston visible](screenshots/map-curb-mode-third-ward.png)

Same engine, different corridor, different recipe — proof this isn't hardcoded to one street.
The banner honestly notes Raccoon mode isn't available here yet (no 311/waste data pulled for
this corridor), rather than faking a score.

### Map — Satellite basemap, sunset

![Satellite imagery of Washington Ave with a warm sunset tint applied](screenshots/map-satellite-sunset.png)

The day → evening → night visual treatment works over both basemaps; this is the sunset
transition around 6 PM.

### Recipe Lab

![Recipe Lab with sliders over the component catalog](screenshots/recipe-lab.png)

Drag weights over the same component catalog the map uses, watch the map recolor live.

### Recipe Agent (current)

![Current Recipe Agent page with a flat dataset list](screenshots/recipe-agent-current.png)

Describe a need in a sentence, get back signed weights and a time window with a reason per
dataset. This is the version currently wired into `src/recipe_agent.html`.

## Preview: upcoming Recipe Agent (not yet merged)

Your partner is building a significantly expanded version of the Recipe Agent — categorized
dataset browsing, per-category live/locked counts, a "locked data the agent would use" section,
and save/open-on-map actions. These screenshots are from that in-progress build, not from
anything currently running in this repo; they're included here as a preview so the direction is
documented, not as a claim about current functionality.

### Empty state — categorized catalog

![Upcoming Recipe Agent empty state with Streets & Parking, Transit & Mobility, Environment, and Venues & Activity categories](screenshots/recipe-agent-preview-empty.png)

### Proposed recipe with reasons per component

![Upcoming Recipe Agent showing a proposed Raccoon Settlement Suitability recipe with 11 weighted, reasoned components](screenshots/recipe-agent-preview-proposed.png)

### Catalog detail — locked/licensed data and JSON export

![Upcoming Recipe Agent detail view showing locked datasets like meter transactions and Waymo pickups, plus a JSON export panel](screenshots/recipe-agent-preview-catalog-detail.png)

Once this build is handed off and merged, this section should move up into "The live app" above.
