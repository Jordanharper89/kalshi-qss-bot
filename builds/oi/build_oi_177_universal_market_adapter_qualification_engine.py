from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
MODULE_PATH = MODULE_DIR / "universal_market_adapter_qualification_engine.py"
TEST_PATH = ROOT / "test_oi_177_universal_market_adapter_qualification_engine.py"
INIT_PATH = MODULE_DIR / "__init__.py"

MODULE_CODE = r'''
"""
OI-177 — Oracle Universal Market Adapter Qualification Engine

Read-only qualification layer for Universal Market Adapter candidates.

This engine consumes adapter discovery-like records, evaluates institutional
qualification gates, produces explainable qualification decisions, and emits
replayable telemetry. Oracle remains intelligence-only. Q Series remains the
sole execution owner.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


ENGINE_ID = "oi.177.universal_market_adapter_qualification"
ENGINE_NAME = "Oracle Universal Market Adapter Qualification Engine"
ENGINE_VERSION = "1.0.0"
ARCHITECTURE_ROLE = "read_only_adapter_qualification"
Q_SERIES_EXECUTION_OWNER = "qseries.execution"

READ_ONLY_GUARDRAILS = (
    "Oracle never executes trades.",
    "Oracle never manages positions.",
    "Oracle never submits orders.",
    "Oracle never routes orders.",
    "Oracle never signs transactions.",
    "Q Series is the only execution engine.",
)

QUALIFICATION_GATES = (
    "read_only_safe",
    "umm_compatible",
    "schema_sufficient",
    "terms_known",
    "rate_limit_known",
    "health_check_available",
    "historical_or_replay_ready",
    "telemetry_ready",
    "explainability_ready",
)


@dataclass(frozen=True)
class AdapterQualificationCandidate:
    candidate_id: str
    name: str
    market_type: str
    source_kind: str
    readiness_score: float
    classification: str
    required_umm_coverage_ratio: float
    market_specific_coverage_ratio: float
    optional_umm_coverage_ratio: float = 0.0
    warning_count: int = 0
    terms_known: bool = False
    rate_limit_known: bool = False
    health_check_available: bool = False
    historical_available: bool = False
    replay_key: Optional[str] = None
    evidence: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True
    execution_owner: str = Q_SERIES_EXECUTION_OWNER

    def normalized(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "name": self.name,
            "market_type": normalize_market_type(self.market_type),
            "source_kind": self.source_kind,
            "readiness_score": clamp(self.readiness_score),
            "classification": self.classification,
            "required_umm_coverage_ratio": clamp(self.required_umm_coverage_ratio),
            "market_specific_coverage_ratio": clamp(self.market_specific_coverage_ratio),
            "optional_umm_coverage_ratio": clamp(self.optional_umm_coverage_ratio),
            "warning_count": max(0, int(self.warning_count)),
            "terms_known": bool(self.terms_known),
            "rate_limit_known": bool(self.rate_limit_known),
            "health_check_available": bool(self.health_check_available),
            "historical_available": bool(self.historical_available),
            "replay_key": self.replay_key,
            "evidence": dict(self.evidence),
            "read_only": bool(self.read_only),
            "execution_owner": self.execution_owner,
        }


@dataclass(frozen=True)
class AdapterQualificationDecision:
    candidate: AdapterQualificationCandidate
    qualified: bool
    qualification_level: str
    score: float
    gates: Mapping[str, bool]
    blockers: Tuple[str, ...]
    warnings: Tuple[str, ...]
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate": self.candidate.normalized(),
            "qualified": self.qualified,
            "qualification_level": self.qualification_level,
            "score": self.score,
            "gates": dict(self.gates),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "replay_hash": self.replay_hash,
        }


@dataclass(frozen=True)
class AdapterQualificationSnapshot:
    engine_id: str
    engine_name: str
    engine_version: str
    created_at: float
    decision_count: int
    qualified_count: int
    decisions: Tuple[AdapterQualificationDecision, ...]
    architecture: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "decision_count": self.decision_count,
            "qualified_count": self.qualified_count,
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
        "guardrails": list(READ_ONLY_GUARDRAILS),
    }


def build_gates(candidate: AdapterQualificationCandidate) -> Dict[str, bool]:
    data = candidate.normalized()

    return {
        "read_only_safe": data["read_only"] is True and data["execution_owner"] == Q_SERIES_EXECUTION_OWNER,
        "umm_compatible": data["required_umm_coverage_ratio"] >= 0.80,
        "schema_sufficient": data["readiness_score"] >= 0.70 and data["classification"] in {
            "adapter_ready",
            "adapter_candidate",
            "qualified",
        },
        "terms_known": data["terms_known"],
        "rate_limit_known": data["rate_limit_known"],
        "health_check_available": data["health_check_available"],
        "historical_or_replay_ready": data["historical_available"] or bool(data["replay_key"]),
        "telemetry_ready": data["market_specific_coverage_ratio"] >= 0.60,
        "explainability_ready": data["warning_count"] <= 3,
    }


def score_candidate(candidate: AdapterQualificationCandidate, gates: Mapping[str, bool]) -> float:
    base = (
        candidate.normalized()["readiness_score"] * 0.35
        + candidate.normalized()["required_umm_coverage_ratio"] * 0.25
        + candidate.normalized()["market_specific_coverage_ratio"] * 0.20
        + candidate.normalized()["optional_umm_coverage_ratio"] * 0.10
        + (sum(1 for value in gates.values() if value) / len(gates)) * 0.10
    )
    penalty = min(0.20, max(0, int(candidate.warning_count)) * 0.025)
    return round(max(0.0, min(1.0, base - penalty)), 6)


def qualification_level(score: float, gates: Mapping[str, bool]) -> str:
    required_core = (
        gates.get("read_only_safe", False),
        gates.get("umm_compatible", False),
        gates.get("schema_sufficient", False),
    )

    if all(required_core) and score >= 0.88 and all(gates.values()):
        return "qualified_for_registry_review"
    if all(required_core) and score >= 0.74:
        return "qualified_with_conditions"
    if gates.get("read_only_safe", False) and score >= 0.55:
        return "research_required"
    return "not_qualified"


def qualify_candidate(
    candidate: AdapterQualificationCandidate,
    evaluated_at: Optional[float] = None,
) -> AdapterQualificationDecision:
    timestamp = float(evaluated_at if evaluated_at is not None else time.time())
    gates = build_gates(candidate)
    score = score_candidate(candidate, gates)
    level = qualification_level(score, gates)
    qualified = level in {"qualified_for_registry_review", "qualified_with_conditions"}

    blockers = tuple(name for name, passed in gates.items() if not passed and name in {
        "read_only_safe",
        "umm_compatible",
        "schema_sufficient",
    })

    warnings = tuple(name for name, passed in gates.items() if not passed and name not in blockers)

    explanation = {
        "summary": f"{candidate.name} received qualification level {level} with score {score:.3f}.",
        "qualified": qualified,
        "market_type": normalize_market_type(candidate.market_type),
        "source_kind": candidate.source_kind,
        "passed_gates": [name for name, passed in gates.items() if passed],
        "failed_gates": [name for name, passed in gates.items() if not passed],
        "blockers": list(blockers),
        "warnings": list(warnings),
        "read_only_statement": "Qualification is descriptive only and cannot execute, route, submit, or manage trades.",
        "q_series_boundary": "Q Series remains the sole execution owner.",
        "next_step": recommend_next_step(level),
    }

    telemetry = {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "architecture_role": ARCHITECTURE_ROLE,
        "candidate_id": candidate.candidate_id,
        "market_type": normalize_market_type(candidate.market_type),
        "qualification_level": level,
        "qualified": qualified,
        "score": score,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "evaluated_at": timestamp,
    }

    replay_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "candidate": candidate.normalized(),
        "gates": dict(gates),
        "score": score,
        "qualification_level": level,
        "qualified": qualified,
        "blockers": blockers,
        "warnings": warnings,
    })

    return AdapterQualificationDecision(
        candidate=candidate,
        qualified=qualified,
        qualification_level=level,
        score=score,
        gates=gates,
        blockers=blockers,
        warnings=warnings,
        explanation=explanation,
        telemetry=telemetry,
        replay_hash=replay_hash,
    )


def recommend_next_step(level: str) -> str:
    if level == "qualified_for_registry_review":
        return "Promote to adapter registry review with human approval and replay fixture validation."
    if level == "qualified_with_conditions":
        return "Resolve failed non-core gates before production adapter promotion."
    if level == "research_required":
        return "Collect missing documentation, health checks, replay evidence, and terms metadata."
    return "Do not promote. Core qualification gates failed."


def qualify_adapters(
    candidates: Iterable[AdapterQualificationCandidate],
    evaluated_at: Optional[float] = None,
) -> AdapterQualificationSnapshot:
    timestamp = float(evaluated_at if evaluated_at is not None else time.time())
    decisions = tuple(
        sorted(
            (qualify_candidate(candidate, evaluated_at=timestamp) for candidate in candidates),
            key=lambda decision: (-decision.score, decision.candidate.name.lower(), decision.candidate.candidate_id),
        )
    )

    architecture = architecture_contract()
    replay_hash = stable_hash({
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "created_at": timestamp,
        "decision_hashes": [decision.replay_hash for decision in decisions],
        "architecture": architecture,
    })

    return AdapterQualificationSnapshot(
        engine_id=ENGINE_ID,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        created_at=timestamp,
        decision_count=len(decisions),
        qualified_count=sum(1 for decision in decisions if decision.qualified),
        decisions=decisions,
        architecture=architecture,
        replay_hash=replay_hash,
    )


def candidate_from_discovery_result(result: Mapping[str, Any]) -> AdapterQualificationCandidate:
    source = result.get("source", {})
    telemetry = result.get("telemetry", {})
    evidence = result.get("evidence", {})

    signal_map = evidence.get("signal_map", {})
    return AdapterQualificationCandidate(
        candidate_id=str(source.get("source_id") or telemetry.get("source_id") or "unknown"),
        name=str(source.get("name") or source.get("source_id") or "Unknown Adapter Candidate"),
        market_type=str(source.get("market_type") or telemetry.get("market_type") or "unknown"),
        source_kind=str(source.get("source_kind") or telemetry.get("source_kind") or "unknown"),
        readiness_score=clamp(result.get("readiness_score", telemetry.get("readiness_score", 0.0))),
        classification=str(result.get("classification", telemetry.get("classification", "unknown"))),
        required_umm_coverage_ratio=clamp(telemetry.get("required_umm_coverage_ratio", coverage_ratio(evidence.get("required_umm_coverage", {})))),
        market_specific_coverage_ratio=clamp(telemetry.get("market_specific_coverage_ratio", coverage_ratio(evidence.get("market_specific_coverage", {})))),
        optional_umm_coverage_ratio=clamp(telemetry.get("optional_umm_coverage_ratio", coverage_ratio(evidence.get("optional_umm_coverage", {})))),
        warning_count=int(telemetry.get("warning_count", len(evidence.get("warnings", [])))),
        terms_known=bool(signal_map.get("terms_known", False)),
        rate_limit_known=bool(signal_map.get("rate_limit_known", False)),
        health_check_available=bool(signal_map.get("health_probe_available", False)),
        historical_available=bool(signal_map.get("historical_snapshots_available", False)),
        replay_key=result.get("replay_key"),
        evidence=evidence,
        read_only=bool(telemetry.get("read_only", True)),
        execution_owner=str(telemetry.get("execution_owner", Q_SERIES_EXECUTION_OWNER)),
    )


def coverage_ratio(coverage: Mapping[str, Any]) -> float:
    if not coverage:
        return 0.0
    return round(sum(1 for value in coverage.values() if bool(value)) / len(coverage), 6)


def qualify_discovery_snapshot(snapshot: Mapping[str, Any]) -> AdapterQualificationSnapshot:
    candidates = [candidate_from_discovery_result(result) for result in snapshot.get("results", [])]
    return qualify_adapters(candidates, evaluated_at=float(snapshot.get("created_at", time.time())))


def snapshot_to_json(snapshot: AdapterQualificationSnapshot, indent: int = 2) -> str:
    return json.dumps(snapshot.to_dict(), indent=indent, sort_keys=True, default=str)


class UniversalMarketAdapterQualificationEngine:
    def __init__(self) -> None:
        self._history = []

    def qualify(
        self,
        candidates: Iterable[AdapterQualificationCandidate],
        evaluated_at: Optional[float] = None,
    ) -> AdapterQualificationSnapshot:
        snapshot = qualify_adapters(candidates, evaluated_at=evaluated_at)
        self._history.append(snapshot)
        return snapshot

    def qualify_discovery_snapshot(self, snapshot: Mapping[str, Any]) -> AdapterQualificationSnapshot:
        qualified = qualify_discovery_snapshot(snapshot)
        self._history.append(qualified)
        return qualified

    def latest_snapshot(self) -> Optional[AdapterQualificationSnapshot]:
        return self._history[-1] if self._history else None

    def history(self) -> Tuple[AdapterQualificationSnapshot, ...]:
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


oracle_universal_market_adapter_qualification_engine = UniversalMarketAdapterQualificationEngine()
universal_market_adapter_qualification_engine = oracle_universal_market_adapter_qualification_engine


def demo_candidates() -> Tuple[AdapterQualificationCandidate, ...]:
    return (
        AdapterQualificationCandidate(
            candidate_id="demo.prediction.qualified",
            name="Demo Prediction Qualified Candidate",
            market_type="prediction_markets",
            source_kind="api_schema",
            readiness_score=0.96,
            classification="adapter_ready",
            required_umm_coverage_ratio=1.0,
            market_specific_coverage_ratio=1.0,
            optional_umm_coverage_ratio=0.72,
            warning_count=0,
            terms_known=True,
            rate_limit_known=True,
            health_check_available=True,
            historical_available=True,
            replay_key="demo-replay-key",
        ),
        AdapterQualificationCandidate(
            candidate_id="demo.crypto.research",
            name="Demo Crypto Research Candidate",
            market_type="crypto",
            source_kind="vendor_export",
            readiness_score=0.48,
            classification="not_ready",
            required_umm_coverage_ratio=0.40,
            market_specific_coverage_ratio=0.42,
            optional_umm_coverage_ratio=0.20,
            warning_count=4,
            terms_known=False,
            rate_limit_known=False,
            health_check_available=False,
            historical_available=False,
        ),
    )


if __name__ == "__main__":
    snapshot = qualify_adapters(demo_candidates(), evaluated_at=1760000000.0)
    print(snapshot_to_json(snapshot))
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_qualification_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterQualificationCandidate,
    UniversalMarketAdapterQualificationEngine,
    architecture_contract,
    candidate_from_discovery_result,
    demo_candidates,
    qualify_adapters,
    snapshot_to_json,
)


def test_qualification_snapshot_contract():
    snapshot = qualify_adapters(demo_candidates(), evaluated_at=1760000000.0)

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.decision_count == 2
    assert snapshot.qualified_count == 1
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert snapshot.replay_hash


def test_qualified_candidate_passes_core_gates():
    snapshot = qualify_adapters(demo_candidates(), evaluated_at=1760000000.0)
    qualified = snapshot.decisions[0]

    assert qualified.qualified is True
    assert qualified.qualification_level in {
        "qualified_for_registry_review",
        "qualified_with_conditions",
    }
    assert qualified.gates["read_only_safe"] is True
    assert qualified.gates["umm_compatible"] is True
    assert qualified.gates["schema_sufficient"] is True
    assert "Q Series remains the sole execution owner." == qualified.explanation["q_series_boundary"]


def test_unqualified_candidate_has_blockers():
    weak = AdapterQualificationCandidate(
        candidate_id="weak.news",
        name="Weak News Candidate",
        market_type="news",
        source_kind="manual_note",
        readiness_score=0.25,
        classification="not_ready",
        required_umm_coverage_ratio=0.20,
        market_specific_coverage_ratio=0.20,
        warning_count=8,
        terms_known=False,
        rate_limit_known=False,
        health_check_available=False,
        historical_available=False,
    )

    snapshot = qualify_adapters([weak], evaluated_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.qualified is False
    assert decision.qualification_level == "not_qualified"
    assert "umm_compatible" in decision.blockers
    assert "schema_sufficient" in decision.blockers


def test_candidate_from_discovery_result_mapping():
    discovery_result = {
        "source": {
            "source_id": "demo.discovery",
            "name": "Demo Discovery Source",
            "market_type": "weather",
            "source_kind": "registry_item",
        },
        "readiness_score": 0.91,
        "classification": "adapter_ready",
        "replay_key": "abc123",
        "evidence": {
            "signal_map": {
                "terms_known": True,
                "rate_limit_known": True,
                "health_probe_available": True,
                "historical_snapshots_available": True,
            },
            "required_umm_coverage": {"market_id": True, "market_type": True, "title": True, "status": True, "timestamp": True},
            "market_specific_coverage": {"event_id": True, "title": True, "timestamp": True},
            "optional_umm_coverage": {"source_url": True, "settlement_source": True},
            "warnings": [],
        },
        "telemetry": {
            "required_umm_coverage_ratio": 1.0,
            "market_specific_coverage_ratio": 1.0,
            "optional_umm_coverage_ratio": 1.0,
            "warning_count": 0,
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
        },
    }

    candidate = candidate_from_discovery_result(discovery_result)
    snapshot = qualify_adapters([candidate], evaluated_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert candidate.candidate_id == "demo.discovery"
    assert decision.qualified is True
    assert decision.gates["historical_or_replay_ready"] is True


def test_engine_history_and_json():
    engine = UniversalMarketAdapterQualificationEngine()
    snapshot = engine.qualify(demo_candidates(), evaluated_at=1760000000.0)

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Qualification Engine" in text
    assert "read_only" in text


def test_architecture_contract():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_qualification_snapshot_contract()
    test_qualified_candidate_passes_core_gates()
    test_unqualified_candidate_has_blockers()
    test_candidate_from_discovery_result_mapping()
    test_engine_history_and_json()
    test_architecture_contract()
    print("[PASS] OI-177 Universal Market Adapter Qualification Engine")
    print(qualify_adapters(demo_candidates(), evaluated_at=1760000000.0).to_dict())
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
        "from .universal_market_adapter_qualification_engine import "
        "UniversalMarketAdapterQualificationEngine, "
        "oracle_universal_market_adapter_qualification_engine, "
        "universal_market_adapter_qualification_engine\n"
    )

    additions = [
        "UniversalMarketAdapterQualificationEngine",
        "oracle_universal_market_adapter_qualification_engine",
        "universal_market_adapter_qualification_engine",
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
    print(" OI-177 INSTALLER")
    print(" Universal Market Adapter Qualification Engine")
    print("========================================")

    write_file(MODULE_PATH, MODULE_CODE)
    print(f"[OK] Wrote {MODULE_PATH}")

    write_file(TEST_PATH, TEST_CODE)
    print(f"[OK] Wrote {TEST_PATH}")

    update_init()
    print(f"[OK] Updated {INIT_PATH}")

    print()
    print("[DONE] OI-177 installed")
    print()
    print("Run:")
    print("py test_oi_177_universal_market_adapter_qualification_engine.py")


if __name__ == "__main__":
    main()