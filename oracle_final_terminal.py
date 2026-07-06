
"""
ORACLE-062 Final Decision Terminal

Purpose:
- Simple terminal command for top Oracle final decisions.
- Does NOT place trades.

Commands:
 python oracle_final_terminal.py
 python oracle_final_terminal.py 5
 python oracle_final_terminal.py full
"""

import sys
import json


def run(limit=5, full=False):
    import oracle_continuous_intelligence as o

    o.run_cycle()
    s = o.status()
    ranked = s.get("last_ranked") or []

    print("")
    print("============================================================")
    print(" ORACLE FINAL DECISION TERMINAL")
    print("============================================================")
    print(f"Market Regime: {s.get('market_regime')}")
    print(f"Final Decision Status: {s.get('final_decision_status', {}).get('action_counts')}")
    print(f"Trade Readiness: {s.get('trade_readiness_status', {}).get('verdict_counts')}")
    print(f"EV Status: {s.get('expected_value_status', {}).get('ev_counts')}")
    print(f"Queue Counts: {s.get('execution_queue_status', {}).get('counts')}")
    print("============================================================")

    if not ranked:
        print("No ranked opportunities available.")
        return

    for i, item in enumerate(ranked[:limit], 1):
        print("")
        print(f"#{i}")
        print("------------------------------------------------------------")

        card = item.get("oracle_final_card")
        if card:
            print(card)
        else:
            print(f"Ticker: {item.get('ticker')}")
            print(f"Market: {item.get('title')}")
            print(f"Final Action: {item.get('oracle_final_action')}")
            print(f"Final Score: {item.get('oracle_final_score')}")

        if full:
            print("")
            print("---- Trade Readiness ----")
            print(item.get("trade_readiness_card"))
            print("")
            print("---- Expected Value ----")
            print(item.get("ev_card"))
            print("")
            print("---- Queue ----")
            print(item.get("execution_queue", item.get("queue_decision")))

    print("")
    print("============================================================")
    print(" END ORACLE FINAL DECISION TERMINAL")
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
