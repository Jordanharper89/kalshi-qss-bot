
"""
OI-179 — Oracle Universal Market Adapter Promotion Engine

Read-only institutional promotion layer for Universal Market Adapter candidates.

Promotion is the step after certification. It evaluates whether a certified
adapter candidate is eligible to be promoted into registry-ready status while
preserving the strict Oracle/Q Series boundary:

- Oracle remains read-only.
- Oracle never executes trades.
- Oracle never submits orders.
- Oracle never manages positions.
- Q Series remains the sole execution owner.

This engine does not activate live execution. It produces explainable,
replayable promotion decisions for architecture registry workflows.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


ENGINE_ID = "oi.179.universal_market_adapter_promotion"
ENGINE_NAME = "Oracle Universal Market Adapter Promotion Engine"
ENGINE_VERSION = "1.0.0"
ARCHITECTURE_ROLE = "read_only_adapter_promotion"
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

PROMOTION_GATES = (
    "read_only_boundary_promoted",
    "q_series_execution_boundary_promoted",
    "certification_status_promoted",
    "registry_metadata_promoted",
    "replay_artifact_promoted",
    "explanation_artifact_promoted",
    "telemetry_artifact_promoted",
    "rollback_plan_promoted",
    "human_review_promoted",
    "architecture_registry_promoted",
)


@dataclass(frozen=True)
class AdapterPromotionCandidate:
    candidate_id: str
    name: str
    market_type: str
    source_kind: str
    certification_level: str
    certification_score: float
    certified: bool
    certification_hash: Optional[str] = None
    replay_hash: Optional[str] = None
    registry_namespace: Optional[str] = None
    registry_version: Optional[str] = None
    registry_owner: Optional[str] = None
    explanation_ready: bool = False
    telemetry_ready: bool = False
    rollback_plan_ready: bool = False
    human_review_status: str = "pending"
    architecture_registry_ready: bool = False
    promotion_notes: Tuple[str, ...] = field(default_factory=tuple)
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
            "certification_level": str(self.certification_level),
            "certification_score": clamp(self.certification_score),
            "certified": bool(self.certified),
            "certification_hash": self.certification_hash,
            "replay_hash": self.replay_hash,
            "registry_namespace": self.registry_namespace,
            "registry_version": self.registry_version,
            "registry_owner": self.registry_owner,
            "explanation_ready": bool(self.explanation_ready),
            "telemetry_ready": bool(self.telemetry_ready),
            "rollback_plan_ready": bool(self.rollback_plan_ready),
            "human_review_status": str(self.human_review_status or "pending").strip().lower(),
            "architecture_registry_ready": bool(self.architecture_registry_ready),
            "promotion_notes": list(self.promotion_notes),
            "warning_count": max(0, int(self.warning_count)),
            "blocker_count": max(0, int(self.blocker_count)),
            "read_only": bool(self.read_only),
            "execution_owner": str(self.execution_owner),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class AdapterPromotionDecision:
    candidate: AdapterPromotionCandidate
    promoted: bool
    promotion_level: str
    promotion_score: float
    gates: Mapping[str, bool]
    blockers: Tuple[str, ...]
    warnings: Tuple[str, ...]
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    promotion_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate": self.candidate.normalized(),
            "promoted": self.promoted,
            "promotion_level": self.promotion_level,
            "promotion_score": self.promotion_score,
            "gates": dict(self.gates),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "promotion_hash": self.promotion_hash,
        }


@dataclass(frozen=True)
class AdapterPromotionSnapshot:
    engine_id: str
    engine_name: str
    engine_version: str
    created_at: float
    decision_count: int
    promoted_count: int
    decisions: Tuple[AdapterPromotionDecision, ...]
    architecture: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "decision_count": self.decision_count,
            "promoted_count": self.promoted_count,
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
        "adapter_promotion_ready": True,
        "guardrails": list(READ_ONLY_GUARDRAILS),
    }


def build_promotion_gates(candidate: AdapterPromotionCandidate) -> Dict[str, bool]:
    data = candidate.normalized()

    return {
        "read_only_boundary_promoted": data["read_only"] is True,
        "q_series_execution_boundary_promoted": data["execution_owner"] == Q_SERIES_EXECUTION_OWNER,
        "certification_status_promoted": (
            data["certified"] is True
            and data["certification_level"] in {
                "certified_for_registry_promotion",
                "certified_with_conditions",
                "promoted",
            }
            and data["certification_score"] >= 0.80
            and bool(data["certification_hash"])
        ),
        "registry_metadata_promoted": (
            bool(data["registry_namespace"])
            and bool(data["registry_version"])
            and bool(data["registry_owner"])
        ),
        "replay_artifact_promoted": bool(data["replay_hash"]),
        "explanation_artifact_promoted": data["explanation_ready"] is True,
        "telemetry_artifact_promoted": data["telemetry_ready"] is True,
        "rollback_plan_promoted": data["rollback_plan_ready"] is True,
        "human_review_promoted": data["human_review_status"] in {"approved", "accepted", "reviewed"},
        "architecture_registry_promoted": data["architecture_registry_ready"] is True,
    }


def promotion_score(candidate: AdapterPromotionCandidate, gates: Mapping[str, bool]) -> float:
    data = candidate.normalized()
    gate_ratio = sum(1 for value in gates.values() if value) / len(gates)

    score = (
        data["certification_score"] * 0.42
        + gate_ratio * 0.38
        + (1.0 if data["architecture_registry_ready"] else 0.0) * 0.08
        + (1.0 if data["rollback_plan_ready"] else 0.0) * 0.05
        + (1.0 if data["human_review_status"] in {"approved", "accepted", "reviewed"} else 0.0) * 0.07
    )

    penalty = min(0.30, (data["warning_count"] * 0.025) + (data["blocker_count"] * 0.07))
    return round(max(0.0, min(1.0, score - penalty)), 6)


def promotion_level(score: float, gates: Mapping[str, bool]) -> str:
    core_gates = (
        gates.get("read_only_boundary_promoted", False),
        gates.get("q_series_execution_boundary_promoted", False),
        gates.get("certification_status_promoted", False),
        gates.get("registry_metadata_promoted", False),
    )

    if all(gates.values()) and score >= 0.90:
        return "promoted_to_registry_ready"
    if all(core_gates) and score >= 0.78:
        return "promoted_with_conditions"
    if gates.get("read_only_boundary_promoted", False) and score >= 0.58:
        return "promotion_research_required"
    return "not_promoted"


def recommend_next_step(level: str) -> str:
    if level == "promoted_to_registry_ready":
        return "Move candidate into registry-ready queue for controlled activation by governance workflow."
    if level == "promoted_with_conditions":
        return "Resolve conditional promotion gaps before registry-ready queue movement."
    if level == "promotion_research_required":
        return "Collect missing registry metadata, replay artifacts, rollback plan, or human review."
    return "Do not promote. Core promotion gates failed."

def promote_candidate(
    candidate: AdapterPromotionCandidate,
    promoted_at: Optional[float] = None,
) -> AdapterPromotionDecision:
    timestamp = float(promoted_at if promoted_at is not None else time.time())
    gates = build_promotion_gates(candidate)
    score = promotion_score(candidate, gates)
    level = promotion_level(score, gates)
    promoted = level in {"promoted_to_registry_ready", "promoted_with_conditions"}

    core_names = {
        "read_only_boundary_promoted",
        "q_series_execution_boundary_promoted",
        "certification_status_promoted",
        "registry_metadata_promoted",
    }

    blockers = tuple(name for name, passed in gates.items() if not passed and name in core_names)
    warnings = tuple(name for name, passed in gates.items() if not passed and name not in core_names)

    explanation = {
        "summary": f"{candidate.name} received promotion level {level} with score {score:.3f}.",
        "promoted": promoted,
        "market_type": normalize_market_type(candidate.market_type),
        "source_kind": candidate.source_kind,
        "passed_gates": [name for name, passed in gates.items() if passed],
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "blockers": list(blockers),
        "warnings": list(warnings),
        "read_only_statement": "Promotion is descriptive only and cannot execute, route, submit, or manage trades.",
        "q_series_boundary": "Q Series remains the sole execution owner.",
        "registry_boundary": "Promotion marks registry-ready eligibility only; it does not activate execution.",
        "next_step": recommend_next_step(level),
    }

    telemetry = {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "architecture_role": ARCHITECTURE_ROLE,
        "candidate_id": candidate.candidate_id,
        "market_type": normalize_market_type(candidate.market_type),
        "promotion_level": level,
        "promoted": promoted,
        "promotion_score": score,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "promoted_at": timestamp,
    }

    promotion_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "candidate": candidate.normalized(),
        "gates": dict(gates),
        "score": score,
        "level": level,
        "promoted": promoted,
        "blockers": blockers,
        "warnings": warnings,
    })

    return AdapterPromotionDecision(
        candidate=candidate,
        promoted=promoted,
        promotion_level=level,
        promotion_score=score,
        gates=gates,
        blockers=blockers,
        warnings=warnings,
        explanation=explanation,
        telemetry=telemetry,
        promotion_hash=promotion_hash,
    )


def promote_adapters(
    candidates: Iterable[AdapterPromotionCandidate],
    promoted_at: Optional[float] = None,
) -> AdapterPromotionSnapshot:
    timestamp = float(promoted_at if promoted_at is not None else time.time())

    decisions = tuple(
        sorted(
            (promote_candidate(candidate, promoted_at=timestamp) for candidate in candidates),
            key=lambda decision: (
                -decision.promotion_score,
                decision.candidate.name.lower(),
                decision.candidate.candidate_id,
            ),
        )
    )

    architecture = architecture_contract()

    replay_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "created_at": timestamp,
        "decision_hashes": [decision.promotion_hash for decision in decisions],
        "architecture": architecture,
    })

    return AdapterPromotionSnapshot(
        engine_id=ENGINE_ID,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        created_at=timestamp,
        decision_count=len(decisions),
        promoted_count=sum(1 for decision in decisions if decision.promoted),
        decisions=decisions,
        architecture=architecture,
        replay_hash=replay_hash,
    )


def candidate_from_certification_decision(decision: Mapping[str, Any]) -> AdapterPromotionCandidate:
    candidate = decision.get("candidate", {})
    telemetry = decision.get("telemetry", {})

    certified = bool(decision.get("certified", telemetry.get("certified", False)))
    certification_level = str(
        decision.get("certification_level")
        or telemetry.get("certification_level")
        or "unknown"
    )

    return AdapterPromotionCandidate(
        candidate_id=str(candidate.get("candidate_id") or telemetry.get("candidate_id") or "unknown"),
        name=str(candidate.get("name") or candidate.get("candidate_id") or "Unknown Promotion Candidate"),
        market_type=str(candidate.get("market_type") or telemetry.get("market_type") or "unknown"),
        source_kind=str(candidate.get("source_kind") or "unknown"),
        certification_level=certification_level,
        certification_score=clamp(
            decision.get(
                "certification_score",
                telemetry.get("certification_score", 0.0),
            )
        ),
        certified=certified,
        certification_hash=decision.get("certification_hash"),
        replay_hash=decision.get("certification_hash") or telemetry.get("replay_hash"),
        registry_namespace=str(candidate.get("registry_namespace") or f"oracle.adapters.{candidate.get('market_type', 'unknown')}")
        if certified
        else candidate.get("registry_namespace"),
        registry_version=str(candidate.get("registry_version") or "1.0.0") if certified else candidate.get("registry_version"),
        registry_owner=str(candidate.get("registry_owner") or "oracle_intelligence") if certified else candidate.get("registry_owner"),
        explanation_ready=bool(decision.get("explanation")),
        telemetry_ready=bool(decision.get("telemetry")),
        rollback_plan_ready=certified,
        human_review_status="approved" if certified and certification_level == "certified_for_registry_promotion" else "pending",
        architecture_registry_ready=bool(certified),
        warning_count=int(telemetry.get("warning_count", len(decision.get("warnings", [])))),
        blocker_count=int(telemetry.get("blocker_count", len(decision.get("blockers", [])))),
        read_only=bool(telemetry.get("read_only", candidate.get("read_only", True))),
        execution_owner=str(
            telemetry.get(
                "execution_owner",
                candidate.get("execution_owner", Q_SERIES_EXECUTION_OWNER),
            )
        ),
        evidence=candidate.get("evidence", {}),
    )


def promote_certification_snapshot(snapshot: Mapping[str, Any]) -> AdapterPromotionSnapshot:
    candidates = [
        candidate_from_certification_decision(decision)
        for decision in snapshot.get("decisions", [])
    ]
    return promote_adapters(candidates, promoted_at=float(snapshot.get("created_at", time.time())))


def snapshot_to_json(snapshot: AdapterPromotionSnapshot, indent: int = 2) -> str:
    return json.dumps(snapshot.to_dict(), indent=indent, sort_keys=True, default=str)


class UniversalMarketAdapterPromotionEngine:
    def __init__(self) -> None:
        self._history = []

    def promote(
        self,
        candidates: Iterable[AdapterPromotionCandidate],
        promoted_at: Optional[float] = None,
    ) -> AdapterPromotionSnapshot:
        snapshot = promote_adapters(candidates, promoted_at=promoted_at)
        self._history.append(snapshot)
        return snapshot

    def promote_certification_snapshot(self, snapshot: Mapping[str, Any]) -> AdapterPromotionSnapshot:
        promoted = promote_certification_snapshot(snapshot)
        self._history.append(promoted)
        return promoted

    def latest_snapshot(self) -> Optional[AdapterPromotionSnapshot]:
        return self._history[-1] if self._history else None

    def history(self) -> Tuple[AdapterPromotionSnapshot, ...]:
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
            "guardrails": list(READ_ONLY_GUARDRAILS),
        }


oracle_universal_market_adapter_promotion_engine = UniversalMarketAdapterPromotionEngine()
universal_market_adapter_promotion_engine = oracle_universal_market_adapter_promotion_engine


def demo_candidates() -> Tuple[AdapterPromotionCandidate, ...]:
    return (
        AdapterPromotionCandidate(
            candidate_id="demo.prediction.promoted",
            name="Demo Prediction Promoted Candidate",
            market_type="prediction_markets",
            source_kind="api_schema",
            certification_level="certified_for_registry_promotion",
            certification_score=0.96,
            certified=True,
            certification_hash="demo-certification-hash",
            replay_hash="demo-replay-hash",
            registry_namespace="oracle.adapters.prediction_markets",
            registry_version="1.0.0",
            registry_owner="oracle_intelligence",
            explanation_ready=True,
            telemetry_ready=True,
            rollback_plan_ready=True,
            human_review_status="approved",
            architecture_registry_ready=True,
            promotion_notes=("Demo fixture eligible for registry-ready promotion.",),
            warning_count=0,
            blocker_count=0,
        ),
        AdapterPromotionCandidate(
            candidate_id="demo.crypto.not_promoted",
            name="Demo Crypto Not Promoted Candidate",
            market_type="crypto",
            source_kind="vendor_export",
            certification_level="not_certified",
            certification_score=0.17,
            certified=False,
            certification_hash=None,
            replay_hash=None,
            explanation_ready=False,
            telemetry_ready=False,
            rollback_plan_ready=False,
            human_review_status="pending",
            architecture_registry_ready=False,
            warning_count=5,
            blocker_count=3,
        ),
    )


if __name__ == "__main__":
    snapshot = promote_adapters(demo_candidates(), promoted_at=1760000000.0)
    print(snapshot_to_json(snapshot))
