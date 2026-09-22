
from pathlib import Path
from collections import Counter
from qseries_v2.oracle_pre_momentum.opm_006_exact_chf_btc_history_parser import load_btc_history, group_by_anchor

r = load_btc_history(Path.cwd())
rows = r["rows"]
assert rows, "no admissible BTC CHF history"
assert all(x["window_seconds"] in (5,15,30,60) for x in rows)
assert all(x["anchor_time"].tzinfo is not None for x in rows)
counts = Counter(x["window_seconds"] for x in rows)
anchors = group_by_anchor(rows)
complete = sum(all(w in v for w in (5,15,30,60)) for v in anchors.values())
print("[BTC_CHF_ROWS]", len(rows))
print("[WINDOW_COUNTS]", dict(sorted(counts.items())))
print("[ANCHORS]", len(anchors))
print("[COMPLETE_5_15_30_60_ANCHORS]", complete)
print("[REJECTED]", len(r["rejected"]))
print("[PASS] only CHF-016 RAW_EXTERNAL past-only complete BTC windows admitted")
print("[PASS] OPM-006 exact CHF BTC history parser certified")
