from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
MODULE_PATH = MODULE_DIR / "universal_market_adapter_registry_enrollment_engine.py"
TEST_PATH = ROOT / "test_oi_180_universal_market_adapter_registry_enrollment_engine.py"
INIT_PATH = MODULE_DIR / "__init__.py"

MODULE_CODE = r'''
"""
OI-180 — Oracle Universal Market Adapter Registry Enrollment Engine

Read-only registry enrollment layer for Universal Market Adapter candidates.

Enrollment is the step after promotion. It creates an explainable, replayable
registry enrollment record for adapters that have reached registry-ready status.

This engine does not activate execution.
This engine does not submit orders.
This engine does not manage positions.
This engine does not mutate external systems.

Oracle remains intelligence-only.
Q Series remains the sole execution owner.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


ENGINE_ID = "oi.180.universal_market_adapter_registry_enrollment"
ENGINE_NAME = "Oracle Universal Market Adapter Registry Enrollment Engine"
ENGINE_VERSION = "1.0.0"
ARCHITECTURE_ROLE = "read_only_adapter_registry_enrollment"
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

ENROLLMENT_GATES = (
    "read_only_boundary_enrolled",
    "q_series_execution_boundary_enrolled",
    "promotion_status_enrolled",
    "registry_identity_enrolled",
    "registry_version_enrolled",
    "registry_owner_enrolled",
    "promotion_hash_enrolled",
    "replay_hash_enrolled",
    "telemetry_enrolled",
    "explanation_enrolled",
)


@dataclass(frozen=True)
class AdapterRegistryEnrollmentCandidate:
    candidate_id: str
    name: str
    market_type: str
    source_kind: str
    promotion_level: str
    promotion_score: float
    promoted: bool
    promotion_hash: Optional[str] = None
    replay_hash: Optional[str] = None
    registry_namespace: Optional[str] = None
    registry_version: Optional[str] = None
    registry_owner: Optional[str] = None
    explanation_ready: bool = False
    telemetry_ready: bool = False
    enrollment_notes: Tuple[str, ...] = field(default_factory=tuple)
    warning_count: int = 0
    blocker_count: int = 0
    read_only: bool = True
    execution_owner: str = Q_SERIES_EXECUTION_OWNER
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def normalized(self) -> Dict[str, Any]:
        return {
            "candidate_id": str(self.candidate_id),
            "name": str(self.name),
            "market_type": normalize_market_type(self.market_type),
            "source_kind": str(self.source_kind),
            "promotion_level": str(self.promotion_level),
            "promotion_score": clamp(self.promotion_score),
            "promoted": bool(self.promoted),
            "promotion_hash": self.promotion_hash,
            "replay_hash": self.replay_hash,
            "registry_namespace": self.registry_namespace,
            "registry_version": self.registry_version,
            "registry_owner": self.registry_owner,
            "explanation_ready": bool(self.explanation_ready),
            "telemetry_ready": bool(self.telemetry_ready),
            "enrollment_notes": list(self.enrollment_notes),
            "warning_count": max(0, int(self.warning_count)),
            "blocker_count": max(0, int(self.blocker_count)),
            "read_only": bool(self.read_only),
            "execution_owner": str(self.execution_owner),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class AdapterRegistryEnrollmentRecord:
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
    enrolled_at: float
    read_only: bool
    execution_owner: str
    enrollment_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "registry_id": self.registry_id,
            "candidate_id": self.candidate_id,
            "name": self.name,
            "market_type": self.market_type,
            "source_kind": self.source_kind,
            "registry_namespace": self.registry_namespace,
            "registry_version": self.registry_version,
            "registry_owner": self.registry_owner,
            "enrollment_status": self.enrollment_status,
            "enrollment_score": self.enrollment_score,
            "promotion_hash": self.promotion_hash,
            "replay_hash": self.replay_hash,
            "enrolled_at": self.enrolled_at,
            "read_only": self.read_only,
            "execution_owner": self.execution_owner,
            "enrollment_hash": self.enrollment_hash,
        }


@dataclass(frozen=True)
class AdapterRegistryEnrollmentDecision:
    candidate: AdapterRegistryEnrollmentCandidate
    enrolled: bool
    enrollment_status: str
    enrollment_score: float
    gates: Mapping[str, bool]
    blockers: Tuple[str, ...]
    warnings: Tuple[str, ...]
    record: Optional[AdapterRegistryEnrollmentRecord]
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    enrollment_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate": self.candidate.normalized(),
            "enrolled": self.enrolled,
            "enrollment_status": self.enrollment_status,
            "enrollment_score": self.enrollment_score,
            "gates": dict(self.gates),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "record": self.record.to_dict() if self.record else None,
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "enrollment_hash": self.enrollment_hash,
        }


@dataclass(frozen=True)
class AdapterRegistryEnrollmentSnapshot:
    engine_id: str
    engine_name: str
    engine_version: str
    created_at: float
    decision_count: int
    enrolled_count: int
    decisions: Tuple[AdapterRegistryEnrollmentDecision, ...]
    records: Tuple[AdapterRegistryEnrollmentRecord, ...]
    architecture: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "decision_count": self.decision_count,
            "enrolled_count": self.enrolled_count,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "records": [record.to_dict() for record in self.records],
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
        "adapter_registry_enrollment_ready": True,
        "guardrails": list(READ_ONLY_GUARDRAILS),
    }


def build_enrollment_gates(candidate: AdapterRegistryEnrollmentCandidate) -> Dict[str, bool]:
    data = candidate.normalized()
    return {
        "read_only_boundary_enrolled": data["read_only"] is True,
        "q_series_execution_boundary_enrolled": data["execution_owner"] == Q_SERIES_EXECUTION_OWNER,
        "promotion_status_enrolled": (
            data["promoted"] is True
            and data["promotion_level"] in {"promoted_to_registry_ready", "promoted_with_conditions", "enrolled"}
            and data["promotion_score"] >= 0.78
        ),
        "registry_identity_enrolled": bool(data["registry_namespace"]),
        "registry_version_enrolled": bool(data["registry_version"]),
        "registry_owner_enrolled": bool(data["registry_owner"]),
        "promotion_hash_enrolled": bool(data["promotion_hash"]),
        "replay_hash_enrolled": bool(data["replay_hash"]),
        "telemetry_enrolled": data["telemetry_ready"] is True,
        "explanation_enrolled": data["explanation_ready"] is True,
    }


def enrollment_score(candidate: AdapterRegistryEnrollmentCandidate, gates: Mapping[str, bool]) -> float:
    data = candidate.normalized()
    gate_ratio = sum(1 for value in gates.values() if value) / len(gates)

    score = data["promotion_score"] * 0.55 + gate_ratio * 0.45
    penalty = min(0.25, (data["warning_count"] * 0.02) + (data["blocker_count"] * 0.06))
    return round(max(0.0, min(1.0, score - penalty)), 6)


def enrollment_status(score: float, gates: Mapping[str, bool]) -> str:
    core = (
        gates.get("read_only_boundary_enrolled", False),
        gates.get("q_series_execution_boundary_enrolled", False),
        gates.get("promotion_status_enrolled", False),
        gates.get("registry_identity_enrolled", False),
        gates.get("registry_version_enrolled", False),
        gates.get("registry_owner_enrolled", False),
    )

    if all(gates.values()) and score >= 0.88:
        return "enrolled_registry_ready"
    if all(core) and score >= 0.76:
        return "enrolled_with_conditions"
    if gates.get("read_only_boundary_enrolled", False) and score >= 0.55:
        return "enrollment_research_required"
    return "not_enrolled"


def recommend_next_step(status: str) -> str:
    if status == "enrolled_registry_ready":
        return "Store enrollment record in registry governance workflow for controlled adapter lifecycle tracking."
    if status == "enrolled_with_conditions":
        return "Resolve conditional enrollment gaps before final registry availability."
    if status == "enrollment_research_required":
        return "Collect missing registry metadata, replay hash, telemetry, or explanation artifacts."
    return "Do not enroll. Core enrollment gates failed."


def build_registry_id(candidate: AdapterRegistryEnrollmentCandidate) -> str:
    data = candidate.normalized()
    namespace = str(data["registry_namespace"] or "oracle.adapters.unknown")
    market = normalize_market_type(data["market_type"])
    identity = str(data["candidate_id"])
    version = str(data["registry_version"] or "0.0.0")
    return f"{namespace}.{market}.{identity}.v{version}".replace(" ", "_")


def enroll_candidate(
    candidate: AdapterRegistryEnrollmentCandidate,
    enrolled_at: Optional[float] = None,
) -> AdapterRegistryEnrollmentDecision:
    timestamp = float(enrolled_at if enrolled_at is not None else time.time())
    gates = build_enrollment_gates(candidate)
    score = enrollment_score(candidate, gates)
    status = enrollment_status(score, gates)
    enrolled = status in {"enrolled_registry_ready", "enrolled_with_conditions"}

    core_names = {
        "read_only_boundary_enrolled",
        "q_series_execution_boundary_enrolled",
        "promotion_status_enrolled",
        "registry_identity_enrolled",
        "registry_version_enrolled",
        "registry_owner_enrolled",
    }

    blockers = tuple(name for name, passed in gates.items() if not passed and name in core_names)
    warnings = tuple(name for name, passed in gates.items() if not passed and name not in core_names)

    enrollment_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "candidate": candidate.normalized(),
        "gates": dict(gates),
        "score": score,
        "status": status,
        "enrolled": enrolled,
        "blockers": blockers,
        "warnings": warnings,
    })

    record = None
    if enrolled:
        data = candidate.normalized()
        record = AdapterRegistryEnrollmentRecord(
            registry_id=build_registry_id(candidate),
            candidate_id=data["candidate_id"],
            name=data["name"],
            market_type=data["market_type"],
            source_kind=data["source_kind"],
            registry_namespace=str(data["registry_namespace"]),
            registry_version=str(data["registry_version"]),
            registry_owner=str(data["registry_owner"]),
            enrollment_status=status,
            enrollment_score=score,
            promotion_hash=str(data["promotion_hash"]),
            replay_hash=str(data["replay_hash"]),
            enrolled_at=timestamp,
            read_only=True,
            execution_owner=Q_SERIES_EXECUTION_OWNER,
            enrollment_hash=enrollment_hash,
        )

    explanation = {
        "summary": f"{candidate.name} received enrollment status {status} with score {score:.3f}.",
        "enrolled": enrolled,
        "market_type": normalize_market_type(candidate.market_type),
        "source_kind": candidate.source_kind,
        "passed_gates": [name for name, passed in gates.items() if passed],
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "blockers": list(blockers),
        "warnings": list(warnings),
        "read_only_statement": "Enrollment is descriptive only and cannot execute, route, submit, or manage trades.",
        "q_series_boundary": "Q Series remains the sole execution owner.",
        "registry_boundary": "Enrollment creates registry governance records only; it does not activate execution.",
        "next_step": recommend_next_step(status),
    }

    telemetry = {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "architecture_role": ARCHITECTURE_ROLE,
        "candidate_id": candidate.candidate_id,
        "market_type": normalize_market_type(candidate.market_type),
        "enrollment_status": status,
        "enrolled": enrolled,
        "enrollment_score": score,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "enrolled_at": timestamp,
    }

    return AdapterRegistryEnrollmentDecision(
        candidate=candidate,
        enrolled=enrolled,
        enrollment_status=status,
        enrollment_score=score,
        gates=gates,
        blockers=blockers,
        warnings=warnings,
        record=record,
        explanation=explanation,
        telemetry=telemetry,
        enrollment_hash=enrollment_hash,
    )


def enroll_adapters(
    candidates: Iterable[AdapterRegistryEnrollmentCandidate],
    enrolled_at: Optional[float] = None,
) -> AdapterRegistryEnrollmentSnapshot:
    timestamp = float(enrolled_at if enrolled_at is not None else time.time())
    decisions = tuple(
        sorted(
            (enroll_candidate(candidate, enrolled_at=timestamp) for candidate in candidates),
            key=lambda decision: (-decision.enrollment_score, decision.candidate.name.lower(), decision.candidate.candidate_id),
        )
    )

    records = tuple(decision.record for decision in decisions if decision.record is not None)
    architecture = architecture_contract()
    replay_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "created_at": timestamp,
        "decision_hashes": [decision.enrollment_hash for decision in decisions],
        "record_hashes": [record.enrollment_hash for record in records],
        "architecture": architecture,
    })

    return AdapterRegistryEnrollmentSnapshot(
        engine_id=ENGINE_ID,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        created_at=timestamp,
        decision_count=len(decisions),
        enrolled_count=sum(1 for decision in decisions if decision.enrolled),
        decisions=decisions,
        records=records,
        architecture=architecture,
        replay_hash=replay_hash,
    )


def candidate_from_promotion_decision(decision: Mapping[str, Any]) -> AdapterRegistryEnrollmentCandidate:
    candidate = decision.get("candidate", {})
    telemetry = decision.get("telemetry", {})
    promoted = bool(decision.get("promoted", telemetry.get("promoted", False)))

    return AdapterRegistryEnrollmentCandidate(
        candidate_id=str(candidate.get("candidate_id") or telemetry.get("candidate_id") or "unknown"),
        name=str(candidate.get("name") or candidate.get("candidate_id") or "Unknown Enrollment Candidate"),
        market_type=str(candidate.get("market_type") or telemetry.get("market_type") or "unknown"),
        source_kind=str(candidate.get("source_kind") or "unknown"),
        promotion_level=str(decision.get("promotion_level") or telemetry.get("promotion_level") or "unknown"),
        promotion_score=clamp(decision.get("promotion_score", telemetry.get("promotion_score", 0.0))),
        promoted=promoted,
        promotion_hash=decision.get("promotion_hash"),
        replay_hash=decision.get("promotion_hash") or telemetry.get("replay_hash"),
        registry_namespace=candidate.get("registry_namespace"),
        registry_version=candidate.get("registry_version"),
        registry_owner=candidate.get("registry_owner"),
        explanation_ready=bool(decision.get("explanation")),
        telemetry_ready=bool(decision.get("telemetry")),
        warning_count=int(telemetry.get("warning_count", len(decision.get("warnings", [])))),
        blocker_count=int(telemetry.get("blocker_count", len(decision.get("blockers", [])))),
        read_only=bool(telemetry.get("read_only", candidate.get("read_only", True))),
        execution_owner=str(telemetry.get("execution_owner", candidate.get("execution_owner", Q_SERIES_EXECUTION_OWNER))),
        evidence=candidate.get("evidence", {}),
    )


def enroll_promotion_snapshot(snapshot: Mapping[str, Any]) -> AdapterRegistryEnrollmentSnapshot:
    candidates = [
        candidate_from_promotion_decision(decision)
        for decision in snapshot.get("decisions", [])
    ]
    return enroll_adapters(candidates, enrolled_at=float(snapshot.get("created_at", time.time())))


def snapshot_to_json(snapshot: AdapterRegistryEnrollmentSnapshot, indent: int = 2) -> str:
    return json.dumps(snapshot.to_dict(), indent=indent, sort_keys=True, default=str)


class UniversalMarketAdapterRegistryEnrollmentEngine:
    def __init__(self) -> None:
        self._history = []

    def enroll(
        self,
        candidates: Iterable[AdapterRegistryEnrollmentCandidate],
        enrolled_at: Optional[float] = None,
    ) -> AdapterRegistryEnrollmentSnapshot:
        snapshot = enroll_adapters(candidates, enrolled_at=enrolled_at)
        self._history.append(snapshot)
        return snapshot

    def enroll_promotion_snapshot(self, snapshot: Mapping[str, Any]) -> AdapterRegistryEnrollmentSnapshot:
        enrolled = enroll_promotion_snapshot(snapshot)
        self._history.append(enrolled)
        return enrolled

    def latest_snapshot(self) -> Optional[AdapterRegistryEnrollmentSnapshot]:
        return self._history[-1] if self._history else None

    def history(self) -> Tuple[AdapterRegistryEnrollmentSnapshot, ...]:
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
            "latest_enrolled_count": latest.enrolled_count if latest else 0,
            "guardrails": list(READ_ONLY_GUARDRAILS),
        }


oracle_universal_market_adapter_registry_enrollment_engine = UniversalMarketAdapterRegistryEnrollmentEngine()
universal_market_adapter_registry_enrollment_engine = oracle_universal_market_adapter_registry_enrollment_engine


def demo_candidates() -> Tuple[AdapterRegistryEnrollmentCandidate, ...]:
    return (
        AdapterRegistryEnrollmentCandidate(
            candidate_id="demo.prediction.enrolled",
            name="Demo Prediction Enrolled Candidate",
            market_type="prediction_markets",
            source_kind="api_schema",
            promotion_level="promoted_to_registry_ready",
            promotion_score=0.98,
            promoted=True,
            promotion_hash="demo-promotion-hash",
            replay_hash="demo-replay-hash",
            registry_namespace="oracle.adapters.prediction_markets",
            registry_version="1.0.0",
            registry_owner="oracle_intelligence",
            explanation_ready=True,
            telemetry_ready=True,
            enrollment_notes=("Demo registry-ready enrollment fixture.",),
            warning_count=0,
            blocker_count=0,
        ),
        AdapterRegistryEnrollmentCandidate(
            candidate_id="demo.crypto.not_enrolled",
            name="Demo Crypto Not Enrolled Candidate",
            market_type="crypto",
            source_kind="vendor_export",
            promotion_level="not_promoted",
            promotion_score=0.00,
            promoted=False,
            warning_count=6,
            blocker_count=2,
        ),
    )


if __name__ == "__main__":
    snapshot = enroll_adapters(demo_candidates(), enrolled_at=1760000000.0)
    print(snapshot_to_json(snapshot))
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_registry_enrollment_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterRegistryEnrollmentCandidate,
    UniversalMarketAdapterRegistryEnrollmentEngine,
    architecture_contract,
    candidate_from_promotion_decision,
    demo_candidates,
    enroll_adapters,
    snapshot_to_json,
)


def test_enrollment_snapshot_contract():
    snapshot = enroll_adapters(demo_candidates(), enrolled_at=1760000000.0)

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.decision_count == 2
    assert snapshot.enrolled_count == 1
    assert len(snapshot.records) == 1
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert snapshot.replay_hash


def test_enrolled_candidate_creates_registry_record():
    snapshot = enroll_adapters(demo_candidates(), enrolled_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.enrolled is True
    assert decision.enrollment_status == "enrolled_registry_ready"
    assert decision.record is not None
    assert decision.record.registry_id
    assert decision.record.read_only is True
    assert decision.record.execution_owner == Q_SERIES_EXECUTION_OWNER
    assert decision.gates["promotion_status_enrolled"] is True
    assert decision.explanation["q_series_boundary"] == "Q Series remains the sole execution owner."


def test_not_enrolled_candidate_has_blockers():
    weak = AdapterRegistryEnrollmentCandidate(
        candidate_id="weak.adapter",
        name="Weak Adapter Candidate",
        market_type="news",
        source_kind="manual_note",
        promotion_level="not_promoted",
        promotion_score=0.10,
        promoted=False,
        warning_count=5,
        blocker_count=3,
        read_only=True,
        execution_owner=Q_SERIES_EXECUTION_OWNER,
    )

    snapshot = enroll_adapters([weak], enrolled_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.enrolled is False
    assert decision.enrollment_status == "not_enrolled"
    assert decision.record is None
    assert "promotion_status_enrolled" in decision.blockers


def test_candidate_from_promotion_decision_mapping():
    promotion_decision = {
        "candidate": {
            "candidate_id": "promoted.weather",
            "name": "Promoted Weather Candidate",
            "market_type": "weather",
            "source_kind": "registry_item",
            "registry_namespace": "oracle.adapters.weather",
            "registry_version": "1.0.0",
            "registry_owner": "oracle_intelligence",
            "evidence": {"fixture": True},
        },
        "promoted": True,
        "promotion_level": "promoted_to_registry_ready",
        "promotion_score": 0.94,
        "promotion_hash": "weather-promotion-hash",
        "explanation": {"summary": "promoted"},
        "telemetry": {
            "promoted": True,
            "promotion_level": "promoted_to_registry_ready",
            "promotion_score": 0.94,
            "warning_count": 0,
            "blocker_count": 0,
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
        },
    }

    candidate = candidate_from_promotion_decision(promotion_decision)
    snapshot = enroll_adapters([candidate], enrolled_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert candidate.candidate_id == "promoted.weather"
    assert decision.enrolled is True
    assert decision.record is not None
    assert decision.gates["registry_identity_enrolled"] is True


def test_engine_history_and_json():
    engine = UniversalMarketAdapterRegistryEnrollmentEngine()
    snapshot = engine.enroll(demo_candidates(), enrolled_at=1760000000.0)

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Registry Enrollment Engine" in text
    assert "read_only" in text


def test_architecture_contract():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["adapter_registry_enrollment_ready"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_enrollment_snapshot_contract()
    test_enrolled_candidate_creates_registry_record()
    test_not_enrolled_candidate_has_blockers()
    test_candidate_from_promotion_decision_mapping()
    test_engine_history_and_json()
    test_architecture_contract()
    print("[PASS] OI-180 Universal Market Adapter Registry Enrollment Engine")
    print(enroll_adapters(demo_candidates(), enrolled_at=1760000000.0).to_dict())
'''


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def update_init() -> None:
    INIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if INIT_PATH.exists():
        existing = INIT_PATH.read_text(encoding="utf-8")
    else:
        existing = ""

    export_line = (
        "from .universal_market_adapter_registry_enrollment_engine import "
        "UniversalMarketAdapterRegistryEnrollmentEngine, "
        "oracle_universal_market_adapter_registry_enrollment_engine, "
        "universal_market_adapter_registry_enrollment_engine\n"
    )

    additions = [
        "UniversalMarketAdapterRegistryEnrollmentEngine",
        "oracle_universal_market_adapter_registry_enrollment_engine",
        "universal_market_adapter_registry_enrollment_engine",
    ]

    if export_line not in existing:
        existing = existing.rstrip() + "\n" + export_line

    if "__all__" not in existing:
        existing += "\n__all__ = [\n"
        for item in additions:
            existing += f'    "{item}",\n'
        existing += "]\n"
    else:
        for item in additions:
            token = f'"{item}"'
            if token not in existing:
                existing = existing.replace("__all__ = [", f'__all__ = [\n    "{item}",')

    INIT_PATH.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-180 INSTALLER")
    print(" Universal Market Adapter Registry Enrollment Engine")
    print("========================================")

    write_file(MODULE_PATH, MODULE_CODE)
    print(f"[OK] Wrote {MODULE_PATH}")

    write_file(TEST_PATH, TEST_CODE)
    print(f"[OK] Wrote {TEST_PATH}")

    update_init()
    print(f"[OK] Updated {INIT_PATH}")

    print()
    print("[DONE] OI-180 installed")
    print()
    print("Run:")
    print("py test_oi_180_universal_market_adapter_registry_enrollment_engine.py")


if __name__ == "__main__":
    main()