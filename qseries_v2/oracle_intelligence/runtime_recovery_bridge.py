"""
OI-072 Runtime Recovery Bridge

Purpose:
- Connect OI-071 Runtime Recovery Manager to Oracle Command Center/runtime.
- Run startup recovery checks.
- Log recovery attempts.
- Produce safe startup decision:
  - cold_start
  - resume
  - resume_with_validation

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
from .runtime_recovery_manager import (
    runtime_recovery_manager,
    RuntimeRecoveryManager,
)


class RuntimeRecoveryBridge:
    module_name = "oi_072_runtime_recovery_bridge"

    def __init__(
        self,
        command_center: Optional[OracleIntelligenceCommandCenter] = None,
        recovery_manager: Optional[RuntimeRecoveryManager] = None,
    ) -> None:
        self.command_center = command_center or oracle_intelligence_command_center
        self.recovery_manager = recovery_manager or runtime_recovery_manager
        self._last_recovery = None

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "command_center": self._safe_status(self.command_center),
            "recovery_manager": self._safe_status(self.recovery_manager),
            "has_last_recovery": self._last_recovery is not None,
        }

    def startup_check(self) -> Dict[str, Any]:
        plan = self.recovery_manager.recovery_plan()
        recovery_plan = plan.get("recovery_plan", {})
        action = recovery_plan.get("recommended_action", "cold_start")

        decision = {
            "status": "ok",
            "read_only": True,
            "startup_action": action,
            "safe_to_resume": recovery_plan.get("safe_to_resume", True),
            "warnings": recovery_plan.get("warnings", []),
            "steps": recovery_plan.get("steps", []),
            "plan": plan,
        }

        self._last_recovery = decision
        return decision

    def recover_and_start(
        self,
        validation_cycle: bool = True,
        markets=None,
    ) -> Dict[str, Any]:
        check = self.startup_check()
        action = check.get("startup_action")

        started = self.command_center.start_runtime()

        validation = None
        if validation_cycle or action in {"cold_start", "resume_with_validation"}:
            validation = self.command_center.run_once(markets=markets or [])

        success = started.get("status") == "ok" and (
            validation is None or validation.get("status") == "ok"
        )

        event = self.recovery_manager.log_recovery_attempt(
            success=success,
            details={
                "startup_action": action,
                "validation_cycle": validation_cycle,
                "warnings": check.get("warnings", []),
            },
        )

        result = {
            "status": "ok" if success else "error",
            "read_only": True,
            "startup_action": action,
            "started": started,
            "validation": validation,
            "recovery_event": event,
            "startup_check": check,
        }

        self._last_recovery = result
        return result

    def last_recovery(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "read_only": True,
            "last_recovery": self._last_recovery,
        }

    def recovery_summary(self) -> Dict[str, Any]:
        summary = self.recovery_manager.recover_summary()
        command_status = self.command_center.status()

        return {
            "status": "ok",
            "read_only": True,
            "recovery": summary,
            "command_center": command_status,
            "last_recovery": self._last_recovery,
        }

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"


runtime_recovery_bridge = RuntimeRecoveryBridge()
