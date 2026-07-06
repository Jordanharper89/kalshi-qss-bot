
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
