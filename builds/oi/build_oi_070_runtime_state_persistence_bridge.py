from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "runtime_state_persistence_bridge.py"
TEST = ROOT / "test_oi_070_runtime_state_persistence_bridge.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-070 Runtime State Persistence Bridge

Purpose:
- Connect OI-068 Command Center to OI-069 Runtime State Store.
- Persist runtime status/dashboard snapshots.
- Log runtime lifecycle/cycle events.
- Provide restart restore summary.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .oracle_intelligence_command_center import (
    oracle_intelligence_command_center,
    OracleIntelligenceCommandCenter,
)
from .oracle_runtime_state_store import (
    oracle_runtime_state_store,
    OracleRuntimeStateStore,
)


class RuntimeStatePersistenceBridge:
    module_name = "oi_070_runtime_state_persistence_bridge"

    def __init__(
        self,
        command_center: Optional[OracleIntelligenceCommandCenter] = None,
        state_store: Optional[OracleRuntimeStateStore] = None,
    ) -> None:
        self.command_center = command_center or oracle_intelligence_command_center
        self.state_store = state_store or oracle_runtime_state_store

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "command_center": self._safe_status(self.command_center),
            "state_store": self._safe_status(self.state_store),
        }

    def persist_status(self) -> Dict[str, Any]:
        status = self.command_center.status()

        saved = self.state_store.save_snapshot(
            snapshot_type="runtime_status",
            source_module=self.module_name,
            payload=status,
        )

        return {
            "status": "ok",
            "read_only": True,
            "saved": saved,
            "runtime_status": status,
        }

    def persist_dashboard(self) -> Dict[str, Any]:
        dashboard = self.command_center.dashboard()

        saved = self.state_store.save_snapshot(
            snapshot_type="command_center_dashboard",
            source_module=self.module_name,
            payload=dashboard,
        )

        return {
            "status": "ok",
            "read_only": True,
            "saved": saved,
            "dashboard": dashboard,
        }

    def persist_full_state(self) -> Dict[str, Any]:
        status_result = self.persist_status()
        dashboard_result = self.persist_dashboard()

        event = self.state_store.log_event(
            event_type="runtime_state_persisted",
            severity="info",
            source_module=self.module_name,
            payload={
                "runtime_snapshot_id": status_result["saved"]["snapshot_id"],
                "dashboard_snapshot_id": dashboard_result["saved"]["snapshot_id"],
            },
        )

        return {
            "status": "ok",
            "read_only": True,
            "runtime": status_result,
            "dashboard": dashboard_result,
            "event": event,
        }

    def run_once_and_persist(self, markets=None, **kwargs) -> Dict[str, Any]:
        run = self.command_center.run_once(markets=markets or [], **kwargs)

        event = self.state_store.log_event(
            event_type="runtime_cycle_completed",
            severity="info" if run.get("status") == "ok" else "error",
            source_module=self.module_name,
            payload={
                "status": run.get("status"),
                "cycle": run.get("result", {}).get("cycle"),
            },
        )

        persisted = self.persist_full_state()

        return {
            "status": run.get("status"),
            "read_only": True,
            "run": run,
            "event": event,
            "persisted": persisted,
        }

    def start_and_log(self) -> Dict[str, Any]:
        started = self.command_center.start_runtime()

        event = self.state_store.log_event(
            event_type="runtime_started",
            severity="info",
            source_module=self.module_name,
            payload=started,
        )

        persisted = self.persist_status()

        return {
            "status": "ok",
            "read_only": True,
            "started": started,
            "event": event,
            "persisted": persisted,
        }

    def stop_and_log(self) -> Dict[str, Any]:
        stopped = self.command_center.stop_runtime()

        event = self.state_store.log_event(
            event_type="runtime_stopped",
            severity="info",
            source_module=self.module_name,
            payload=stopped,
        )

        persisted = self.persist_full_state()

        return {
            "status": "ok",
            "read_only": True,
            "stopped": stopped,
            "event": event,
            "persisted": persisted,
        }

    def restore_summary(self) -> Dict[str, Any]:
        restore = self.state_store.restore_runtime_summary()

        return {
            "status": "ok",
            "read_only": True,
            "restore": restore,
            "restorable": restore.get("restorable", False),
        }

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"


runtime_state_persistence_bridge = RuntimeStatePersistenceBridge()
'''

test_code = r'''from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_runtime_state_store import OracleRuntimeStateStore
from qseries_v2.oracle_intelligence.runtime_state_persistence_bridge import RuntimeStatePersistenceBridge


class FakeCommandCenter:
    def __init__(self):
        self.running = False
        self.cycles = 0

    def status(self):
        return {
            "status": "ok",
            "read_only": True,
            "runtime_status": "running" if self.running else "stopped",
            "health": "healthy",
            "cycles": self.cycles,
            "metrics": {"errors": 0},
        }

    def dashboard(self):
        return {
            "status": "ok",
            "read_only": True,
            "runtime": self.status(),
            "last_cycle": {"cycle": self.cycles, "status": "ok"},
        }

    def start_runtime(self):
        self.running = True
        return {"status": "ok", "read_only": True, "runtime": self.status()}

    def stop_runtime(self):
        self.running = False
        return {"status": "ok", "read_only": True, "runtime": self.status()}

    def run_once(self, markets=None, **kwargs):
        self.running = True
        self.cycles += 1
        return {
            "status": "ok",
            "read_only": True,
            "result": {"cycle": self.cycles, "markets": len(markets or [])},
        }


def test_oi_070_runtime_state_persistence_bridge():
    test_db = Path("qseries_v2") / "data" / "test_runtime_state_bridge.sqlite3"

    if test_db.exists():
        test_db.unlink()

    store = OracleRuntimeStateStore(test_db)
    center = FakeCommandCenter()
    bridge = RuntimeStatePersistenceBridge(center, store)

    started = bridge.start_and_log()
    assert started["status"] == "ok"
    assert started["event"]["event_type"] == "runtime_started"

    run = bridge.run_once_and_persist(markets=[{"ticker": "STATE-TEST"}])
    assert run["status"] == "ok"
    assert run["event"]["event_type"] == "runtime_cycle_completed"

    full = bridge.persist_full_state()
    assert full["status"] == "ok"

    restore = bridge.restore_summary()
    assert restore["status"] == "ok"
    assert restore["restorable"] is True

    stopped = bridge.stop_and_log()
    assert stopped["status"] == "ok"
    assert stopped["event"]["event_type"] == "runtime_stopped"

    store_status = store.status()
    assert store_status["snapshots"] >= 4
    assert store_status["events"] >= 4

    status = bridge.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-070 Runtime State Persistence Bridge")
    print({
        "snapshots": store_status["snapshots"],
        "events": store_status["events"],
        "restorable": restore["restorable"],
    })


if __name__ == "__main__":
    test_oi_070_runtime_state_persistence_bridge()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .runtime_state_persistence_bridge import runtime_state_persistence_bridge, RuntimeStatePersistenceBridge\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-070 INSTALLER")
print(" Runtime State Persistence Bridge")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-070 installed")
print()
print("Run:")
print("python test_oi_070_runtime_state_persistence_bridge.py")