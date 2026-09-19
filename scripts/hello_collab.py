#!/usr/bin/env python3
"""Collaboration smoke test for AITXHackathon2026.

Run from repo root:  python scripts/hello_collab.py
Confirms the repo is cloneable, Python runs, and data/ is readable.
Each collaborator (human or agent) appends a line to data/handshake.txt and commits.
"""
import json, pathlib, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
boundary = ROOT / "data" / "pbd_boundary.geojson"
handshake = ROOT / "data" / "handshake.txt"

if boundary.exists():
    g = json.loads(boundary.read_text())
    print("PBD boundary loaded:", g["properties"]["name"], "| geometry:", g["geometry"]["type"])
else:
    print("data/pbd_boundary.geojson not found (fine on first run)")

who = sys.argv[1] if len(sys.argv) > 1 else "anonymous"
stamp = datetime.datetime.now().isoformat(timespec="seconds")
handshake.parent.mkdir(exist_ok=True)
with handshake.open("a") as f:
    f.write(f"{stamp}  {who}  hello\n")
print("handshake lines:")
print(handshake.read_text())
