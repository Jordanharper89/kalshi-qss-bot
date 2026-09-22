
from pathlib import Path
from bisect import bisect_right
from qseries_v2.oracle_pre_momentum.opm_006_exact_chf_btc_history_parser import load_btc_history, group_by_anchor
from qseries_v2.oracle_pre_momentum.opm_007_exact_kalshi_btc15m_history_parser import load_kalshi_btc15m

MAX_BASE_LAG_SECONDS = 5.0
REQUIRED_WINDOWS = (5,15,30,60)

def build_alignments(root=None):
    root = Path(root or Path.cwd())
    anchors = group_by_anchor(load_btc_history(root)["rows"])
    krows = load_kalshi_btc15m(root)["rows"]
    times = [x["event_time"].timestamp() for x in krows]
    out, rejected = [], []

    for epoch, winmap in sorted(anchors.items()):
        if not all(w in winmap for w in REQUIRED_WINDOWS):
            rejected.append((epoch, "INCOMPLETE_CHF_MULTI_WINDOW"))
            continue
        t = winmap[60]["anchor_time"]
        idx = bisect_right(times, t.timestamp()) - 1
        if idx < 0:
            rejected.append((epoch, "NO_PRIOR_KALSHI"))
            continue

        base = krows[idx]
        lag = t.timestamp() - base["event_time"].timestamp()
        if lag < 0:
            raise AssertionError("future Kalshi observation selected as base")
        if lag > MAX_BASE_LAG_SECONDS:
            rejected.append((epoch, "BASE_TOO_STALE", lag))
            continue

        out.append({
            "t": t,
            "anchor_epoch": epoch,
            "ticker": base["ticker"],
            "kalshi_base_time": base["event_time"],
            "kalshi_base_sequence": base["sequence_number"],
            "kalshi_base_price": base["price"],
            "kalshi_base_type": base["observation_type"],
            "kalshi_base_lag_seconds": lag,
            "btc_return_5s": winmap[5]["return"],
            "btc_return_15s": winmap[15]["return"],
            "btc_return_30s": winmap[30]["return"],
            "btc_return_60s": winmap[60]["return"],
            "btc_close": winmap[5]["close_price"],
            "btc_event_count_5s": winmap[5]["event_count"],
            "btc_max_gap_5s": winmap[5]["max_event_gap_seconds"],
        })
    return {"rows": out, "rejected": rejected, "kalshi_rows": krows}
