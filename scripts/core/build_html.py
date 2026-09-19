#!/usr/bin/env python3
"""Build all single-file pages.
  src/curbfusion.html    <- src/curbfusion.template.html with every area in data/areas.json inlined (__AREAS__)   [A's page]
  src/recipe_lab.html    <- src/recipe_lab.template.html with data/corridor_lite.json inlined (__DATA__)         [B's page]
  src/recipe_agent.html  <- src/recipe_agent.template.html with the component/licensed catalogs (__CATALOG__)  [B's page]
"""
import pathlib, json
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
esc = lambda s: s.replace("</script", "<\\/script")
LEAFLET_CSS = (ROOT / "src" / "leaflet.min.css").read_text() if (ROOT / "src" / "leaflet.min.css").exists() else ""
def inline_css(html):   # published pages block external stylesheets; inline Leaflet's CSS
    return html.replace('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">', "<style>" + LEAFLET_CSS + "</style>") if LEAFLET_CSS else html
# A: multi-area main app
areas_cfg = json.loads((ROOT / "data" / "areas.json").read_text())
areas = {}
for slug, cfg in areas_cfg.items():
    data = json.loads((ROOT / cfg["path"]).read_text())
    areas[slug] = {"label": cfg["label"], "center": cfg["center"], "zoom": cfg["zoom"], "data": data}
tpl = (ROOT / "src" / "curbfusion.template.html").read_text()
out = inline_css(tpl.replace("__AREAS__", esc(json.dumps(areas, separators=(",", ":")))))
(ROOT / "src" / "curbfusion.html").write_text(out)
print("src/curbfusion.html", round(len(out)/1e6, 2), "MB -", len(areas), "area(s):", ", ".join(areas))
# B: recipe pages (Washington Ave packet)
lite = (ROOT / "data" / "corridor_lite.json").read_text()
lab = inline_css((ROOT / "src" / "recipe_lab.template.html").read_text().replace("__DATA__", esc(lite)))
(ROOT / "src" / "recipe_lab.html").write_text(lab); print("src/recipe_lab.html", round(len(lab)/1e6, 2), "MB")
_l = json.loads(lite); cat = json.dumps({"component_catalog": _l["component_catalog"], "licensed_catalog": _l["licensed_catalog"], "recipes": _l["recipes"]})
ag = (ROOT / "src" / "recipe_agent.template.html").read_text().replace("__CATALOG__", esc(cat))
(ROOT / "src" / "recipe_agent.html").write_text(ag); print("src/recipe_agent.html (catalog only)")
