
"""
ORACLE-071 Learning Summary Terminal

Purpose:
- Simple terminal command for Oracle learning status.
- Shows outcome scores, learning patterns, tracked trades, and learning-adjusted rankings.
- Does NOT place trades.

Commands:
 python oracle_learning_terminal.py
 python oracle_learning_terminal.py 10
 python oracle_learning_terminal.py full
"""

import sys
import json


def run(limit=5, full=False):
    import oracle_continuous_intelligence as o

    o.run_cycle()
    s = o.status()

    print("")
    print("============================================================")
    print(" ORACLE LEARNING TERMINAL")
    print("============================================================")
    print(f"Market Regime: {s.get('market_regime')}")
    print(f"Live Trades: {s.get('live_trade_tracker_status', {}).get('open_count')}")
    print(f"Outcome Counts: {s.get('outcome_scoring_status', {}).get('outcome_counts')}")
    print(f"Learning Patterns: {s.get('signal_learning_status', {}).get('patterns')}")
    print(f"Learning Adapter Matches: {s.get('learning_adapter_status', {}).get('matched_patterns')}")
    print(f"Learning Final Actions: {s.get('learning_final_router_status', {}).get('action_counts')}")
    print("============================================================")

    patterns = s.get("signal_learning_top_patterns") or []
    print("")
    print("TOP LEARNING PATTERNS")
    print("------------------------------------------------------------")
    if not patterns:
        print("No learning patterns yet.")
    else:
        for i, p in enumerate(patterns[:limit], 1):
            print("")
            print(f"#{i}")
            print(f"Pattern: {p.get('pattern_key')}")
            print(f"Samples: {p.get('samples')}")
            print(f"Win Rate: {p.get('win_rate')}%")
            print(f"Avg Outcome: {p.get('avg_outcome_score')}")
            print(f"Avg Paper P&L: {p.get('avg_paper_pnl')}")

    ranked = s.get("last_ranked") or []
    print("")
    print("TOP LEARNING-ADJUSTED OPPORTUNITIES")
    print("------------------------------------------------------------")
    if not ranked:
        print("No ranked opportunities.")
    else:
        for i, item in enumerate(ranked[:limit], 1):
            print("")
            print(f"#{i}")
            print(f"Ticker: {item.get('ticker')}")
            print(f"Market: {item.get('title')}")
            print(f"Final Action: {item.get('oracle_final_action')}")
            print(f"Final Score: {item.get('oracle_final_score')}")
            print(f"Learning Adjusted: {item.get('learning_adjusted_score')}")
            print(f"Learning Confidence: {item.get('learning_confidence')}")
            print(f"Boost/Penalty: {item.get('learning_boost')} / {item.get('learning_penalty')}")

            if full:
                print("")
                print(item.get("learning_card"))

    outcomes = s.get("outcome_scores") or []
    print("")
    print("RECENT OUTCOME SCORES")
    print("------------------------------------------------------------")
    if not outcomes:
        print("No outcome scores yet.")
    else:
        for i, out in enumerate(outcomes[:limit], 1):
            print("")
            print(f"#{i}")
            print(out.get("compact_card"))

    print("")
    print("============================================================")
    print(" END ORACLE LEARNING TERMINAL")
    print("============================================================")


def main():
    args = sys.argv[1:]
    limit = 5
    full = False

    for a in args:
        if str(a).lower() == "full":
            full = True
        else:
            try:
                limit = int(a)
            except Exception:
                pass

    run(limit=limit, full=full)


if __name__ == "__main__":
    main()
