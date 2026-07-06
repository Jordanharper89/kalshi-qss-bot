
from qseries_v2.oracle_intelligence.universal_market_adapter_certification_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterCertificationCandidate,
    UniversalMarketAdapterCertificationEngine,
    architecture_contract,
    candidate_from_qualification_decision,
    certify_adapters,
    demo_candidates,
    snapshot_to_json,
)


def test_certification_snapshot_contract():
    snapshot = certify_adapters(demo_candidates(), certified_at=1760000000.0)

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.decision_count == 2
    assert snapshot.certified_count == 1
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert snapshot.replay_hash


def test_certified_candidate_passes_core_gates():
    snapshot = certify_adapters(demo_candidates(), certified_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.certified is True
    assert decision.certification_level == "certified_for_registry_promotion"
    assert decision.gates["read_only_boundary_certified"] is True
    assert decision.gates["q_series_execution_boundary_certified"] is True
    assert decision.gates["universal_market_model_certified"] is True
    assert decision.gates["qualification_status_certified"] is True
    assert decision.gates["schema_contract_certified"] is True
    assert decision.explanation["q_series_boundary"] == "Q Series remains the sole execution owner."


def test_uncertified_candidate_has_blockers():
    weak = AdapterCertificationCandidate(
        candidate_id="weak.adapter",
        name="Weak Adapter Candidate",
        market_type="news",
        source_kind="manual_note",
        qualification_level="not_qualified",
        qualification_score=0.25,
        qualified=False,
        readiness_score=0.25,
        required_umm_coverage_ratio=0.20,
        market_specific_coverage_ratio=0.20,
        warning_count=6,
        blocker_count=3,
        read_only=True,
        execution_owner=Q_SERIES_EXECUTION_OWNER,
    )

    snapshot = certify_adapters([weak], certified_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.certified is False
    assert decision.certification_level == "not_certified"
    assert "universal_market_model_certified" in decision.blockers
    assert "qualification_status_certified" in decision.blockers
    assert "schema_contract_certified" in decision.blockers


def test_candidate_from_qualification_decision_mapping():
    qualification_decision = {
        "candidate": {
            "candidate_id": "qualified.weather",
            "name": "Qualified Weather Candidate",
            "market_type": "weather",
            "source_kind": "registry_item",
            "readiness_score": 0.93,
            "required_umm_coverage_ratio": 1.0,
            "market_specific_coverage_ratio": 0.90,
            "optional_umm_coverage_ratio": 0.70,
            "historical_available": True,
            "terms_known": True,
            "rate_limit_known": True,
            "health_check_available": True,
            "replay_key": "weather-replay",
            "evidence": {"fixture": True},
        },
        "qualified": True,
        "qualification_level": "qualified_for_registry_review",
        "score": 0.91,
        "explanation": {"summary": "qualified"},
        "telemetry": {
            "qualified": True,
            "qualification_level": "qualified_for_registry_review",
            "score": 0.91,
            "warning_count": 0,
            "blocker_count": 0,
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
        },
        "replay_hash": "qualification-replay-hash",
        "warnings": [],
        "blockers": [],
    }

    candidate = candidate_from_qualification_decision(qualification_decision)
    snapshot = certify_adapters([candidate], certified_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert candidate.candidate_id == "qualified.weather"
    assert decision.certified is True
    assert decision.gates["replay_evidence_certified"] is True
    assert decision.gates["governance_metadata_certified"] is True


def test_engine_history_and_json():
    engine = UniversalMarketAdapterCertificationEngine()
    snapshot = engine.certify(demo_candidates(), certified_at=1760000000.0)

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Certification Engine" in text
    assert "read_only" in text


def test_architecture_contract():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["adapter_certification_ready"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_certification_snapshot_contract()
    test_certified_candidate_passes_core_gates()
    test_uncertified_candidate_has_blockers()
    test_candidate_from_qualification_decision_mapping()
    test_engine_history_and_json()
    test_architecture_contract()
    print("[PASS] OI-178 Universal Market Adapter Certification Engine")
    print(certify_adapters(demo_candidates(), certified_at=1760000000.0).to_dict())
