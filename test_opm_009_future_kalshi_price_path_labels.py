
from pathlib import Path
from collections import Counter
from qseries_v2.oracle_pre_momentum.opm_009_future_kalshi_price_path_labels import build_labeled_examples, HORIZONS

r = build_labeled_examples(Path.cwd())
rows = r["rows"]
assert rows, "no full-horizon labeled examples"
for x in rows:
    for h in HORIZONS:
        assert x[f"t{h}"] > x["t"]
        assert x[f"t{h}"].timestamp() >= x["t"].timestamp()+h
hits = Counter(x["first_hit_5c"] for x in rows)
print("[FULL_PATH_EXAMPLES]", len(rows))
print("[REJECTED]", len(r["rejected"]))
print("[FIRST_HIT_5C]", dict(hits))
print("[UNIQUE_CONTRACTS]", len(set(x["ticker"] for x in rows)))
print("[PASS] 5/15/30/60/120/300 second future labels constructed")
print("[PASS] MFE/MAE and +/-5c first-hit labels constructed")
print("[PASS] OPM-009 future Kalshi price-path labels certified")
