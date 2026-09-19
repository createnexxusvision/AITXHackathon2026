#!/usr/bin/env python3
"""CurbFusion — Streamlit reference viewer (Agent B, replaceable by A).

    pip install streamlit pydeck
    streamlit run src/app.py

Reads data/corridor.json only. Mode toggle Curb / Raccoon, hour-of-week slider, presets, hover.
"""
import json, pathlib
import streamlit as st
import pydeck as pdk
import sys; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts" / "core"))
import model

ROOT = pathlib.Path(__file__).resolve().parent.parent
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

@st.cache_data
def load():
    return json.load(open(ROOT / "data" / "corridor.json"))

def ramp(v):
    """0..100 -> [r,g,b]; blue -> yellow -> red."""
    if v is None: return [85, 85, 85]
    t = max(0, min(1, v / 100))
    if t < .5:
        k = t * 2; return [int(43 + (255-43)*k), int(131 + (255-131)*k), int(186 + (191-186)*k)]
    k = (t - .5) * 2; return [int(255 - (255-215)*k), int(255 - (255-25)*k), int(191 - (191-28)*k)]

d = load()
st.set_page_config(page_title="CurbFusion — Trash Pandas", layout="wide")
st.title("CurbFusion")

with st.sidebar:
    modes = list(d["modes"].keys())
    mode = st.radio("Mode", modes, format_func=lambda m: d["modes"][m]["label"])
    if d["modes"][mode].get("blurb"): st.caption(d["modes"][mode]["blurb"])
    if "h" not in st.session_state: st.session_state.h = 118
    for p in d["presets"]:
        if st.button(p["label"]):
            st.session_state.h = p["h"]; mode = p["mode"]
    h = st.slider("Hour of week", 0, 167, key="h", format="%d")
    st.caption(f"{DAYS[h // 24]} {h % 24:02d}:00 · {d['modes'][mode]['label']}")
    show_311 = st.checkbox("311 points (mode-filtered)", value=False)
    show_pbd = st.checkbox("PBD outline", value=True)

key = d["modes"][mode]["index"]
paths = []
for f in d["faces"]:
    v = model.expand(f, key[7:], d) if key.startswith("scores.") else f[key]
    val = v[h] if v else None
    paths.append({
        "path": f["geometry"]["coordinates"], "color": ramp(val), "width": 4 if v else 1.5,
        "label": f["display_label"], "value": val if val is not None else "—", "conf": f["confidence"],
        "detail": (f"capacity {f['gross_capacity_spaces']} · demand {f['demand_proxy'][h] if f['demand_proxy'] else '—'} · "
                   f"{'restricted' if f['regulation_mask'] and f['regulation_mask'][h] else 'open'}"
                   + (f" · ADT {f['adt']['volume']}" if f["adt"] else ""))
                  if mode == "curb" else
                  f"garbage {f['schedule']['garbage']} · recycling {f['schedule']['recycling']} · heavy {f['schedule']['heavy']} · "
                  f"trash311 {f['forage_components']['trash_311_total']} · missed {f['extras']['missed_collections']} · trees {f['extras']['tree_311']}",
    })

layers = [pdk.Layer("PathLayer", paths, get_path="path", get_color="color", get_width="width",
                    width_units="pixels", pickable=True, auto_highlight=True)]
if show_311:
    kind = "parking" if mode == "curb" else "trash"
    pts = [{**p, "tip": f"{p['type']} · {DAYS[p['h']//24]} {p['h']%24}:00 · {p['date']}"} for p in d["points"]["sr311"] if p["kind"] == kind]
    layers.append(pdk.Layer("ScatterplotLayer", pts, get_position="[lon, lat]", get_radius=12, get_fill_color=[255, 255, 255, 180], pickable=True))
if show_pbd:
    pbd = json.load(open(ROOT / "data" / "pbd_boundary.geojson"))
    layers.append(pdk.Layer("GeoJsonLayer", pbd, stroked=True, filled=False, get_line_color=[255, 255, 255, 160], line_width_min_pixels=1))

st.pydeck_chart(pdk.Deck(
    layers=layers,
    initial_view_state=pdk.ViewState(latitude=29.772, longitude=-95.40, zoom=13.2, pitch=0),
    map_style="dark",
    tooltip={"html": "<b>{label}</b><br/>{value} · confidence {conf}<br/>{detail}{tip}", "style": {"fontSize": "12px"}},
), use_container_width=True, height=720)

c1, c2, c3 = st.columns(3)
scored = [p["value"] for p in paths if p["value"] != "—"]
c1.metric("Faces scored", len(scored))
c2.metric("Faces ≥ 80", sum(1 for v in scored if v >= 80))
c3.metric("311 matched", len(d["points"]["sr311"]))
st.caption("Indices are uncalibrated / hypothetical. See docs/MODEL.md and data/core/assumptions.json.")
