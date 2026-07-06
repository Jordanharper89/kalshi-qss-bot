from pathlib import Path

TARGET = Path("oracle_core.py")

TARGET.write_text(r'''
"""
ORACLE-038 — Core Integration Layer

Purpose:
- Centralize Oracle's major systems behind one safe interface
- Reduce direct cross-module coupling
- Provide one place for status, diagnostics, startup, and pipeline cycles
- Prepare Telegram to talk to one Oracle core instead of many separate modules

Safe module:
- Does not execute trades
- Does not place orders
"""

import time
import traceback
import threading


class OracleCore:
    def __init__(self):
        self.lock = threading.Lock()
        self.started = False
        self.started_at = None
        self.last_error = None
        self.last_cycle_result = None
        self.modules = {}

    def _now(self):
        return time.time()

    def _load_module(self, name):
        try:
            module = __import__(name)
            self.modules[name] = {
                "loaded": True,
                "error": None,
            }
            return module
        except Exception as e:
            self.modules[name] = {
                "loaded": False,
                "error": str(e),
            }
            return None

    def load_modules(self):
        names = [
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

        for name in names:
            self._load_module(name)

        return self.modules

    def start(self):
        """
        Start Oracle core systems.
        Currently delegates continuous intelligence startup if available.
        Safe to call multiple times.
        """
        with self.lock:
            if self.started:
                return {
                    "ok": True,
                    "already_started": True,
                }

            self.started = True
            self.started_at = self._now()
            self.last_error = None

        self.load_modules()

        try:
            import oracle_continuous_intelligence
            oracle_continuous_intelligence.start(interval_seconds=10)
        except Exception as e:
            self.last_error = str(e)
            print(f"[ORACLE-038] continuous intelligence start error: {e}")

        return {
            "ok": True,
            "started": True,
        }

    def stop(self):
        try:
            import oracle_continuous_intelligence
            oracle_continuous_intelligence.stop()
        except Exception as e:
            self.last_error = str(e)

        with self.lock:
            self.started = False

        return {
            "ok": True,
            "stopped": True,
        }

    def run_cycle(self, opportunities=None):
        """
        Run one Oracle intelligence cycle.
        """
        try:
            import oracle_continuous_intelligence

            result = oracle_continuous_intelligence.run_cycle(opportunities=opportunities)

            with self.lock:
                self.last_cycle_result = result
                self.last_error = None if result.get("ok") else result.get("error")

            return result

        except Exception as e:
            err = traceback.format_exc()

            with self.lock:
                self.last_error = str(e)

            print("[ORACLE-038] run_cycle error:")
            print(err)

            return {
                "ok": False,
                "error": str(e),
            }

    def status(self):
        self.load_modules()

        continuous_status = None
        memory_summary = None
        event_count = None

        try:
            import oracle_continuous_intelligence
            continuous_status = oracle_continuous_intelligence.status()
        except Exception as e:
            continuous_status = {
                "error": str(e),
            }

        try:
            from oracle_market_memory import memory_summary as _memory_summary
            memory_summary = _memory_summary()
        except Exception as e:
            memory_summary = {
                "error": str(e),
            }

        try:
            from oracle_event_detection import get_recent_events
            event_count = len(get_recent_events(limit=100))
        except Exception:
            event_count = None

        loaded = sum(1 for item in self.modules.values() if item.get("loaded"))
        failed = sum(1 for item in self.modules.values() if not item.get("loaded"))

        return {
            "started": self.started,
            "started_at": self.started_at,
            "last_error": self.last_error,
            "modules_loaded": loaded,
            "modules_failed": failed,
            "modules": self.modules,
            "continuous_intelligence": continuous_status,
            "market_memory": memory_summary,
            "recent_event_count": event_count,
            "last_cycle_result": self.last_cycle_result,
        }

    def format_status(self):
        s = self.status()
        ci = s.get("continuous_intelligence") or {}
        mem = s.get("market_memory") or {}

        return f"""
🧠 ORACLE CORE STATUS

Started:
{s.get("started")}

Modules Loaded:
{s.get("modules_loaded")}

Modules Failed:
{s.get("modules_failed")}

Continuous Intelligence:
Running: {ci.get("running")}
Cycles: {ci.get("cycles_completed")}
Opportunities Seen: {ci.get("opportunities_seen")}
Ranked: {ci.get("ranked_count")}
Events: {ci.get("events_detected")}
High Priority: {ci.get("high_priority_events")}
Last Error: {ci.get("last_error")}

Market Memory:
Markets: {mem.get("markets")}
Events: {mem.get("events")}
Resolved: {mem.get("resolved")}
Win Rate: {mem.get("win_rate")}

Recent Event Count:
{s.get("recent_event_count")}

Core Last Error:
{s.get("last_error")}
""".strip()

    def diagnostics(self):
        return {
            "module": "oracle_core",
            "status": "ok",
            "core_status": self.status(),
        }


oracle_core = OracleCore()


def start():
    return oracle_core.start()


def stop():
    return oracle_core.stop()


def run_cycle(opportunities=None):
    return oracle_core.run_cycle(opportunities=opportunities)


def status():
    return oracle_core.status()


def format_status():
    return oracle_core.format_status()


def diagnostics():
    return oracle_core.diagnostics()


if __name__ == "__main__":
    print(format_status())
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-038 INSTALLED")
print(" Core Integration Layer")
print("===================================")
print()
print("Created:")
print(" oracle_core.py")
print()
print("Test:")
print(" python oracle_core.py")