from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "runtime_recovery_manager.py"
TEST = ROOT / "test_oi_071_runtime_recovery_manager.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-071 Runtime Recovery Manager

Purpose:
- Read persisted Oracle runtime state from OI-069/OI-070.
- Produce a safe restart recovery plan.
- Restore telemetry context without enabling execution.
- Keep Oracle read-only.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List

from .oracle_runtime_state_store import (
    oracle_runtime_state_store,
    OracleRuntimeStateStore,
)


class RuntimeRecoveryManager:
    module_name = "oi_071_runtime_recovery_manager"

    def __init__(self, state_store: Optional[OracleRuntimeStateStore] = None) -> None:
        self.state_store = state_store or oracle_runtime_state_store

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "state_store": self._safe_status(self.state_store),
        }

    def recovery_plan(self) -> Dict[str, Any]:
        restore = self.state_store.restore_runtime_summary()

        latest_runtime = restore.get("latest_runtime")
        latest_dashboard = restore.get("latest_dashboard")
        recent_events = restore.get("recent_events", [])

        plan = self._build_plan(latest_runtime, latest_dashboard, recent_events)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "restorable": restore.get("restorable", False),
            "latest_runtime": latest_runtime,
            "latest_dashboard": latest_dashboard,
            "recent_events": recent_events,
            "recovery_plan": plan,
        }

    def recover_summary(self) -> Dict[str, Any]:
        plan = self.recovery_plan()
        runtime_payload = (
            (plan.get("latest_runtime") or {}).get("payload")
            or {}
        )
        dashboard_payload = (
            (plan.get("latest_dashboard") or {}).get("payload")
            or {}
        )

        return {
            "status": "ok",
            "read_only": True,
            "restorable": plan.get("restorable"),
            "recommended_action": plan.get("recovery_plan", {}).get("recommended_action"),
            "runtime_status": runtime_payload.get("runtime_status") or runtime_payload.get("status"),
            "health": runtime_payload.get("health"),
            "cycles": runtime_payload.get("cycles"),
            "last_cycle": dashboard_payload.get("last_cycle", {}),
            "warnings": plan.get("recovery_plan", {}).get("warnings", []),
        }

    def log_recovery_attempt(self, success: bool, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.state_store.log_event(
            event_type="runtime_recovery_attempt",
            severity="info" if success else "warning",
            source_module=self.module_name,
            payload={
                "success": success,
                "details": details or {},
            },
        )

    def _build_plan(
        self,
        latest_runtime: Optional[Dict[str, Any]],
        latest_dashboard: Optional[Dict[str, Any]],
        recent_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        warnings = []
        steps = []

        if not latest_runtime and not latest_dashboard:
            return {
                "recommended_action": "cold_start",
                "safe_to_resume": True,
                "warnings": ["no_persisted_runtime_state_found"],
                "steps": [
                    "Start Oracle runtime from clean state.",
                    "Run discovery cycle.",
                    "Rebuild active research from live market cache.",
                ],
            }

        runtime_payload = (latest_runtime or {}).get("payload", {})
        dashboard_payload = (latest_dashboard or {}).get("payload", {})

        health = runtime_payload.get("health")
        runtime_status = runtime_payload.get("runtime_status") or runtime_payload.get("status")

        if health and health != "healthy":
            warnings.append("last_runtime_health_not_healthy")

        if runtime_payload.get("metrics", {}).get("errors", 0) > 0:
            warnings.append("runtime_errors_present_before_shutdown")

        last_event_type = recent_events[0]["event_type"] if recent_events else None

        if last_event_type not in {"runtime_stopped", "runtime_state_persisted", "runtime_cycle_completed"}:
            warnings.append("last_event_not_clean_shutdown")

        if runtime_status == "running" and last_event_type != "runtime_stopped":
            steps.append("Runtime appears to have stopped unexpectedly while previously running.")

        steps.extend([
            "Load latest runtime status snapshot.",
            "Load latest command center dashboard snapshot.",
            "Preserve telemetry counters for reporting.",
            "Restart Oracle runtime in read-only research mode.",
            "Run one validation cycle before enabling continuous loop.",
        ])

        recommended = "resume_with_validation" if warnings else "resume"

        return {
            "recommended_action": recommended,
            "safe_to_resume": True,
            "warnings": warnings,
            "steps": steps,
            "last_runtime_status": runtime_status,
            "last_health": health,
            "last_event_type": last_event_type,
            "last_cycle": dashboard_payload.get("last_cycle", {}),
        }

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"


runtime_recovery_manager = RuntimeRecoveryManager()
'''

test_code = r'''from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_runtime_state_store import OracleRuntimeStateStore
from qseries_v2.oracle_intelligence.runtime_recovery_manager import RuntimeRecoveryManager


def test_oi_071_runtime_recovery_manager():
    test_db = Path("qseries_v2") / "data" / "test_runtime_recovery.sqlite3"

    if test_db.exists():
        test_db.unlink()

    store = OracleRuntimeStateStore(test_db)
    manager = RuntimeRecoveryManager(store)

    cold = manager.recovery_plan()
    assert cold["status"] == "ok"
    assert cold["read_only"] is True
    assert cold["recovery_plan"]["recommended_action"] == "cold_start"

    store.save_snapshot(
        snapshot_type="runtime_status",
        source_module="test_oi_071",
        payload={
            "runtime_status": "running",
            "health": "healthy",
            "cycles": 5,
            "metrics": {"errors": 0},
        },
    )

    store.save_snapshot(
        snapshot_type="command_center_dashboard",
        source_module="test_oi_071",
        payload={
            "last_cycle": {"cycle": 5, "status": "ok"},
        },
    )

    store.log_event(
        event_type="runtime_cycle_completed",
        severity="info",
        source_module="test_oi_071",
        payload={"cycle": 5},
    )

    plan = manager.recovery_plan()
    assert plan["status"] == "ok"
    assert plan["restorable"] is True
    assert plan["recovery_plan"]["safe_to_resume"] is True

    summary = manager.recover_summary()
    assert summary["status"] == "ok"
    assert summary["health"] == "healthy"
    assert summary["cycles"] == 5

    event = manager.log_recovery_attempt(True, {"mode": "test"})
    assert event["status"] == "ok"
    assert event["event_type"] == "runtime_recovery_attempt"

    status = manager.status()
    assert status["status"] == "ok"

    print("[PASS] OI-071 Runtime Recovery Manager")
    print({
        "recommended_action": plan["recovery_plan"]["recommended_action"],
        "warnings": plan["recovery_plan"]["warnings"],
        "summary": summary,
    })


if __name__ == "__main__":
    test_oi_071_runtime_recovery_manager()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .runtime_recovery_manager import runtime_recovery_manager, RuntimeRecoveryManager\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-071 INSTALLER")
print(" Runtime Recovery Manager")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-071 installed")
print()
print("Run:")
print("python test_oi_071_runtime_recovery_manager.py")