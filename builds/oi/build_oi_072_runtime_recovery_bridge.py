from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "runtime_recovery_bridge.py"
TEST = ROOT / "test_oi_072_runtime_recovery_bridge.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
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
'''

test_code = r'''from qseries_v2.oracle_intelligence.runtime_recovery_bridge import RuntimeRecoveryBridge


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
        }

    def start_runtime(self):
        self.running = True
        return {
            "status": "ok",
            "read_only": True,
            "runtime": self.status(),
        }

    def run_once(self, markets=None):
        self.cycles += 1
        return {
            "status": "ok",
            "read_only": True,
            "result": {
                "cycle": self.cycles,
                "markets": len(markets or []),
            },
        }


class FakeRecoveryManager:
    def __init__(self):
        self.logged = []

    def status(self):
        return {"status": "ok"}

    def recovery_plan(self):
        return {
            "status": "ok",
            "read_only": True,
            "restorable": True,
            "recovery_plan": {
                "recommended_action": "resume_with_validation",
                "safe_to_resume": True,
                "warnings": ["last_event_not_clean_shutdown"],
                "steps": ["Run validation cycle."],
            },
        }

    def recover_summary(self):
        return {
            "status": "ok",
            "read_only": True,
            "recommended_action": "resume_with_validation",
            "warnings": ["last_event_not_clean_shutdown"],
        }

    def log_recovery_attempt(self, success, details=None):
        event = {
            "status": "ok",
            "read_only": True,
            "event_type": "runtime_recovery_attempt",
            "success": success,
            "details": details or {},
        }
        self.logged.append(event)
        return event


def test_oi_072_runtime_recovery_bridge():
    center = FakeCommandCenter()
    recovery = FakeRecoveryManager()
    bridge = RuntimeRecoveryBridge(center, recovery)

    check = bridge.startup_check()
    assert check["status"] == "ok"
    assert check["startup_action"] == "resume_with_validation"
    assert check["safe_to_resume"] is True

    result = bridge.recover_and_start(
        validation_cycle=True,
        markets=[{"ticker": "RECOVERY-TEST"}],
    )

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["startup_action"] == "resume_with_validation"
    assert result["validation"]["status"] == "ok"
    assert result["recovery_event"]["event_type"] == "runtime_recovery_attempt"

    last = bridge.last_recovery()
    assert last["last_recovery"]["status"] == "ok"

    summary = bridge.recovery_summary()
    assert summary["status"] == "ok"
    assert summary["command_center"]["runtime_status"] == "running"

    status = bridge.status()
    assert status["status"] == "ok"
    assert status["has_last_recovery"] is True

    print("[PASS] OI-072 Runtime Recovery Bridge")
    print({
        "startup_action": result["startup_action"],
        "validation_cycle": result["validation"]["result"]["cycle"],
        "warnings": check["warnings"],
    })


if __name__ == "__main__":
    test_oi_072_runtime_recovery_bridge()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .runtime_recovery_bridge import runtime_recovery_bridge, RuntimeRecoveryBridge\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-072 INSTALLER")
print(" Runtime Recovery Bridge")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-072 installed")
print()
print("Run:")
print("python test_oi_072_runtime_recovery_bridge.py")