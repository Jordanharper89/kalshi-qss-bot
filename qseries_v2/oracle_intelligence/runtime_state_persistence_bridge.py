"""
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
