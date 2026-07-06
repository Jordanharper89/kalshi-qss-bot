from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_pipeline_doctor.py")

CODE = r'''
"""
ORACLE-073 Pipeline Doctor

Purpose:
- Run Oracle pipeline and diagnose missing/degraded runtime fields.
- Checks final decisions, alerts, queue, EV, learning, regime, and delivery bridge.
- Does NOT place trades.
"""

from datetime import datetime, UTC
import traceback


REQUIRED_STATUS_KEYS = [
    "market_regime_status",
    "expected_value_status",
    "trade_readiness_status",
    "final_decision_status",
    "final_alert_status",
    "alert_outbox_status",
    "alert_delivery_status",
    "live_trade_tracker_status",
    "outcome_scoring_status",
    "signal_learning_status",
    "learning_adapter_status",
    "learning_final_router_status",
]

REQUIRED_ITEM_KEYS = [
    "ticker",
    "title",
    "consensus_final_recommendation",
    "execution_decision",
    "tradability",
    "order_book_rating",
    "ev_decision",
    "trade_readiness_verdict",
    "oracle_final_action",
    "oracle_final_score",
]


def run():
    print("")
    print("============================================================")
    print(" ORACLE PIPELINE DOCTOR")
    print("============================================================")

    result = {
        "module": "oracle_pipeline_doctor",
        "version": "ORACLE-073",
        "timestamp": datetime.now(UTC).isoformat(),
        "status": "ok",
        "warnings": [],
        "errors": [],
        "repairs": [],
    }

    try:
        import oracle_continuous_intelligence as o
        o.run_cycle()
        s = o.status()
    except Exception as exc:
        result["status"] = "error"
        result["errors"].append(f"Pipeline failed to run: {exc}")
        result["traceback"] = traceback.format_exc()
        _print(result)
        return result

    ranked = s.get("last_ranked") or []

    if not ranked:
        result["warnings"].append("No ranked opportunities returned.")
        result["repairs"].append("Check Kalshi loader, market cache, arbitrage source, and continuous intelligence source adapters.")

    for key in REQUIRED_STATUS_KEYS:
        block = s.get(key)
        if not isinstance(block, dict):
            result["warnings"].append(f"Missing status block: {key}")
            result["repairs"].append(f"Confirm the module that creates {key} is installed and patched into oracle_continuous_intelligence.py.")
        else:
            status = block.get("status")
            if status not in ("ok", None):
                result["warnings"].append(f"{key} reports status={status}")
                if block.get("error"):
                    result["errors"].append(f"{key} error: {block.get('error')}")

    if ranked:
        top = ranked[0]
        for key in REQUIRED_ITEM_KEYS:
            if key not in top:
                result["warnings"].append(f"Top ranked opportunity missing field: {key}")

    action_counts = s.get("final_decision_status", {}).get("action_counts") if isinstance(s.get("final_decision_status"), dict) else None
    regime = s.get("market_regime")

    if action_counts:
        if action_counts.get("NO_TRADE", 0) == sum(action_counts.values()):
            result["warnings"].append("All final actions are NO_TRADE.")
            result["repairs"].append("This can be correct in THIN_LIQUIDITY. Improve order-book depth/price inputs before loosening gates.")

    if regime == "THIN_LIQUIDITY":
        result["repairs"].append("Pipeline detects THIN_LIQUIDITY. Prioritize real bid/ask depth, volume, and fill-probability data.")

    queue_status = s.get("execution_queue_status", {})
    if isinstance(queue_status, dict) and queue_status.get("queued", 0) == 0:
        result["repairs"].append("Execution queue is empty. This is expected if Gatekeeper/EV/Portfolio are blocking all candidates.")

    delivery_status = s.get("alert_delivery_status", {})
    if isinstance(delivery_status, dict) and delivery_status.get("prepared", 0) == 0:
        result["repairs"].append("No delivery payloads prepared. This is expected if final alerts/outbox suppress NO_TRADE items.")

    if result["errors"]:
        result["status"] = "error"
    elif result["warnings"]:
        result["status"] = "degraded"

    result["summary"] = {
        "ranked_count": len(ranked),
        "market_regime": regime,
        "final_actions": action_counts,
        "queue_counts": queue_status.get("counts") if isinstance(queue_status, dict) else None,
        "delivery_prepared": delivery_status.get("prepared") if isinstance(delivery_status, dict) else None,
    }

    _print(result)
    return result


def _print(result):
    print(f"Status: {result.get('status')}")
    print(f"Timestamp: {result.get('timestamp')}")
    print("------------------------------------------------------------")

    summary = result.get("summary") or {}
    if summary:
        print("Summary:")
        for k, v in summary.items():
            print(f"- {k}: {v}")
        print("------------------------------------------------------------")

    warnings = result.get("warnings") or []
    errors = result.get("errors") or []
    repairs = result.get("repairs") or []

    if errors:
        print("Errors:")
        for e in errors:
            print(f"- {e}")
        print("------------------------------------------------------------")

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"- {w}")
        print("------------------------------------------------------------")

    if repairs:
        print("Recommended Repairs / Notes:")
        seen = set()
        for r in repairs:
            if r not in seen:
                print(f"- {r}")
                seen.add(r)

    print("============================================================")
    print(" END ORACLE PIPELINE DOCTOR")
    print("============================================================")


if __name__ == "__main__":
    run()
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle073_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-073 INSTALLER")
    print(" Pipeline Doctor")
    print("===================================")

    b = backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")

    print("[OK] Created oracle_pipeline_doctor.py")
    if b:
        print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_pipeline_doctor.py")
    print("")
    print("[DONE] ORACLE-073 Pipeline Doctor installed")


if __name__ == "__main__":
    main()