from pathlib import Path

TARGET = Path("oracle_smoke_test.py")

TARGET.write_text(r'''
"""
KQ-015.3 — Oracle Module Smoke Test

Purpose:
- Quickly verify core Oracle modules import correctly
- Run diagnostics where available
- Catch broken modules before starting telegram_bot.py
"""

import importlib
import traceback


MODULES = [
    "oracle_message_cache",
    "oracle_dashboard_refresh",
    "oracle_opportunity_intelligence",
    "oracle_market_memory",
    "oracle_memory_bridge",
    "oracle_outcome_tracker",
    "oracle_strategy_analytics",
    "oracle_self_learning",
    "oracle_adaptive_ranking",
    "oracle_event_detection",
    "oracle_event_alert_ui",
    "oracle_event_pipeline",
    "oracle_continuous_intelligence",
]


def run_smoke_test():
    results = []

    for name in MODULES:
        item = {
            "module": name,
            "import_ok": False,
            "diagnostics_ok": None,
            "error": None,
        }

        try:
            module = importlib.import_module(name)
            item["import_ok"] = True

            if hasattr(module, "diagnostics"):
                try:
                    item["diagnostics"] = module.diagnostics()
                    item["diagnostics_ok"] = True
                except Exception as e:
                    item["diagnostics_ok"] = False
                    item["error"] = f"diagnostics failed: {e}"

        except Exception as e:
            item["error"] = str(e)
            item["traceback"] = traceback.format_exc()

        results.append(item)

    return results


def format_results(results):
    lines = []
    lines.append("🧪 ORACLE SMOKE TEST")
    lines.append("")

    failures = 0

    for item in results:
        status = "OK" if item["import_ok"] else "FAIL"

        if item["diagnostics_ok"] is False:
            status = "WARN"

        if status in ("FAIL", "WARN"):
            failures += 1

        lines.append(f"{status} — {item['module']}")

        if item.get("error"):
            lines.append(f"  Error: {item['error']}")

    lines.append("")
    lines.append(f"Result: {len(results) - failures} OK / {failures} issues")

    return "\n".join(lines)


if __name__ == "__main__":
    print(format_results(run_smoke_test()))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" KQ-015.3 INSTALLED")
print(" Oracle Module Smoke Test")
print("===================================")
print()
print("Created:")
print(" oracle_smoke_test.py")
print()
print("Run:")
print(" python oracle_smoke_test.py")