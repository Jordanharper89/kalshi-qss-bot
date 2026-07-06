
"""
OI-178 — Oracle Universal Market Adapter Certification Engine

Read-only institutional certification layer for Universal Market Adapter
candidates.

Certification is stricter than discovery and qualification. It verifies that a
candidate is eligible for registry promotion by checking read-only boundaries,
Universal Market Model compatibility, replay readiness, explainability,
telemetry, historical evidence, and institutional governance status.

Oracle remains intelligence-only.
Q Series remains the sole execution owner.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


ENGINE_ID = "oi.178.universal_market_adapter_certification"
ENGINE_NAME = "Oracle Universal Market Adapter Certification Engine"
ENGINE_VERSION = "1.0.0"
ARCHITECTURE_ROLE = "read_only_adapter_certification"
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

CERTIFICATION_GATES = (
    "read_only_boundary_certified",
    "q_series_execution_boundary_certified",
    "universal_market_model_certified",
    "qualification_status_certified",
    "schema_contract_certified",
    "replay_evidence_certified",
    "explainability_certified",
    "telemetry_certified",
    "historical_memory_certified",
    "governance_metadata_certified",
)


@dataclass(frozen=True)
class AdapterCertificationCandidate:
    candidate_id: str
    name: str
    market_type: str
    source_kind: str
    qualification_level: str
    qualification_score: float
    qualified: bool
    readiness_score: float
    required_umm_coverage_ratio: float
    market_specific_coverage_ratio: float
    optional_umm_coverage_ratio: float = 0.0
    replay_key: Optional[str] = None
    replay_hash: Optional[str] = None
    explanation_ready: bool = False
    telemetry_ready: bool = False
    historical_available: bool = False
    governance_owner: Optional[str] = None
    terms_known: bool = False
    rate_limit_known: bool = False
    health_check_available: bool = False
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
            "qualification_level": str(self.qualification_level),
            "qualification_score": clamp(self.qualification_score),
            "qualified": bool(self.qualified),
            "readiness_score": clamp(self.readiness_score),
            "required_umm_coverage_ratio": clamp(self.required_umm_coverage_ratio),
            "market_specific_coverage_ratio": clamp(self.market_specific_coverage_ratio),
            "optional_umm_coverage_ratio": clamp(self.optional_umm_coverage_ratio),
            "replay_key": self.replay_key,
            "replay_hash": self.replay_hash,
            "explanation_ready": bool(self.explanation_ready),
            "telemetry_ready": bool(self.telemetry_ready),
            "historical_available": bool(self.historical_available),
            "governance_owner": self.governance_owner,
            "terms_known": bool(self.terms_known),
            "rate_limit_known": bool(self.rate_limit_known),
            "health_check_available": bool(self.health_check_available),
            "warning_count": max(0, int(self.warning_count)),
            "blocker_count": max(0, int(self.blocker_count)),
            "read_only": bool(self.read_only),
            "execution_owner": str(self.execution_owner),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class AdapterCertificationDecision:
    candidate: AdapterCertificationCandidate
    certified: bool
    certification_level: str
    certification_score: float
    gates: Mapping[str, bool]
    blockers: Tuple[str, ...]
    warnings: Tuple[str, ...]
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    certification_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate": self.candidate.normalized(),
            "certified": self.certified,
            "certification_level": self.certification_level,
            "certification_score": self.certification_score,
            "gates": dict(self.gates),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "certification_hash": self.certification_hash,
        }


@dataclass(frozen=True)
class AdapterCertificationSnapshot:
    engine_id: str
    engine_name: str
    engine_version: str
    created_at: float
    decision_count: int
    certified_count: int
    decisions: Tuple[AdapterCertificationDecision, ...]
    architecture: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "decision_count": self.decision_count,
            "certified_count": self.certified_count,
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
        "adapter_certification_ready": True,
        "guardrails": list(READ_ONLY_GUARDRAILS),
    }


def build_certification_gates(candidate: AdapterCertificationCandidate) -> Dict[str, bool]:
    data = candidate.normalized()

    return {
        "read_only_boundary_certified": data["read_only"] is True,
        "q_series_execution_boundary_certified": data["execution_owner"] == Q_SERIES_EXECUTION_OWNER,
        "universal_market_model_certified": (
            data["required_umm_coverage_ratio"] >= 0.95
            and data["market_specific_coverage_ratio"] >= 0.80
        ),
        "qualification_status_certified": (
            data["qualified"] is True
            and data["qualification_level"] in {
                "qualified_for_registry_review",
                "qualified_with_conditions",
                "certified",
            }
            and data["qualification_score"] >= 0.74
        ),
        "schema_contract_certified": data["readiness_score"] >= 0.80,
        "replay_evidence_certified": bool(data["replay_key"] or data["replay_hash"]),
        "explainability_certified": data["explanation_ready"] is True and data["warning_count"] <= 2,
        "telemetry_certified": data["telemetry_ready"] is True,
        "historical_memory_certified": data["historical_available"] is True,
        "governance_metadata_certified": (
            bool(data["governance_owner"])
            and data["terms_known"] is True
            and data["rate_limit_known"] is True
            and data["health_check_available"] is True
        ),
    }


def certification_score(candidate: AdapterCertificationCandidate, gates: Mapping[str, bool]) -> float:
    data = candidate.normalized()
    gate_ratio = sum(1 for value in gates.values() if value) / len(gates)

    score = (
        data["qualification_score"] * 0.25
        + data["readiness_score"] * 0.20
        + data["required_umm_coverage_ratio"] * 0.20
        + data["market_specific_coverage_ratio"] * 0.15
        + data["optional_umm_coverage_ratio"] * 0.05
        + gate_ratio * 0.15
    )

    penalty = min(0.25, (data["warning_count"] * 0.025) + (data["blocker_count"] * 0.06))
    return round(max(0.0, min(1.0, score - penalty)), 6)


def certification_level(score: float, gates: Mapping[str, bool]) -> str:
    core_gates = (
        gates.get("read_only_boundary_certified", False),
        gates.get("q_series_execution_boundary_certified", False),
        gates.get("universal_market_model_certified", False),
        gates.get("qualification_status_certified", False),
        gates.get("schema_contract_certified", False),
    )

    if all(gates.values()) and score >= 0.90:
        return "certified_for_registry_promotion"
    if all(core_gates) and score >= 0.80:
        return "certified_with_conditions"
    if gates.get("read_only_boundary_certified", False) and score >= 0.60:
        return "certification_research_required"
    return "not_certified"


def recommend_next_step(level: str) -> str:
    if level == "certified_for_registry_promotion":
        return "Promote to adapter registry certification queue with human approval."
    if level == "certified_with_conditions":
        return "Resolve conditional certification gaps before production registry promotion."
    if level == "certification_research_required":
        return "Collect missing replay, telemetry, explainability, governance, or historical evidence."
    return "Do not promote. Certification gates failed."


def certify_candidate(
    candidate: AdapterCertificationCandidate,
    certified_at: Optional[float] = None,
) -> AdapterCertificationDecision:
    timestamp = float(certified_at if certified_at is not None else time.time())
    gates = build_certification_gates(candidate)
    score = certification_score(candidate, gates)
    level = certification_level(score, gates)
    certified = level in {"certified_for_registry_promotion", "certified_with_conditions"}

    core_names = {
        "read_only_boundary_certified",
        "q_series_execution_boundary_certified",
        "universal_market_model_certified",
        "qualification_status_certified",
        "schema_contract_certified",
    }

    blockers = tuple(name for name, passed in gates.items() if not passed and name in core_names)
    warnings = tuple(name for name, passed in gates.items() if not passed and name not in core_names)

    explanation = {
        "summary": f"{candidate.name} received certification level {level} with score {score:.3f}.",
        "certified": certified,
        "market_type": normalize_market_type(candidate.market_type),
        "source_kind": candidate.source_kind,
        "passed_gates": [name for name, passed in gates.items() if passed],
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "blockers": list(blockers),
        "warnings": list(warnings),
        "read_only_statement": "Certification is descriptive only and cannot execute, route, submit, or manage trades.",
        "q_series_boundary": "Q Series remains the sole execution owner.",
        "registry_boundary": "Certification marks registry eligibility only; it does not activate execution.",
        "next_step": recommend_next_step(level),
    }

    telemetry = {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "architecture_role": ARCHITECTURE_ROLE,
        "candidate_id": candidate.candidate_id,
        "market_type": normalize_market_type(candidate.market_type),
        "certification_level": level,
        "certified": certified,
        "certification_score": score,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "certified_at": timestamp,
    }

    certification_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "candidate": candidate.normalized(),
        "gates": dict(gates),
        "score": score,
        "level": level,
        "certified": certified,
        "blockers": blockers,
        "warnings": warnings,
    })

    return AdapterCertificationDecision(
        candidate=candidate,
        certified=certified,
        certification_level=level,
        certification_score=score,
        gates=gates,
        blockers=blockers,
        warnings=warnings,
        explanation=explanation,
        telemetry=telemetry,
        certification_hash=certification_hash,
    )


def certify_adapters(
    candidates: Iterable[AdapterCertificationCandidate],
    certified_at: Optional[float] = None,
) -> AdapterCertificationSnapshot:
    timestamp = float(certified_at if certified_at is not None else time.time())
    decisions = tuple(
        sorted(
            (certify_candidate(candidate, certified_at=timestamp) for candidate in candidates),
            key=lambda decision: (-decision.certification_score, decision.candidate.name.lower(), decision.candidate.candidate_id),
        )
    )

    architecture = architecture_contract()
    replay_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "created_at": timestamp,
        "decision_hashes": [decision.certification_hash for decision in decisions],
        "architecture": architecture,
    })

    return AdapterCertificationSnapshot(
        engine_id=ENGINE_ID,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        created_at=timestamp,
        decision_count=len(decisions),
        certified_count=sum(1 for decision in decisions if decision.certified),
        decisions=decisions,
        architecture=architecture,
        replay_hash=replay_hash,
    )


def candidate_from_qualification_decision(decision: Mapping[str, Any]) -> AdapterCertificationCandidate:
    candidate = decision.get("candidate", {})
    telemetry = decision.get("telemetry", {})
    evidence = candidate.get("evidence", {})

    return AdapterCertificationCandidate(
        candidate_id=str(candidate.get("candidate_id") or telemetry.get("candidate_id") or "unknown"),
        name=str(candidate.get("name") or candidate.get("candidate_id") or "Unknown Certification Candidate"),
        market_type=str(candidate.get("market_type") or telemetry.get("market_type") or "unknown"),
        source_kind=str(candidate.get("source_kind") or "unknown"),
        qualification_level=str(decision.get("qualification_level") or telemetry.get("qualification_level") or "unknown"),
        qualification_score=clamp(decision.get("score", telemetry.get("score", 0.0))),
        qualified=bool(decision.get("qualified", telemetry.get("qualified", False))),
        readiness_score=clamp(candidate.get("readiness_score", 0.0)),
        required_umm_coverage_ratio=clamp(candidate.get("required_umm_coverage_ratio", 0.0)),
        market_specific_coverage_ratio=clamp(candidate.get("market_specific_coverage_ratio", 0.0)),
        optional_umm_coverage_ratio=clamp(candidate.get("optional_umm_coverage_ratio", 0.0)),
        replay_key=candidate.get("replay_key"),
        replay_hash=decision.get("replay_hash"),
        explanation_ready=bool(decision.get("explanation")),
        telemetry_ready=bool(decision.get("telemetry")),
        historical_available=bool(candidate.get("historical_available", False)),
        governance_owner=str(candidate.get("governance_owner") or "oracle_intelligence")
        if decision.get("qualified", False)
        else candidate.get("governance_owner"),
        terms_known=bool(candidate.get("terms_known", False)),
        rate_limit_known=bool(candidate.get("rate_limit_known", False)),
        health_check_available=bool(candidate.get("health_check_available", False)),
        warning_count=int(telemetry.get("warning_count", len(decision.get("warnings", [])))),
        blocker_count=int(telemetry.get("blocker_count", len(decision.get("blockers", [])))),
        read_only=bool(telemetry.get("read_only", candidate.get("read_only", True))),
        execution_owner=str(telemetry.get("execution_owner", candidate.get("execution_owner", Q_SERIES_EXECUTION_OWNER))),
        evidence=evidence,
    )


def certify_qualification_snapshot(snapshot: Mapping[str, Any]) -> AdapterCertificationSnapshot:
    candidates = [
        candidate_from_qualification_decision(decision)
        for decision in snapshot.get("decisions", [])
    ]
    return certify_adapters(candidates, certified_at=float(snapshot.get("created_at", time.time())))


def snapshot_to_json(snapshot: AdapterCertificationSnapshot, indent: int = 2) -> str:
    return json.dumps(snapshot.to_dict(), indent=indent, sort_keys=True, default=str)


class UniversalMarketAdapterCertificationEngine:
    def __init__(self) -> None:
        self._history = []

    def certify(
        self,
        candidates: Iterable[AdapterCertificationCandidate],
        certified_at: Optional[float] = None,
    ) -> AdapterCertificationSnapshot:
        snapshot = certify_adapters(candidates, certified_at=certified_at)
        self._history.append(snapshot)
        return snapshot

    def certify_qualification_snapshot(self, snapshot: Mapping[str, Any]) -> AdapterCertificationSnapshot:
        certified = certify_qualification_snapshot(snapshot)
        self._history.append(certified)
        return certified

    def latest_snapshot(self) -> Optional[AdapterCertificationSnapshot]:
        return self._history[-1] if self._history else None

    def history(self) -> Tuple[AdapterCertificationSnapshot, ...]:
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


oracle_universal_market_adapter_certification_engine = UniversalMarketAdapterCertificationEngine()
universal_market_adapter_certification_engine = oracle_universal_market_adapter_certification_engine


def demo_candidates() -> Tuple[AdapterCertificationCandidate, ...]:
    return (
        AdapterCertificationCandidate(
            candidate_id="demo.prediction.certified",
            name="Demo Prediction Certified Candidate",
            market_type="prediction_markets",
            source_kind="api_schema",
            qualification_level="qualified_for_registry_review",
            qualification_score=0.94,
            qualified=True,
            readiness_score=0.96,
            required_umm_coverage_ratio=1.0,
            market_specific_coverage_ratio=1.0,
            optional_umm_coverage_ratio=0.72,
            replay_key="demo-replay-key",
            replay_hash="demo-replay-hash",
            explanation_ready=True,
            telemetry_ready=True,
            historical_available=True,
            governance_owner="oracle_intelligence",
            terms_known=True,
            rate_limit_known=True,
            health_check_available=True,
            warning_count=0,
            blocker_count=0,
        ),
        AdapterCertificationCandidate(
            candidate_id="demo.crypto.not_certified",
            name="Demo Crypto Not Certified Candidate",
            market_type="crypto",
            source_kind="vendor_export",
            qualification_level="research_required",
            qualification_score=0.48,
            qualified=False,
            readiness_score=0.45,
            required_umm_coverage_ratio=0.40,
            market_specific_coverage_ratio=0.42,
            optional_umm_coverage_ratio=0.20,
            warning_count=4,
            blocker_count=2,
        ),
    )


if __name__ == "__main__":
    snapshot = certify_adapters(demo_candidates(), certified_at=1760000000.0)
    print(snapshot_to_json(snapshot))
