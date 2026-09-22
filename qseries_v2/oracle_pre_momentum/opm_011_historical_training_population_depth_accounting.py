
from pathlib import Path
from collections import Counter
from qseries_v2.oracle_pre_momentum.opm_006_exact_chf_btc_history_parser import load_btc_history, group_by_anchor
from qseries_v2.oracle_pre_momentum.opm_007_exact_kalshi_btc15m_history_parser import load_kalshi_btc15m
from qseries_v2.oracle_pre_momentum.opm_009_future_kalshi_price_path_labels import build_labeled_examples

def audit_population(root=None):
    root = Path(root or Path.cwd())

    chf = load_btc_history(root)["rows"]
    anchors = group_by_anchor(chf)
    complete_anchors = [
        epoch for epoch, winmap in anchors.items()
        if all(w in winmap for w in (5,15,30,60))
    ]

    kalshi = load_kalshi_btc15m(root)["rows"]
    labeled = build_labeled_examples(root)["rows"]

    chf_times = [x["anchor_time"] for x in chf]
    kalshi_times = [x["event_time"] for x in kalshi]
    label_times = [x["t"] for x in labeled]

    state = {
        "schema_version": "OPM-011",
        "chf_rows": len(chf),
        "chf_complete_multiwindow_anchors": len(complete_anchors),
        "kalshi_rows": len(kalshi),
        "kalshi_contracts": len(set(x["ticker"] for x in kalshi)),
        "labeled_examples": len(labeled),
        "labeled_contracts": len(set(x["ticker"] for x in labeled)),
        "chf_start": min(chf_times).isoformat() if chf_times else None,
        "chf_end": max(chf_times).isoformat() if chf_times else None,
        "kalshi_start": min(kalshi_times).isoformat() if kalshi_times else None,
        "kalshi_end": max(kalshi_times).isoformat() if kalshi_times else None,
        "label_start": min(label_times).isoformat() if label_times else None,
        "label_end": max(label_times).isoformat() if label_times else None,
        "label_contract_counts": dict(Counter(x["ticker"] for x in labeled)),
        "predictive_edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }
    return state
