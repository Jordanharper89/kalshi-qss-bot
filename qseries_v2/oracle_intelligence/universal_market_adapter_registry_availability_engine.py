
"""
OI-182 — Oracle Universal Market Adapter Registry Availability Engine

Read-only availability layer for validated Universal Market Adapter registry
records.

This module determines whether validated registry records are available for
Oracle intelligence lookup. Availability is descriptive only. It does not
activate execution, route orders, submit orders, manage positions, or trade.

Oracle remains intelligence-only.
Q Series remains the sole execution owner.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


ENGINE_ID = "oi.182.universal_market_adapter_registry_availability"
ENGINE_NAME = "Oracle Universal Market Adapter Registry Availability Engine"
ENGINE_VERSION = "1.0.0"
ARCHITECTURE_ROLE = "read_only_adapter_registry_availability"
Q_SERIES_EXECUTION_OWNER = "qseries.execution"

READ_ONLY_GUARDRAILS = (
    "Oracle never executes trades.",
    "Oracle never manages positions.",
    "Oracle never submits orders.",
    "Oracle never routes orders.",
    "Oracle never signs transactions.",
    "Oracle never custody-controls assets.",
    "Q Series is the only execution engine.",
)

AVAILABILITY_GATES = (
    "read_only_boundary_available",
    "q_series_execution_boundary_available",
    "validation_status_available",
    "registry_identity_available",
    "lookup_namespace_available",
    "market_type_available",
    "availability_mode_available",
    "validation_hash_available",
    "replay_hash_available",
    "telemetry_available",
)


@dataclass(frozen=True)
class AdapterRegistryAvailabilityRecord:
    registry_id: str
    candidate_id: str
    name: str
    market_type: str
    source_kind: str
    registry_namespace: str
    registry_version: str
    registry_owner: str
    validation_status: str
    validation_score: float
    validation_hash: str
    replay_hash: str
    availability_mode: str = "lookup_only"
    telemetry_ready: bool = True
    enabled_for_lookup: bool = True
    read_only: bool = True
    execution_owner: str = Q_SERIES_EXECUTION_OWNER
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def normalized(self) -> Dict[str, Any]:
        return {
            "registry_id": str(self.registry_id),
            "candidate_id": str(self.candidate_id),
            "name": str(self.name),
            "market_type": normalize_market_type(self.market_type),
            "source_kind": str(self.source_kind),
            "registry_namespace": str(self.registry_namespace),
            "registry_version": str(self.registry_version),
            "registry_owner": str(self.registry_owner),
            "validation_status": str(self.validation_status),
            "validation_score": clamp(self.validation_score),
            "validation_hash": str(self.validation_hash),
            "replay_hash": str(self.replay_hash),
            "availability_mode": str(self.availability_mode or "lookup_only").strip().lower(),
            "telemetry_ready": bool(self.telemetry_ready),
            "enabled_for_lookup": bool(self.enabled_for_lookup),
            "read_only": bool(self.read_only),
            "execution_owner": str(self.execution_owner),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AdapterRegistryAvailabilityDecision:
    record: AdapterRegistryAvailabilityRecord
    available: bool
    availability_status: str
    availability_score: float
    gates: Mapping[str, bool]
    blockers: Tuple[str, ...]
    warnings: Tuple[str, ...]
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    availability_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record": self.record.normalized(),
            "available": self.available,
            "availability_status": self.availability_status,
            "availability_score": self.availability_score,
            "gates": dict(self.gates),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "availability_hash": self.availability_hash,
        }


@dataclass(frozen=True)
class AdapterRegistryAvailabilitySnapshot:
    engine_id: str
    engine_name: str
    engine_version: str
    created_at: float
    decision_count: int
    available_count: int
    decisions: Tuple[AdapterRegistryAvailabilityDecision, ...]
    lookup_index: Mapping[str, str]
    architecture: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "decision_count": self.decision_count,
            "available_count": self.available_count,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "lookup_index": dict(self.lookup_index),
            "architecture": dict(self.architecture),
            "replay_hash": self.replay_hash,
        }


def normalize_market_type(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def clamp(value: Any) -> float:
    try:
        number = float(value)
    except Exception:
        number = 0.0
    return round(max(0.0, min(1.0, number)), 6)


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def architecture_contract() -> Dict[str, Any]:
    return {
        "oracle_mode": "read_only",
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "universal_market_model": True,
        "single_oracle_instance": True,
        "adapter_based_expansion": True,
        "event_driven_intelligence": True,
        "explainability_by_default": True,
        "replayability_by_default": True,
        "historical_memory_ready": True,
        "institutional_telemetry": True,
        "strategy_agnostic_q_series": True,
        "architecture_registry_ready": True,
        "adapter_registry_availability_ready": True,
        "guardrails": list(READ_ONLY_GUARDRAILS),
    }


def build_availability_gates(record: AdapterRegistryAvailabilityRecord) -> Dict[str, bool]:
    data = record.normalized()
    return {
        "read_only_boundary_available": data["read_only"] is True,
        "q_series_execution_boundary_available": data["execution_owner"] == Q_SERIES_EXECUTION_OWNER,
        "validation_status_available": (
            data["validation_status"] in {
                "validated_registry_available",
                "validated_with_conditions",
                "available",
            }
            and data["validation_score"] >= 0.76
        ),
        "registry_identity_available": bool(data["registry_id"]) and ".v" in data["registry_id"],
        "lookup_namespace_available": data["registry_namespace"].startswith("oracle.adapters."),
        "market_type_available": bool(data["market_type"]) and data["market_type"] != "unknown",
        "availability_mode_available": data["availability_mode"] in {"lookup_only", "read_only_lookup", "oracle_lookup"},
        "validation_hash_available": bool(data["validation_hash"]) and len(data["validation_hash"]) >= 16,
        "replay_hash_available": bool(data["replay_hash"]) and len(data["replay_hash"]) >= 8,
        "telemetry_available": data["telemetry_ready"] is True and data["enabled_for_lookup"] is True,
    }


def availability_score(record: AdapterRegistryAvailabilityRecord, gates: Mapping[str, bool]) -> float:
    data = record.normalized()
    gate_ratio = sum(1 for value in gates.values() if value) / len(gates)
    score = data["validation_score"] * 0.50 + gate_ratio * 0.50
    return round(max(0.0, min(1.0, score)), 6)


def availability_status(score: float, gates: Mapping[str, bool]) -> str:
    core = (
        gates.get("read_only_boundary_available", False),
        gates.get("q_series_execution_boundary_available", False),
        gates.get("validation_status_available", False),
        gates.get("registry_identity_available", False),
        gates.get("lookup_namespace_available", False),
        gates.get("market_type_available", False),
    )

    if all(gates.values()) and score >= 0.88:
        return "available_for_oracle_lookup"
    if all(core) and score >= 0.76:
        return "available_with_conditions"
    if gates.get("read_only_boundary_available", False) and score >= 0.55:
        return "availability_research_required"
    return "not_available"


def recommend_next_step(status: str) -> str:
    if status == "available_for_oracle_lookup":
        return "Expose record to Oracle lookup and routing intelligence indexes without enabling execution."
    if status == "available_with_conditions":
        return "Expose conditionally after resolving non-core availability warnings."
    if status == "availability_research_required":
        return "Collect missing validation hash, replay hash, telemetry, or lookup availability evidence."
    return "Do not expose to lookup. Core availability gates failed."


def lookup_key(record: AdapterRegistryAvailabilityRecord) -> str:
    data = record.normalized()
    return f"{data['market_type']}::{data['registry_namespace']}::{data['registry_id']}"


def evaluate_availability(
    record: AdapterRegistryAvailabilityRecord,
    evaluated_at: Optional[float] = None,
) -> AdapterRegistryAvailabilityDecision:
    timestamp = float(evaluated_at if evaluated_at is not None else time.time())
    gates = build_availability_gates(record)
    score = availability_score(record, gates)
    status = availability_status(score, gates)
    available = status in {"available_for_oracle_lookup", "available_with_conditions"}

    core_names = {
        "read_only_boundary_available",
        "q_series_execution_boundary_available",
        "validation_status_available",
        "registry_identity_available",
        "lookup_namespace_available",
        "market_type_available",
    }

    blockers = tuple(name for name, passed in gates.items() if not passed and name in core_names)
    warnings = tuple(name for name, passed in gates.items() if not passed and name not in core_names)

    explanation = {
        "summary": f"{record.name} received availability status {status} with score {score:.3f}.",
        "available": available,
        "market_type": normalize_market_type(record.market_type),
        "source_kind": record.source_kind,
        "lookup_key": lookup_key(record),
        "passed_gates": [name for name, passed in gates.items() if passed],
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "blockers": list(blockers),
        "warnings": list(warnings),
        "read_only_statement": "Availability is descriptive only and cannot execute, route, submit, or manage trades.",
        "q_series_boundary": "Q Series remains the sole execution owner.",
        "registry_boundary": "Availability permits Oracle lookup only; it does not activate execution.",
        "next_step": recommend_next_step(status),
    }

    telemetry = {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "architecture_role": ARCHITECTURE_ROLE,
        "registry_id": record.registry_id,
        "candidate_id": record.candidate_id,
        "market_type": normalize_market_type(record.market_type),
        "availability_status": status,
        "available": available,
        "availability_score": score,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "lookup_key": lookup_key(record),
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "evaluated_at": timestamp,
    }

    availability_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "record": record.normalized(),
        "gates": dict(gates),
        "score": score,
        "status": status,
        "available": available,
        "blockers": blockers,
        "warnings": warnings,
    })

    return AdapterRegistryAvailabilityDecision(
        record=record,
        available=available,
        availability_status=status,
        availability_score=score,
        gates=gates,
        blockers=blockers,
        warnings=warnings,
        explanation=explanation,
        telemetry=telemetry,
        availability_hash=availability_hash,
    )


def evaluate_records(
    records: Iterable[AdapterRegistryAvailabilityRecord],
    evaluated_at: Optional[float] = None,
) -> AdapterRegistryAvailabilitySnapshot:
    timestamp = float(evaluated_at if evaluated_at is not None else time.time())
    decisions = tuple(
        sorted(
            (evaluate_availability(record, evaluated_at=timestamp) for record in records),
            key=lambda decision: (-decision.availability_score, decision.record.name.lower(), decision.record.registry_id),
        )
    )

    lookup_index = {
        lookup_key(decision.record): decision.record.registry_id
        for decision in decisions
        if decision.available
    }

    architecture = architecture_contract()
    replay_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "created_at": timestamp,
        "decision_hashes": [decision.availability_hash for decision in decisions],
        "lookup_index": lookup_index,
        "architecture": architecture,
    })

    return AdapterRegistryAvailabilitySnapshot(
        engine_id=ENGINE_ID,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        created_at=timestamp,
        decision_count=len(decisions),
        available_count=sum(1 for decision in decisions if decision.available),
        decisions=decisions,
        lookup_index=lookup_index,
        architecture=architecture,
        replay_hash=replay_hash,
    )


def record_from_validation_decision(decision: Mapping[str, Any]) -> AdapterRegistryAvailabilityRecord:
    record = decision.get("record", {})
    telemetry = decision.get("telemetry", {})

    return AdapterRegistryAvailabilityRecord(
        registry_id=str(record.get("registry_id", telemetry.get("registry_id", ""))),
        candidate_id=str(record.get("candidate_id", telemetry.get("candidate_id", ""))),
        name=str(record.get("name", "")),
        market_type=str(record.get("market_type", telemetry.get("market_type", "unknown"))),
        source_kind=str(record.get("source_kind", "unknown")),
        registry_namespace=str(record.get("registry_namespace", "")),
        registry_version=str(record.get("registry_version", "")),
        registry_owner=str(record.get("registry_owner", "")),
        validation_status=str(decision.get("validation_status", telemetry.get("validation_status", ""))),
        validation_score=clamp(decision.get("validation_score", telemetry.get("validation_score", 0.0))),
        validation_hash=str(decision.get("validation_hash", "")),
        replay_hash=str(record.get("replay_hash", "")),
        availability_mode="lookup_only",
        telemetry_ready=bool(decision.get("telemetry")),
        enabled_for_lookup=bool(decision.get("valid", telemetry.get("valid", False))),
        read_only=bool(telemetry.get("read_only", record.get("read_only", True))),
        execution_owner=str(telemetry.get("execution_owner", record.get("execution_owner", Q_SERIES_EXECUTION_OWNER))),
        metadata=record.get("metadata", {}),
    )


def evaluate_validation_snapshot(snapshot: Mapping[str, Any]) -> AdapterRegistryAvailabilitySnapshot:
    records = [
        record_from_validation_decision(decision)
        for decision in snapshot.get("decisions", [])
    ]
    return evaluate_records(records, evaluated_at=float(snapshot.get("created_at", time.time())))


def snapshot_to_json(snapshot: AdapterRegistryAvailabilitySnapshot, indent: int = 2) -> str:
    return json.dumps(snapshot.to_dict(), indent=indent, sort_keys=True, default=str)


class UniversalMarketAdapterRegistryAvailabilityEngine:
    def __init__(self) -> None:
        self._history = []

    def evaluate(
        self,
        records: Iterable[AdapterRegistryAvailabilityRecord],
        evaluated_at: Optional[float] = None,
    ) -> AdapterRegistryAvailabilitySnapshot:
        snapshot = evaluate_records(records, evaluated_at=evaluated_at)
        self._history.append(snapshot)
        return snapshot

    def evaluate_validation_snapshot(self, snapshot: Mapping[str, Any]) -> AdapterRegistryAvailabilitySnapshot:
        evaluated = evaluate_validation_snapshot(snapshot)
        self._history.append(evaluated)
        return evaluated

    def latest_snapshot(self) -> Optional[AdapterRegistryAvailabilitySnapshot]:
        return self._history[-1] if self._history else None

    def history(self) -> Tuple[AdapterRegistryAvailabilitySnapshot, ...]:
        return tuple(self._history)

    def diagnostics(self) -> Dict[str, Any]:
        latest = self.latest_snapshot()
        return {
            "engine_id": ENGINE_ID,
            "engine_name": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "architecture_role": ARCHITECTURE_ROLE,
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
            "history_count": len(self._history),
            "latest_replay_hash": latest.replay_hash if latest else None,
            "latest_decision_count": latest.decision_count if latest else 0,
            "latest_available_count": latest.available_count if latest else 0,
            "guardrails": list(READ_ONLY_GUARDRAILS),
        }


oracle_universal_market_adapter_registry_availability_engine = UniversalMarketAdapterRegistryAvailabilityEngine()
universal_market_adapter_registry_availability_engine = oracle_universal_market_adapter_registry_availability_engine


def demo_records() -> Tuple[AdapterRegistryAvailabilityRecord, ...]:
    return (
        AdapterRegistryAvailabilityRecord(
            registry_id="oracle.adapters.prediction_markets.prediction_markets.demo.prediction.v1.0.0",
            candidate_id="demo.prediction",
            name="Demo Prediction Available Registry Record",
            market_type="prediction_markets",
            source_kind="api_schema",
            registry_namespace="oracle.adapters.prediction_markets",
            registry_version="1.0.0",
            registry_owner="oracle_intelligence",
            validation_status="validated_registry_available",
            validation_score=0.99,
            validation_hash="demo-validation-hash-123456789",
            replay_hash="demo-replay-hash",
            availability_mode="lookup_only",
            telemetry_ready=True,
            enabled_for_lookup=True,
        ),
        AdapterRegistryAvailabilityRecord(
            registry_id="",
            candidate_id="demo.crypto",
            name="Demo Crypto Unavailable Registry Record",
            market_type="crypto",
            source_kind="vendor_export",
            registry_namespace="",
            registry_version="",
            registry_owner="",
            validation_status="not_validated",
            validation_score=0.15,
            validation_hash="",
            replay_hash="",
            telemetry_ready=False,
            enabled_for_lookup=False,
        ),
    )


if __name__ == "__main__":
    snapshot = evaluate_records(demo_records(), evaluated_at=1760000000.0)
    print(snapshot_to_json(snapshot))
