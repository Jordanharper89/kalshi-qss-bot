
"""
OI-181 — Oracle Universal Market Adapter Registry Validation Engine

Read-only validation layer for enrolled Universal Market Adapter registry
records.

This module validates registry enrollment records before they are considered
available to downstream Oracle intelligence workflows. It does not activate
execution, submit orders, route trades, or manage positions.

Oracle remains intelligence-only.
Q Series remains the sole execution owner.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


ENGINE_ID = "oi.181.universal_market_adapter_registry_validation"
ENGINE_NAME = "Oracle Universal Market Adapter Registry Validation Engine"
ENGINE_VERSION = "1.0.0"
ARCHITECTURE_ROLE = "read_only_adapter_registry_validation"
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

VALIDATION_GATES = (
    "read_only_boundary_validated",
    "q_series_execution_boundary_validated",
    "registry_id_validated",
    "namespace_validated",
    "version_validated",
    "owner_validated",
    "market_type_validated",
    "enrollment_status_validated",
    "enrollment_hash_validated",
    "replay_hash_validated",
)


@dataclass(frozen=True)
class AdapterRegistryValidationRecord:
    registry_id: str
    candidate_id: str
    name: str
    market_type: str
    source_kind: str
    registry_namespace: str
    registry_version: str
    registry_owner: str
    enrollment_status: str
    enrollment_score: float
    promotion_hash: str
    replay_hash: str
    enrollment_hash: str
    enrolled_at: float
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
            "enrollment_status": str(self.enrollment_status),
            "enrollment_score": clamp(self.enrollment_score),
            "promotion_hash": str(self.promotion_hash),
            "replay_hash": str(self.replay_hash),
            "enrollment_hash": str(self.enrollment_hash),
            "enrolled_at": float(self.enrolled_at),
            "read_only": bool(self.read_only),
            "execution_owner": str(self.execution_owner),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AdapterRegistryValidationDecision:
    record: AdapterRegistryValidationRecord
    valid: bool
    validation_status: str
    validation_score: float
    gates: Mapping[str, bool]
    blockers: Tuple[str, ...]
    warnings: Tuple[str, ...]
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    validation_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record": self.record.normalized(),
            "valid": self.valid,
            "validation_status": self.validation_status,
            "validation_score": self.validation_score,
            "gates": dict(self.gates),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "validation_hash": self.validation_hash,
        }


@dataclass(frozen=True)
class AdapterRegistryValidationSnapshot:
    engine_id: str
    engine_name: str
    engine_version: str
    created_at: float
    decision_count: int
    valid_count: int
    decisions: Tuple[AdapterRegistryValidationDecision, ...]
    architecture: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "decision_count": self.decision_count,
            "valid_count": self.valid_count,
            "decisions": [decision.to_dict() for decision in self.decisions],
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
        "adapter_registry_validation_ready": True,
        "guardrails": list(READ_ONLY_GUARDRAILS),
    }


def build_validation_gates(record: AdapterRegistryValidationRecord) -> Dict[str, bool]:
    data = record.normalized()
    return {
        "read_only_boundary_validated": data["read_only"] is True,
        "q_series_execution_boundary_validated": data["execution_owner"] == Q_SERIES_EXECUTION_OWNER,
        "registry_id_validated": bool(data["registry_id"]) and ".v" in data["registry_id"],
        "namespace_validated": data["registry_namespace"].startswith("oracle.adapters."),
        "version_validated": bool(data["registry_version"]) and data["registry_version"].count(".") >= 2,
        "owner_validated": bool(data["registry_owner"]),
        "market_type_validated": bool(data["market_type"]) and data["market_type"] != "unknown",
        "enrollment_status_validated": data["enrollment_status"] in {
            "enrolled_registry_ready",
            "enrolled_with_conditions",
            "validated",
        },
        "enrollment_hash_validated": bool(data["enrollment_hash"]) and len(data["enrollment_hash"]) >= 16,
        "replay_hash_validated": bool(data["replay_hash"]) and len(data["replay_hash"]) >= 8,
    }


def validation_score(record: AdapterRegistryValidationRecord, gates: Mapping[str, bool]) -> float:
    data = record.normalized()
    gate_ratio = sum(1 for value in gates.values() if value) / len(gates)
    score = data["enrollment_score"] * 0.50 + gate_ratio * 0.50
    return round(max(0.0, min(1.0, score)), 6)


def validation_status(score: float, gates: Mapping[str, bool]) -> str:
    core = (
        gates.get("read_only_boundary_validated", False),
        gates.get("q_series_execution_boundary_validated", False),
        gates.get("registry_id_validated", False),
        gates.get("namespace_validated", False),
        gates.get("version_validated", False),
        gates.get("owner_validated", False),
    )

    if all(gates.values()) and score >= 0.88:
        return "validated_registry_available"
    if all(core) and score >= 0.76:
        return "validated_with_conditions"
    if gates.get("read_only_boundary_validated", False) and score >= 0.55:
        return "validation_research_required"
    return "not_validated"


def recommend_next_step(status: str) -> str:
    if status == "validated_registry_available":
        return "Mark registry record available for Oracle intelligence routing lookup."
    if status == "validated_with_conditions":
        return "Resolve conditional validation gaps before broad routing availability."
    if status == "validation_research_required":
        return "Collect missing identity, namespace, hash, replay, or enrollment evidence."
    return "Do not validate. Core registry validation gates failed."


def validate_record(
    record: AdapterRegistryValidationRecord,
    validated_at: Optional[float] = None,
) -> AdapterRegistryValidationDecision:
    timestamp = float(validated_at if validated_at is not None else time.time())
    gates = build_validation_gates(record)
    score = validation_score(record, gates)
    status = validation_status(score, gates)
    valid = status in {"validated_registry_available", "validated_with_conditions"}

    core_names = {
        "read_only_boundary_validated",
        "q_series_execution_boundary_validated",
        "registry_id_validated",
        "namespace_validated",
        "version_validated",
        "owner_validated",
    }

    blockers = tuple(name for name, passed in gates.items() if not passed and name in core_names)
    warnings = tuple(name for name, passed in gates.items() if not passed and name not in core_names)

    explanation = {
        "summary": f"{record.name} received validation status {status} with score {score:.3f}.",
        "valid": valid,
        "market_type": normalize_market_type(record.market_type),
        "source_kind": record.source_kind,
        "passed_gates": [name for name, passed in gates.items() if passed],
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "blockers": list(blockers),
        "warnings": list(warnings),
        "read_only_statement": "Validation is descriptive only and cannot execute, route, submit, or manage trades.",
        "q_series_boundary": "Q Series remains the sole execution owner.",
        "registry_boundary": "Validation marks Oracle registry availability only; it does not activate execution.",
        "next_step": recommend_next_step(status),
    }

    telemetry = {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "architecture_role": ARCHITECTURE_ROLE,
        "registry_id": record.registry_id,
        "candidate_id": record.candidate_id,
        "market_type": normalize_market_type(record.market_type),
        "validation_status": status,
        "valid": valid,
        "validation_score": score,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "validated_at": timestamp,
    }

    validation_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "record": record.normalized(),
        "gates": dict(gates),
        "score": score,
        "status": status,
        "valid": valid,
        "blockers": blockers,
        "warnings": warnings,
    })

    return AdapterRegistryValidationDecision(
        record=record,
        valid=valid,
        validation_status=status,
        validation_score=score,
        gates=gates,
        blockers=blockers,
        warnings=warnings,
        explanation=explanation,
        telemetry=telemetry,
        validation_hash=validation_hash,
    )


def validate_records(
    records: Iterable[AdapterRegistryValidationRecord],
    validated_at: Optional[float] = None,
) -> AdapterRegistryValidationSnapshot:
    timestamp = float(validated_at if validated_at is not None else time.time())
    decisions = tuple(
        sorted(
            (validate_record(record, validated_at=timestamp) for record in records),
            key=lambda decision: (-decision.validation_score, decision.record.name.lower(), decision.record.registry_id),
        )
    )

    architecture = architecture_contract()
    replay_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "created_at": timestamp,
        "decision_hashes": [decision.validation_hash for decision in decisions],
        "architecture": architecture,
    })

    return AdapterRegistryValidationSnapshot(
        engine_id=ENGINE_ID,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        created_at=timestamp,
        decision_count=len(decisions),
        valid_count=sum(1 for decision in decisions if decision.valid),
        decisions=decisions,
        architecture=architecture,
        replay_hash=replay_hash,
    )


def record_from_enrollment_record(record: Mapping[str, Any]) -> AdapterRegistryValidationRecord:
    return AdapterRegistryValidationRecord(
        registry_id=str(record.get("registry_id", "")),
        candidate_id=str(record.get("candidate_id", "")),
        name=str(record.get("name", "")),
        market_type=str(record.get("market_type", "unknown")),
        source_kind=str(record.get("source_kind", "unknown")),
        registry_namespace=str(record.get("registry_namespace", "")),
        registry_version=str(record.get("registry_version", "")),
        registry_owner=str(record.get("registry_owner", "")),
        enrollment_status=str(record.get("enrollment_status", "")),
        enrollment_score=clamp(record.get("enrollment_score", 0.0)),
        promotion_hash=str(record.get("promotion_hash", "")),
        replay_hash=str(record.get("replay_hash", "")),
        enrollment_hash=str(record.get("enrollment_hash", "")),
        enrolled_at=float(record.get("enrolled_at", 0.0)),
        read_only=bool(record.get("read_only", True)),
        execution_owner=str(record.get("execution_owner", Q_SERIES_EXECUTION_OWNER)),
        metadata=record.get("metadata", {}),
    )


def validate_enrollment_snapshot(snapshot: Mapping[str, Any]) -> AdapterRegistryValidationSnapshot:
    records = [record_from_enrollment_record(record) for record in snapshot.get("records", [])]
    return validate_records(records, validated_at=float(snapshot.get("created_at", time.time())))


def snapshot_to_json(snapshot: AdapterRegistryValidationSnapshot, indent: int = 2) -> str:
    return json.dumps(snapshot.to_dict(), indent=indent, sort_keys=True, default=str)


class UniversalMarketAdapterRegistryValidationEngine:
    def __init__(self) -> None:
        self._history = []

    def validate(
        self,
        records: Iterable[AdapterRegistryValidationRecord],
        validated_at: Optional[float] = None,
    ) -> AdapterRegistryValidationSnapshot:
        snapshot = validate_records(records, validated_at=validated_at)
        self._history.append(snapshot)
        return snapshot

    def validate_enrollment_snapshot(self, snapshot: Mapping[str, Any]) -> AdapterRegistryValidationSnapshot:
        validated = validate_enrollment_snapshot(snapshot)
        self._history.append(validated)
        return validated

    def latest_snapshot(self) -> Optional[AdapterRegistryValidationSnapshot]:
        return self._history[-1] if self._history else None

    def history(self) -> Tuple[AdapterRegistryValidationSnapshot, ...]:
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
            "latest_valid_count": latest.valid_count if latest else 0,
            "guardrails": list(READ_ONLY_GUARDRAILS),
        }


oracle_universal_market_adapter_registry_validation_engine = UniversalMarketAdapterRegistryValidationEngine()
universal_market_adapter_registry_validation_engine = oracle_universal_market_adapter_registry_validation_engine


def demo_records() -> Tuple[AdapterRegistryValidationRecord, ...]:
    return (
        AdapterRegistryValidationRecord(
            registry_id="oracle.adapters.prediction_markets.prediction_markets.demo.prediction.v1.0.0",
            candidate_id="demo.prediction",
            name="Demo Prediction Registry Record",
            market_type="prediction_markets",
            source_kind="api_schema",
            registry_namespace="oracle.adapters.prediction_markets",
            registry_version="1.0.0",
            registry_owner="oracle_intelligence",
            enrollment_status="enrolled_registry_ready",
            enrollment_score=0.98,
            promotion_hash="demo-promotion-hash",
            replay_hash="demo-replay-hash",
            enrollment_hash="demo-enrollment-hash-123456789",
            enrolled_at=1760000000.0,
        ),
        AdapterRegistryValidationRecord(
            registry_id="",
            candidate_id="demo.crypto",
            name="Demo Crypto Invalid Registry Record",
            market_type="crypto",
            source_kind="vendor_export",
            registry_namespace="",
            registry_version="",
            registry_owner="",
            enrollment_status="not_enrolled",
            enrollment_score=0.0,
            promotion_hash="",
            replay_hash="",
            enrollment_hash="",
            enrolled_at=1760000000.0,
        ),
    )


if __name__ == "__main__":
    snapshot = validate_records(demo_records(), validated_at=1760000000.0)
    print(snapshot_to_json(snapshot))
