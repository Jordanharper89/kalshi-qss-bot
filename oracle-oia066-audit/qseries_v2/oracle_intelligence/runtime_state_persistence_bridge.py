"""
OI-070 Runtime State Persistence Bridge

Purpose:
- Connect OI-068 Command Center to ORP-001 persistence proposals.
- Produce immutable Oracle-to-Q-Series persistence proposals.
- Leave authorization and persistence ownership to Q Series.

Read-only:
- No execution ownership.
- No order placement.
- No trade mutation.
- No filesystem, SQLite, or runtime-state writes.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .oracle_intelligence_command_center import (
    oracle_intelligence_command_center,
    OracleIntelligenceCommandCenter,
)
from .persistence_proposal_contract import (
    OracleEventPersistenceProposal,
    OracleSnapshotPersistenceProposal,
)


class RuntimeStatePersistenceBridge:
    module_name = "oi_070_runtime_state_persistence_bridge"

    def __init__(
        self,
        command_center: Optional[OracleIntelligenceCommandCenter] = None,
    ) -> None:
        self.command_center = command_center or oracle_intelligence_command_center

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "persisted": False,
            "command_center": self._safe_status(self.command_center),
            "boundary": "oracle_proposal_only",
        }

    def persist_status(self, proposed_at: str, source_runtime_id: Optional[str] = None) -> Dict[str, Any]:
        runtime_status = self.command_center.status()
        proposal = self._snapshot_proposal(
            snapshot_type="runtime_status",
            payload={"runtime_status": runtime_status},
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            operation="runtime_status_snapshot",
        )
        return self._proposal_response(proposal, "Runtime status proposal generated for Q Series authorization.")

    def persist_dashboard(self, proposed_at: str, source_runtime_id: Optional[str] = None) -> Dict[str, Any]:
        dashboard = self.command_center.dashboard()
        proposal = self._snapshot_proposal(
            snapshot_type="command_center_dashboard",
            payload={"dashboard": dashboard},
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            operation="dashboard_snapshot",
        )
        return self._proposal_response(proposal, "Command center dashboard proposal generated for Q Series authorization.")

    def persist_full_state(self, proposed_at: str, source_runtime_id: Optional[str] = None) -> Dict[str, Any]:
        runtime_status = self.command_center.status()
        dashboard = self.command_center.dashboard()
        proposal = self._snapshot_proposal(
            snapshot_type="runtime_full_state",
            payload={
                "runtime_status": runtime_status,
                "dashboard": dashboard,
            },
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            operation="full_state_snapshot",
        )
        return self._proposal_response(proposal, "Full runtime state proposal generated for Q Series authorization.")

    def run_once_and_persist(
        self,
        markets=None,
        proposed_at: str = "",
        source_runtime_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        run = self.command_center.run_once(markets=markets or [], **kwargs)
        dashboard = self.command_center.dashboard()
        proposal = self._snapshot_proposal(
            snapshot_type="runtime_cycle_result",
            payload={
                "run": run,
                "dashboard": dashboard,
            },
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            operation="runtime_cycle_snapshot",
        )
        response = self._proposal_response(proposal, "Runtime cycle proposal generated for Q Series authorization.")
        response["status"] = run.get("status", response["status"])
        return response

    def start_and_log(self, proposed_at: str, source_runtime_id: Optional[str] = None) -> Dict[str, Any]:
        started = self.command_center.start_runtime()
        proposal = self._event_proposal(
            event_type="runtime_started",
            severity="info" if started.get("status") == "ok" else "warning",
            payload={"start_result": started},
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            operation="runtime_start_event",
        )
        return self._proposal_response(proposal, "Runtime start event proposal generated for Q Series authorization.")

    def stop_and_log(self, proposed_at: str, source_runtime_id: Optional[str] = None) -> Dict[str, Any]:
        stopped = self.command_center.stop_runtime()
        proposal = self._event_proposal(
            event_type="runtime_stopped",
            severity="info" if stopped.get("status") == "ok" else "warning",
            payload={"stop_result": stopped},
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            operation="runtime_stop_event",
        )
        return self._proposal_response(proposal, "Runtime stop event proposal generated for Q Series authorization.")

    def restore_summary(self, restore_data: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        if restore_data is None:
            return {
                "status": "unavailable",
                "read_only": True,
                "persisted": False,
                "restorable": False,
                "restore": None,
                "explanation": "No caller-supplied restore data was provided; Q Series owns restore state access.",
            }

        restore = dict(restore_data)
        return {
            "status": "ok",
            "read_only": True,
            "persisted": False,
            "restorable": bool(restore.get("restorable")),
            "restore": restore,
            "explanation": "Caller-supplied restore data summarized without accessing a store.",
        }

    def _snapshot_proposal(
        self,
        *,
        snapshot_type: str,
        payload: Dict[str, Any],
        proposed_at: str,
        source_runtime_id: Optional[str],
        operation: str,
    ) -> OracleSnapshotPersistenceProposal:
        proposal = OracleSnapshotPersistenceProposal(
            oracle_module_id=self.module_name,
            snapshot_type=snapshot_type,
            payload=self._contract_payload(payload),
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            replay_metadata=self._replay_metadata(operation),
        )
        proposal.validate()
        return proposal

    def _event_proposal(
        self,
        *,
        event_type: str,
        severity: str,
        payload: Dict[str, Any],
        proposed_at: str,
        source_runtime_id: Optional[str],
        operation: str,
    ) -> OracleEventPersistenceProposal:
        proposal = OracleEventPersistenceProposal(
            oracle_module_id=self.module_name,
            event_type=event_type,
            severity=severity,
            payload=self._contract_payload(payload),
            proposed_at=proposed_at,
            source_runtime_id=source_runtime_id,
            replay_metadata=self._replay_metadata(operation),
        )
        proposal.validate()
        return proposal


    def _contract_payload(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            normalized: Dict[str, Any] = {}
            for key, item in value.items():
                clean_key = "oracle_runtime" if str(key) == "runtime" else str(key)
                normalized[clean_key] = self._contract_payload(item)
            return normalized
        if isinstance(value, list):
            return [self._contract_payload(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._contract_payload(item) for item in value)
        return value
    def _replay_metadata(self, operation: str) -> Dict[str, Any]:
        return {
            "schema_version": "ORP-001",
            "operation": operation,
            "qseries_authorization_required": True,
            "boundary": "oracle_to_qseries_proposal",
        }

    def _proposal_response(self, proposal: Any, explanation: str) -> Dict[str, Any]:
        return {
            "status": "ok",
            "read_only": True,
            "persisted": False,
            "proposal": proposal,
            "explanation": explanation,
        }

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"


runtime_state_persistence_bridge = RuntimeStatePersistenceBridge()
