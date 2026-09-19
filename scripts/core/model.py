"""Pure scoring helpers shared by backend and any Python frontend. No I/O."""
def expand(face, rid, doc):
    """168-int score vector for recipe `rid` on `face`, or None."""
    sc = face["scores"].get(rid)
    if not sc: return None
    T = doc["curve_table"]
    return [round(100 * sc["base"] * max(T[c][h] for c in sc["curves"])) for h in range(168)]

def index_at(face, mode, h, doc):
    """Value at hour h for any mode key in doc['modes'] (pressure_index, forage_index, or scores.<rid>)."""
    key = doc["modes"][mode]["index"]
    if key.startswith("scores."):
        v = expand(face, key[7:], doc); return v[h] if v else None
    v = face.get(key); return v[h] if v else None
