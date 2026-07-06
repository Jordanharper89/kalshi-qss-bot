
"""
ORACLE-072 System Health Terminal

Purpose:
- Check Oracle module health in one command.
- Imports key modules and calls diagnostics when available.
- Does NOT place trades.
"""

from datetime import datetime, UTC
import importlib
import json

MODULES = [
    ("oracle_consensus_engine", "oracle_consensus_engine"),
    ("oracle_execution_policy", "oracle_execution_policy"),
    ("oracle_market_microstructure", "oracle_market_microstructure"),
    ("oracle_order_book_intelligence", "oracle_order_book_intelligence"),
    ("oracle_order_flow_engine", "oracle_order_flow_engine"),
    ("oracle_live_opportunity_monitor", "oracle_live_opportunity_monitor"),
    ("oracle_opportunity_lifecycle", "oracle_opportunity_lifecycle"),
    ("oracle_smart_alert_prioritizer", "oracle_smart_alert_prioritizer"),
    ("oracle_portfolio_exposure_manager", "oracle_portfolio_exposure_manager"),
    ("oracle_execution_queue_manager", "oracle_execution_queue_manager"),
    ("oracle_live_price_discovery", "oracle_live_price_discovery"),
    ("oracle_market_regime_engine", "oracle_market_regime_engine"),
    ("oracle_expected_value_engine", "oracle_expected_value_engine"),
    ("oracle_trade_readiness_report", "oracle_trade_readiness_report"),
    ("oracle_final_decision_router", "oracle_final_decision_router"),
    ("oracle_final_alert_formatter", "oracle_final_alert_formatter"),
    ("oracle_alert_outbox_manager", "oracle_alert_outbox_manager"),
    ("oracle_alert_delivery_bridge", "oracle_alert_delivery_bridge"),
    ("oracle_live_trade_tracker", "oracle_live_trade_tracker"),
    ("oracle_outcome_scoring_engine", "oracle_outcome_scoring_engine"),
    ("oracle_signal_learning_memory", "oracle_signal_learning_memory"),
    ("oracle_learning_score_adapter", "oracle_learning_score_adapter"),
]


def check_module(module_name, object_name):
    row = {
        "module": module_name,
        "object": object_name,
        "import": "FAIL",
        "diagnostics": None,
        "status": "error",
        "error": None,
    }

    try:
        mod = importlib.import_module(module_name)
        row["import"] = "OK"

        obj = getattr(mod, object_name, None)
        if obj is None:
            row["status"] = "missing_object"
            row["error"] = f"Missing object: {object_name}"
            return row

        if hasattr(obj, "diagnostics"):
            try:
                row["diagnostics"] = obj.diagnostics()
                row["status"] = row["diagnostics"].get("status", "ok") if isinstance(row["diagnostics"], dict) else "ok"
            except Exception as exc:
                row["status"] = "diagnostics_error"
                row["error"] = str(exc)
        else:
            row["status"] = "ok_no_diagnostics"

    except Exception as exc:
        row["error"] = str(exc)

    return row


def run():
    rows = [check_module(m, o) for m, o in MODULES]

    ok = sum(1 for r in rows if r.get("import") == "OK" and str(r.get("status")).startswith("ok"))
    fail = len(rows) - ok

    result = {
        "module": "oracle_system_health",
        "version": "ORACLE-072",
        "status": "ok" if fail == 0 else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "total": len(rows),
        "ok": ok,
        "fail": fail,
        "rows": rows,
    }

    print("")
    print("============================================================")
    print(" ORACLE SYSTEM HEALTH")
    print("============================================================")
    print(f"Status: {result['status']}")
    print(f"Modules: {result['total']} | OK: {result['ok']} | Fail/Degraded: {result['fail']}")
    print("============================================================")

    for r in rows:
        icon = "✅" if r.get("import") == "OK" and str(r.get("status")).startswith("ok") else "⚠️"
        print(f"{icon} {r.get('module')} :: import={r.get('import')} status={r.get('status')}")
        if r.get("error"):
            print(f"   error: {r.get('error')}")

    print("============================================================")
    print(" END ORACLE SYSTEM HEALTH")
    print("============================================================")

    return result


if __name__ == "__main__":
    run()
