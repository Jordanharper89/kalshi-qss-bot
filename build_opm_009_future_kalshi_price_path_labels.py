from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_pre_momentum"
MODULE = PKG / "opm_009_future_kalshi_price_path_labels.py"
TEST = ROOT / "test_opm_009_future_kalshi_price_path_labels.py"

module = r"""
from pathlib import Path
from collections import defaultdict
from datetime import timedelta
from qseries_v2.oracle_pre_momentum.opm_008_strict_past_only_cross_stream_alignment import build_alignments

HORIZONS = (5,15,30,60,120,300)
TARGET_MOVE = 0.05

def _first_at_or_after(rows, target_ts):
    for r in rows:
        if r["event_time"].timestamp() >= target_ts:
            return r
    return None

def build_labeled_examples(root=None):
    root = Path(root or Path.cwd())
    a = build_alignments(root)
    alignments, krows = a["rows"], a["kalshi_rows"]
    by_ticker = defaultdict(list)
    for r in krows:
        by_ticker[r["ticker"]].append(r)

    labeled, rejected = [], []
    for x in alignments:
        future = [r for r in by_ticker.get(x["ticker"], []) if r["event_time"] > x["t"]]
        if not future:
            rejected.append((x["anchor_epoch"], "NO_FUTURE_SAME_CONTRACT"))
            continue

        base = x["kalshi_base_price"]
        labels, complete = {}, True
        for h in HORIZONS:
            r = _first_at_or_after(future, x["t"].timestamp() + h)
            if r is None:
                complete = False
                break
            labels[f"d{h}"] = r["price"] - base
            labels[f"p{h}"] = r["price"]
            labels[f"t{h}"] = r["event_time"]
        if not complete:
            rejected.append((x["anchor_epoch"], "INCOMPLETE_300S_PATH"))
            continue

        path300 = [r for r in future if r["event_time"] <= x["t"] + timedelta(seconds=300)]
        if not path300:
            rejected.append((x["anchor_epoch"], "EMPTY_300S_PATH"))
            continue

        moves = [r["price"] - base for r in path300]
        pos_time = neg_time = None
        for r in path300:
            move = r["price"] - base
            lag = (r["event_time"] - x["t"]).total_seconds()
            if pos_time is None and move >= TARGET_MOVE:
                pos_time = lag
            if neg_time is None and move <= -TARGET_MOVE:
                neg_time = lag

        if pos_time is None and neg_time is None:
            first_hit = "NONE"
        elif neg_time is None or (pos_time is not None and pos_time < neg_time):
            first_hit = "PLUS_5C"
        elif pos_time is None or neg_time < pos_time:
            first_hit = "MINUS_5C"
        else:
            first_hit = "TIE"

        labeled.append({
            **x, **labels,
            "mfe_300": max(moves),
            "mae_300": min(moves),
            "plus_5c_time_s": pos_time,
            "minus_5c_time_s": neg_time,
            "first_hit_5c": first_hit,
            "label_end_time": x["t"] + timedelta(seconds=300),
        })
    return {"rows": labeled, "rejected": rejected}
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
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
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPM-009 installer complete")
