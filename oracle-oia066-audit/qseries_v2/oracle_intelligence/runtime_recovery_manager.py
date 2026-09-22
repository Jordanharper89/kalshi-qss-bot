"""
OI-071 Runtime Recovery Manager

Purpose:
- Produce safe restart recovery plans from caller-supplied restore data.
- Emit immutable ORP-001 recovery/event proposals for Q Series authorization.
- Keep Oracle read-only and proposal-only.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
- No filesystem, SQLite, or runtime-state writes.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional

from .persistence_proposal_contract import (
    OracleEventPersistenceProposal,
    OracleRecoveryPersistenceProposal,
)


class RuntimeRecoveryManager:
    module_name = "oi_071_runtime_recovery_manager"

    def __init__(self, restore_data_provider: Optional[Callable[[], Mapping[str, Any]]] = None) -> None:
        self.restore_data_provider = restore_data_provider

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "persisted": False,
            "boundary": "oracle_recovery_proposal_only",
            "restore_source": "caller_supplied",
        }

    def recovery_plan(
        self,
        restore_data: Optional[Mapping[str, Any]] = None,
        proposed_at: str = "",
        source_runtime_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        restore = self._restore_data(restore_data)
        latest_runtime = restore.get("latest_runtime")
        latest_dashboard = restore.get("latest_dashboard")
        recent_events = list(restore.get("recent_events", []) or [])

        plan = self._build_plan(latest_runtime, latest_dashboard, recent_events)
        evidence = {
            "restorable": bool(restore.get("restorable", False)),
            "latest_runtime": latest_runtime or {},
            "latest_dashboard": latest_dashboard or {},
            "recent_events": recent_events,
        }
        proposal = self._recovery_proposal(
            plan=plan,
            evidence=evidence,
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            operation="recovery_plan",
        )

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "persisted": False,
            "restorable": bool(restore.get("restorable", False)),
            "latest_runtime": latest_runtime,
            "latest_dashboard": latest_dashboard,
            "recent_events": recent_events,
            "recovery_plan": plan,
            "proposal": proposal,
            "explanation": "Recovery plan proposal generated from caller-supplied restore data; nothing was persisted.",
        }

    def recover_summary(
        self,
        recovery_info: Optional[Mapping[str, Any]] = None,
        proposed_at: str = "",
        source_runtime_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        plan_result = self._plan_result(recovery_info, proposed_at, source_runtime_id)
        runtime_payload = ((plan_result.get("latest_runtime") or {}).get("payload") or {})
        dashboard_payload = ((plan_result.get("latest_dashboard") or {}).get("payload") or {})
        plan = plan_result.get("recovery_plan", {})

        return {
            "status": "ok",
            "read_only": True,
            "persisted": False,
            "restorable": plan_result.get("restorable"),
            "recommended_action": plan.get("recommended_action"),
            "runtime_status": runtime_payload.get("runtime_status") or runtime_payload.get("status"),
            "health": runtime_payload.get("health"),
            "cycles": runtime_payload.get("cycles"),
            "last_cycle": dashboard_payload.get("last_cycle", {}),
            "warnings": plan.get("warnings", []),
            "proposal": plan_result.get("proposal"),
            "explanation": "Recovery summary derived without persistence access.",
        }

    def log_recovery_attempt(
        self,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        proposed_at: str = "",
        source_runtime_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "success": bool(success),
            "attempt_details": details or {},
        }
        proposal = OracleEventPersistenceProposal(
            oracle_module_id=self.module_name,
            event_type="recovery_attempt",
            severity="info" if success else "warning",
            payload=payload,
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            replay_metadata=self._replay_metadata("recovery_attempt_event"),
        )
        proposal.validate()
        return {
            "status": "ok",
            "read_only": True,
            "persisted": False,
            "event_type": "recovery_attempt",
            "success": bool(success),
            "proposal": proposal,
            "explanation": "Recovery attempt event proposal generated for Q Series authorization; nothing was logged or persisted.",
        }

    def _restore_data(self, restore_data: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        if restore_data is not None:
            return dict(restore_data)
        if self.restore_data_provider is not None:
            return dict(self.restore_data_provider() or {})
        return {"restorable": False, "latest_runtime": None, "latest_dashboard": None, "recent_events": []}

    def _plan_result(
        self,
        recovery_info: Optional[Mapping[str, Any]],
        proposed_at: str,
        source_runtime_id: Optional[str],
    ) -> Dict[str, Any]:
        if recovery_info and "recovery_plan" in recovery_info:
            return dict(recovery_info)
        return self.recovery_plan(
            restore_data=recovery_info,
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
        )

    def _recovery_proposal(
        self,
        *,
        plan: Mapping[str, Any],
        evidence: Mapping[str, Any],
        proposed_at: str,
        source_runtime_id: Optional[str],
        operation: str,
    ) -> OracleRecoveryPersistenceProposal:
        proposal = OracleRecoveryPersistenceProposal(
            oracle_module_id=self.module_name,
            recovery_action=str(plan.get("recommended_action") or "cold_start"),
            safe_to_resume=bool(plan.get("safe_to_resume", True)),
            warnings=tuple(str(item) for item in plan.get("warnings", []) or ()),
            steps=tuple(str(item) for item in plan.get("steps", []) or ()),
            payload={
                "recommended_action": plan.get("recommended_action"),
                "safe_to_resume": bool(plan.get("safe_to_resume", True)),
                "warning_count": len(plan.get("warnings", []) or ()),
                "step_count": len(plan.get("steps", []) or ()),
            },
            evidence=evidence,
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            replay_metadata=self._replay_metadata(operation),
        )
        proposal.validate()
        return proposal

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
                "warnings": ["no_recovery_state_found"],
                "steps": [
                    "Prepare Oracle runtime from clean state.",
                    "Run discovery cycle proposal.",
                    "Rebuild active research from read-only market cache view.",
                ],
            }

        runtime_payload = (latest_runtime or {}).get("payload", {})
        dashboard_payload = (latest_dashboard or {}).get("payload", {})

        health = runtime_payload.get("health")
        runtime_status = runtime_payload.get("runtime_status") or runtime_payload.get("status")

        if health and health != "healthy":
            warnings.append("last_health_not_healthy")

        if runtime_payload.get("metrics", {}).get("errors", 0) > 0:
            warnings.append("errors_present_before_shutdown")

        last_event_type = recent_events[0]["event_type"] if recent_events else None

        if last_event_type not in {"runtime_stopped", "runtime_state_proposed", "runtime_cycle_completed"}:
            warnings.append("last_event_not_clean_shutdown")

        if runtime_status == "running" and last_event_type != "runtime_stopped":
            steps.append("Previous status looked running; require validation before continuous loop.")

        steps.extend([
            "Review latest status snapshot supplied by Q Series.",
            "Review latest command center dashboard supplied by Q Series.",
            "Preserve telemetry counters for reporting.",
            "Propose restart in read-only research mode.",
            "Run one validation cycle before continuous loop.",
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

    def _replay_metadata(self, operation: str) -> Dict[str, Any]:
        return {
            "schema_version": "ORP-001",
            "operation": operation,
            "qseries_authorization_required": True,
            "boundary": "oracle_to_qseries_proposal",
        }


runtime_recovery_manager = RuntimeRecoveryManager()
