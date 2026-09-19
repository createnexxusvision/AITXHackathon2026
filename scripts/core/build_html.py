#!/usr/bin/env python3
"""Inline data/corridor_lite.json into src/curbfusion.template.html -> src/curbfusion.html (single file, no server needed)."""
import pathlib, json
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
lite = (ROOT / "data" / "corridor_lite.json").read_text()
tpl = (ROOT / "src" / "curbfusion.template.html").read_text()
out = tpl.replace("__DATA__", lite.replace("</script", "<\\/script"))
(ROOT / "src" / "curbfusion.html").write_text(out)
print("src/curbfusion.html", round(len(out)/1e6, 2), "MB")
