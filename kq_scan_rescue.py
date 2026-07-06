
"""
KQ-020 Scan Rescue

Run:
 python kq_scan_rescue.py

Purpose:
- Show whether Oracle/KQ is actually producing scan candidates.
- Show whether market data service is making API calls.
- Show top blockers.
"""

import importlib
import traceback


def safe_import(name):
    try:
        return importlib.import_module(name)
    except Exception as exc:
        return exc


def print_block(title):
    print("")
    print("=" * 60)
    print(title)
    print("=" * 60)


def main():
    print_block("KQ-020 SCAN RESCUE")

    # Oracle continuous intelligence
    print_block("ORACLE CONTINUOUS INTELLIGENCE")
    o = safe_import("oracle_continuous_intelligence")
    if isinstance(o, Exception):
        print("[FAIL] Cannot import oracle_continuous_intelligence")
        print(o)
    else:
        try:
            if hasattr(o, "run_cycle"):
                o.run_cycle()
            s = o.status() if hasattr(o, "status") else {}
            ranked = s.get("last_ranked") or []

            print(f"ranked_count: {len(ranked)}")
            print(f"market_regime: {s.get('market_regime')}")
            print(f"final_decision_status: {s.get('final_decision_status')}")
            print(f"execution_queue_status: {s.get('execution_queue_status')}")
            print(f"data_quality_status: {s.get('data_quality_planner_status', {}).get('status')}")

            if ranked:
                top = ranked[0]
                print("")
                print("TOP OPPORTUNITY")
                print(f"ticker: {top.get('ticker')}")
                print(f"title: {top.get('title')}")
                print(f"grade: {top.get('grade')}")
                print(f"execution_decision: {top.get('execution_decision')}")
                print(f"oracle_final_action: {top.get('oracle_final_action')}")
                print(f"tradability: {top.get('tradability')}")
                print(f"order_book_rating: {top.get('order_book_rating')}")
                print(f"fill_probability: {top.get('fill_probability')}")
                print(f"reason_type: {top.get('oracle_no_trade_reason_type')}")
            else:
                print("[WARN] Oracle returned ZERO ranked opportunities.")
        except Exception:
            traceback.print_exc()

    # Common services/modules
    print_block("SERVICE / MARKET DATA CHECKS")
    candidates = [
        "market_data_service",
        "kalshi_market_data",
        "kalshi_client",
        "oracle_market_cache",
        "oracle_research_engine",
        "oracle_cross_market_arbitrage",
        "oracle_market_loader",
    ]

    for name in candidates:
        mod = safe_import(name)
        if isinstance(mod, Exception):
            print(f"[MISS] {name}: {mod}")
            continue

        print(f"[OK] import {name}")

        for attr in ["diagnostics", "status", "get_status"]:
            fn = getattr(mod, attr, None)
            if callable(fn):
                try:
                    print(f"{name}.{attr}(): {fn()}")
                except Exception as exc:
                    print(f"{name}.{attr}() error: {exc}")

        for obj_name in [
            "oracle_market_cache",
            "oracle_research_engine",
            "oracle_cross_market_arbitrage",
            "market_data_service",
        ]:
            obj = getattr(mod, obj_name, None)
            if obj:
                for attr in ["diagnostics", "status", "get_status"]:
                    fn = getattr(obj, attr, None)
                    if callable(fn):
                        try:
                            print(f"{name}.{obj_name}.{attr}(): {fn()}")
                        except Exception as exc:
                            print(f"{name}.{obj_name}.{attr}() error: {exc}")

    print_block("WHAT THIS MEANS")
    print("If market_data shows registered_tickers=0 and api_calls=0, the bot is running but no real scan universe is being registered.")
    print("If Oracle ranked_count > 0 but final_action is NO_TRADE, Oracle is scanning but blocking candidates.")
    print("If Telegram status=400 happens after long cards, the Telegram guard should stop oversized edit failures.")

    print("")
    print("[DONE] KQ-020 scan rescue complete")


if __name__ == "__main__":
    main()
