#!/usr/bin/env python3
"""Inline every area listed in data/areas.json into src/curbfusion.template.html
-> src/curbfusion.html (single file, no server needed).

Each area's own corridor_lite.json (produced by build_core.py / build_area.py) is embedded
under its slug, so the frontend can switch between corridors without a network request.
"""
import pathlib, json
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
areas_cfg = json.loads((ROOT / "data" / "areas.json").read_text())
areas = {}
for slug, cfg in areas_cfg.items():
    data = json.loads((ROOT / cfg["path"]).read_text())
    areas[slug] = {"label": cfg["label"], "center": cfg["center"], "zoom": cfg["zoom"], "data": data}
payload = json.dumps(areas, separators=(",", ":"))
tpl = (ROOT / "src" / "curbfusion.template.html").read_text()
out = tpl.replace("__AREAS__", payload.replace("</script", "<\\/script"))
(ROOT / "src" / "curbfusion.html").write_text(out)
print("src/curbfusion.html", round(len(out)/1e6, 2), "MB", "-", len(areas), "area(s):", ", ".join(areas))
