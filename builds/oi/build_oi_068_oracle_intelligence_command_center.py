from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "oracle_intelligence_command_center.py"
TEST = ROOT / "test_oi_068_oracle_intelligence_command_center.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-068 Oracle Intelligence Command Center

Purpose:
- Single control/status surface for Oracle autonomous research.
- Expose runtime health, metrics, queue, active research, refresh, drift,
  notifications, and portfolio intelligence in one read-only command center.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .autonomous_research_runtime import autonomous_research_runtime, AutonomousResearchRuntime


class OracleIntelligenceCommandCenter:
    module_name = "oi_068_oracle_intelligence_command_center"

    def __init__(self, runtime: Optional[AutonomousResearchRuntime] = None) -> None:
        self.runtime = runtime or autonomous_research_runtime

    def status(self) -> Dict[str, Any]:
        runtime_status = self.runtime.status()

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "runtime_status": runtime_status.get("status"),
            "health": runtime_status.get("health"),
            "cycles": runtime_status.get("cycles"),
            "metrics": runtime_status.get("metrics", {}),
        }

    def dashboard(self) -> Dict[str, Any]:
        runtime_status = self.runtime.status()
        last_outputs = self.runtime.last_outputs()

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "runtime": runtime_status,
            "queue": runtime_status.get("queue", {}),
            "scheduler": runtime_status.get("scheduler", {}),
            "refresh": runtime_status.get("refresh", {}),
            "last_cycle": self._summarize_last_cycle(last_outputs),
            "last_outputs": last_outputs,
        }

    def start_runtime(self) -> Dict[str, Any]:
        started = self.runtime.start()
        return {
            "status": "ok",
            "read_only": True,
            "command": "start_runtime",
            "runtime": started,
        }

    def stop_runtime(self) -> Dict[str, Any]:
        stopped = self.runtime.stop()
        return {
            "status": "ok",
            "read_only": True,
            "command": "stop_runtime",
            "runtime": stopped,
        }

    def run_once(self, markets=None, **kwargs) -> Dict[str, Any]:
        result = self.runtime.run_once(markets=markets or [], **kwargs)

        return {
            "status": result.get("status"),
            "read_only": True,
            "command": "run_once",
            "result": result,
            "dashboard": self.dashboard(),
        }

    def health_report(self) -> Dict[str, Any]:
        status = self.runtime.status()
        metrics = status.get("metrics", {})

        warnings = []

        if status.get("health") != "healthy":
            warnings.append("runtime_health_not_healthy")

        if metrics.get("errors", 0) > 0:
            warnings.append("runtime_errors_present")

        queue = status.get("queue", {})
        if queue.get("queued", 0) > 100:
            warnings.append("queue_depth_high")

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "health": status.get("health"),
            "warnings": warnings,
            "metrics": metrics,
            "runtime_status": status.get("status"),
            "uptime_seconds": status.get("uptime_seconds"),
        }

    def command_summary_text(self) -> str:
        d = self.dashboard()
        runtime = d.get("runtime", {})
        metrics = runtime.get("metrics", {})

        lines = [
            "=" * 58,
            " ORACLE INTELLIGENCE COMMAND CENTER",
            "=" * 58,
            f"Runtime: {runtime.get('status')}",
            f"Health: {runtime.get('health')}",
            f"Uptime Seconds: {runtime.get('uptime_seconds')}",
            f"Cycles: {runtime.get('cycles')}",
            "",
            "[Metrics]",
            f"- Markets Scanned: {metrics.get('markets_scanned', 0)}",
            f"- Opportunities Found: {metrics.get('opportunities_found', 0)}",
            f"- Queued Added: {metrics.get('queued_added', 0)}",
            f"- Research Runs: {metrics.get('research_runs', 0)}",
            f"- Refreshes: {metrics.get('refreshes', 0)}",
            f"- Drift Checks: {metrics.get('drift_checks', 0)}",
            f"- Notifications: {metrics.get('notifications', 0)}",
            f"- Portfolio Updates: {metrics.get('portfolio_updates', 0)}",
            f"- Errors: {metrics.get('errors', 0)}",
            "",
            "[Execution Boundary]",
            "- Oracle is read-only research.",
            "- Q Series remains responsible for execution.",
        ]

        return "\n".join(lines)

    def _summarize_last_cycle(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        if not outputs:
            return {
                "status": "none",
                "message": "No runtime cycle has completed yet.",
            }

        discovery = outputs.get("discovery", {})
        research = outputs.get("research", {})
        refresh = outputs.get("refresh", {})
        notifications = outputs.get("notifications", {})
        portfolio = outputs.get("portfolio", {})

        return {
            "status": outputs.get("status"),
            "cycle": outputs.get("cycle"),
            "started_at": outputs.get("started_at"),
            "completed_at": outputs.get("completed_at"),
            "markets_scanned": discovery.get("markets_scanned", 0),
            "opportunities_found": discovery.get("opportunities_found", 0),
            "research_completed": research.get("tracked_sessions", 0),
            "refreshes": refresh.get("refreshed_count", 0),
            "notifications": notifications.get("notification_count", 0),
            "portfolio_state": portfolio.get("portfolio_state", {}),
        }


oracle_intelligence_command_center = OracleIntelligenceCommandCenter()
'''

test_code = r'''from qseries_v2.oracle_intelligence.oracle_intelligence_command_center import OracleIntelligenceCommandCenter


class FakeRuntime:
    def __init__(self):
        self.running = False
        self.outputs = {}
        self.cycles = 0

    def start(self):
        self.running = True
        return self.status()

    def stop(self):
        self.running = False
        return self.status()

    def status(self):
        return {
            "module": "fake_runtime",
            "status": "running" if self.running else "stopped",
            "read_only": True,
            "uptime_seconds": 1.0,
            "cycles": self.cycles,
            "last_cycle_at": "now",
            "metrics": {
                "markets_scanned": 1,
                "opportunities_found": 1,
                "queued_added": 1,
                "research_runs": 1,
                "refreshes": 0,
                "drift_checks": 1,
                "notifications": 0,
                "portfolio_updates": 1,
                "errors": 0,
            },
            "queue": {"status": "ok", "queued": 1, "processed": 0},
            "scheduler": {"status": "ok", "scheduled_jobs": 0},
            "refresh": {"status": "ok", "active_sessions": 1},
            "health": "healthy",
        }

    def run_once(self, markets=None, **kwargs):
        self.running = True
        self.cycles += 1
        self.outputs = {
            "status": "ok",
            "cycle": self.cycles,
            "started_at": "start",
            "completed_at": "end",
            "discovery": {"markets_scanned": len(markets or []), "opportunities_found": 1},
            "research": {"tracked_sessions": 1},
            "refresh": {"refreshed_count": 0},
            "notifications": {"notification_count": 0},
            "portfolio": {"portfolio_state": {"state": "normal"}},
        }
        return self.outputs

    def last_outputs(self):
        return self.outputs


def test_oi_068_oracle_intelligence_command_center():
    center = OracleIntelligenceCommandCenter(FakeRuntime())

    start = center.start_runtime()
    assert start["status"] == "ok"
    assert start["runtime"]["status"] == "running"

    run = center.run_once(markets=[{"ticker": "CMD-TEST"}])
    assert run["status"] == "ok"
    assert run["dashboard"]["last_cycle"]["opportunities_found"] == 1

    dash = center.dashboard()
    assert dash["status"] == "ok"
    assert dash["read_only"] is True
    assert dash["runtime"]["health"] == "healthy"

    health = center.health_report()
    assert health["health"] == "healthy"
    assert health["warnings"] == []

    text = center.command_summary_text()
    assert "ORACLE INTELLIGENCE COMMAND CENTER" in text
    assert "Oracle is read-only research" in text

    stop = center.stop_runtime()
    assert stop["runtime"]["status"] == "stopped"

    status = center.status()
    assert status["status"] == "ok"

    print("[PASS] OI-068 Oracle Intelligence Command Center")
    print({
        "runtime_status": status["runtime_status"],
        "health": status["health"],
        "cycles": status["cycles"],
    })


if __name__ == "__main__":
    test_oi_068_oracle_intelligence_command_center()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .oracle_intelligence_command_center import oracle_intelligence_command_center, OracleIntelligenceCommandCenter\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-068 INSTALLER")
print(" Oracle Intelligence Command Center")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-068 installed")
print()
print("Run:")
print("python test_oi_068_oracle_intelligence_command_center.py")