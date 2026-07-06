
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
