"""
OI-072 Runtime Recovery Bridge

Purpose:
- Convert caller-supplied recovery context into safe ORP-001 startup proposals.
- Describe recommended runtime actions without executing them.
- Keep Q Series as the sole runtime authorization and execution owner.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
- No filesystem, SQLite, runtime control, or persistence writes.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .persistence_proposal_contract import OracleRecoveryPersistenceProposal
from .runtime_recovery_manager import (
    runtime_recovery_manager,
    RuntimeRecoveryManager,
)


class RuntimeRecoveryBridge:
    module_name = "oi_072_runtime_recovery_bridge"

    def __init__(
        self,
        recovery_manager: Optional[RuntimeRecoveryManager] = None,
    ) -> None:
        self.recovery_manager = recovery_manager or runtime_recovery_manager
        self._last_recovery: Optional[Dict[str, Any]] = None

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "executed": False,
            "started": False,
            "persisted": False,
            "recovery_manager": self._safe_status(self.recovery_manager),
            "has_last_recovery": self._last_recovery is not None,
            "boundary": "oracle_recovery_proposal_only",
        }

    def startup_check(
        self,
        restore_data: Optional[Mapping[str, Any]] = None,
        proposed_at: str = "",
        source_runtime_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        manager_plan = self.recovery_manager.recovery_plan(
            restore_data=restore_data,
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
        )
        recovery_plan = manager_plan.get("recovery_plan", {})
        proposal = self._bridge_recovery_proposal(
            recovery_plan=recovery_plan,
            manager_plan=manager_plan,
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            operation="startup_check",
        )

        decision = {
            "status": "ok",
            "read_only": True,
            "executed": False,
            "started": False,
            "persisted": False,
            "startup_action": recovery_plan.get("recommended_action", "cold_start"),
            "safe_to_resume": recovery_plan.get("safe_to_resume", True),
            "warnings": recovery_plan.get("warnings", []),
            "steps": recovery_plan.get("steps", []),
            "plan": manager_plan,
            "proposal": proposal,
            "explanation": "Startup recovery proposal generated; Q Series must authorize any runtime action.",
        }
        self._last_recovery = decision
        return decision

    def recover_and_start(
        self,
        restore_data: Optional[Mapping[str, Any]] = None,
        proposed_at: str = "",
        source_runtime_id: Optional[str] = None,
        validation_cycle: bool = True,
        markets=None,
    ) -> Dict[str, Any]:
        check = self.startup_check(
            restore_data=restore_data,
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
        )
        proposal = check["proposal"]
        result = {
            "status": "ok",
            "read_only": True,
            "executed": False,
            "started": False,
            "persisted": False,
            "startup_action": check.get("startup_action"),
            "safe_to_resume": check.get("safe_to_resume"),
            "warnings": check.get("warnings", []),
            "steps": check.get("steps", []),
            "proposal": proposal,
            "startup_check": check,
            "requested_validation_cycle": bool(validation_cycle),
            "requested_market_count": len(markets or []),
            "explanation": "Recovery was not executed and runtime was not started; this is an ORP-001 proposal for Q Series.",
        }
        self._last_recovery = result
        return result

    def last_recovery(self, recovery_data: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        if recovery_data is not None:
            return {
                "status": "ok",
                "read_only": True,
                "executed": False,
                "started": False,
                "persisted": False,
                "last_recovery": dict(recovery_data),
                "explanation": "Caller-supplied recovery data returned without runtime or persistence access.",
            }
        if self._last_recovery is None:
            return {
                "status": "unavailable",
                "read_only": True,
                "executed": False,
                "started": False,
                "persisted": False,
                "last_recovery": None,
                "explanation": "No recovery proposal has been generated and no caller-supplied data was provided.",
            }
        return {
            "status": "ok",
            "read_only": True,
            "executed": False,
            "started": False,
            "persisted": False,
            "last_recovery": self._last_recovery,
            "explanation": "Last in-memory proposal result returned without persistence access.",
        }

    def recovery_summary(
        self,
        recovery_info: Optional[Mapping[str, Any]] = None,
        proposed_at: str = "",
        source_runtime_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if recovery_info is None:
            return {
                "status": "unavailable",
                "read_only": True,
                "executed": False,
                "started": False,
                "persisted": False,
                "recovery": None,
                "last_recovery": self._last_recovery,
                "explanation": "No caller-supplied recovery information was provided; no runtime or persistence access occurred.",
            }

        summary = self.recovery_manager.recover_summary(
            recovery_info=recovery_info,
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
        )
        return {
            "status": "ok",
            "read_only": True,
            "executed": False,
            "started": False,
            "persisted": False,
            "recovery": summary,
            "last_recovery": self._last_recovery,
            "explanation": "Caller-supplied recovery information summarized without runtime or persistence access.",
        }

    def _bridge_recovery_proposal(
        self,
        *,
        recovery_plan: Mapping[str, Any],
        manager_plan: Mapping[str, Any],
        proposed_at: str,
        source_runtime_id: Optional[str],
        operation: str,
    ) -> OracleRecoveryPersistenceProposal:
        evidence = {
            "manager_module": "oi_071_runtime_recovery_manager",
            "manager_proposal_id": getattr(manager_plan.get("proposal"), "proposal_id", None),
            "restorable": bool(manager_plan.get("restorable", False)),
            "latest_runtime": manager_plan.get("latest_runtime") or {},
            "latest_dashboard": manager_plan.get("latest_dashboard") or {},
            "recent_events": manager_plan.get("recent_events", []) or [],
        }
        proposal = OracleRecoveryPersistenceProposal(
            oracle_module_id=self.module_name,
            recovery_action=str(recovery_plan.get("recommended_action") or "cold_start"),
            safe_to_resume=bool(recovery_plan.get("safe_to_resume", True)),
            warnings=tuple(str(item) for item in recovery_plan.get("warnings", []) or ()),
            steps=tuple(str(item) for item in recovery_plan.get("steps", []) or ()),
            payload={
                "startup_action": recovery_plan.get("recommended_action") or "cold_start",
                "safe_to_resume": bool(recovery_plan.get("safe_to_resume", True)),
                "warning_count": len(recovery_plan.get("warnings", []) or ()),
                "step_count": len(recovery_plan.get("steps", []) or ()),
            },
            evidence=evidence,
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            replay_metadata={
                "schema_version": "ORP-001",
                "operation": operation,
                "qseries_authorization_required": True,
                "boundary": "oracle_to_qseries_runtime_control_proposal",
            },
        )
        proposal.validate()
        return proposal

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"


runtime_recovery_bridge = RuntimeRecoveryBridge()
