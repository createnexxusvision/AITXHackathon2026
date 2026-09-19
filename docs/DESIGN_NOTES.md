# Design notes for the skin (B → A, proposals only)

1. **Recipe-first flow.** Landing = recipe picker: cards (icon, name, blurb, audience) + "describe your need" (agent). Pick/create → map
   with recipe applied, hour slider, corridor switcher. "Recipes" button returns. Lab and Agent become the picker's two tabs (browse / describe).
   Choosing a view is choosing a recipe; curb pressure and raccoon forage are the two built-in cards.
2. **One look.** Same panel style, color ramp and type across map, Lab and Agent. Skin the two B templates rather than restyling separately.
3. **Satellite at 20–30% opacity** under the dark base, or hover-to-reveal. Imagery is texture; the lines are the information.
4. **No cliff at the corridor edge.** Draw `data/context/citywide_lite.json` (every centerline in the 610 loop, parcels-only pressure base)
   thin and dim everywhere; corridors sit on top bright. Outside reads as "less detail," not "off limits."
5. **Event icons** (💀 🗑️ 🚯) cluster or thin below z15.
