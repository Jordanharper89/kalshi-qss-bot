
from qseries_v2.oracle_intelligence.universal_market_adapter_promotion_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterPromotionCandidate,
    UniversalMarketAdapterPromotionEngine,
    architecture_contract,
    candidate_from_certification_decision,
    demo_candidates,
    promote_adapters,
    snapshot_to_json,
)


def test_promotion_snapshot_contract():
    snapshot = promote_adapters(demo_candidates(), promoted_at=1760000000.0)

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.decision_count == 2
    assert snapshot.promoted_count == 1
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert snapshot.replay_hash


def test_promoted_candidate_passes_core_gates():
    snapshot = promote_adapters(demo_candidates(), promoted_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.promoted is True
    assert decision.promotion_level == "promoted_to_registry_ready"
    assert decision.gates["read_only_boundary_promoted"] is True
    assert decision.gates["q_series_execution_boundary_promoted"] is True
    assert decision.gates["certification_status_promoted"] is True
    assert decision.gates["registry_metadata_promoted"] is True
    assert decision.explanation["q_series_boundary"] == "Q Series remains the sole execution owner."


def test_unpromoted_candidate_has_blockers():
    weak = AdapterPromotionCandidate(
        candidate_id="weak.adapter",
        name="Weak Adapter Candidate",
        market_type="news",
        source_kind="manual_note",
        certification_level="not_certified",
        certification_score=0.25,
        certified=False,
        certification_hash=None,
        replay_hash=None,
        registry_namespace=None,
        registry_version=None,
        registry_owner=None,
        explanation_ready=False,
        telemetry_ready=False,
        rollback_plan_ready=False,
        human_review_status="pending",
        architecture_registry_ready=False,
        warning_count=6,
        blocker_count=3,
        read_only=True,
        execution_owner=Q_SERIES_EXECUTION_OWNER,
    )

    snapshot = promote_adapters([weak], promoted_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.promoted is False
    assert decision.promotion_level == "not_promoted"
    assert "certification_status_promoted" in decision.blockers
    assert "registry_metadata_promoted" in decision.blockers


def test_candidate_from_certification_decision_mapping():
    certification_decision = {
        "candidate": {
            "candidate_id": "certified.weather",
            "name": "Certified Weather Candidate",
            "market_type": "weather",
            "source_kind": "registry_item",
            "evidence": {"fixture": True},
        },
        "certified": True,
        "certification_level": "certified_for_registry_promotion",
        "certification_score": 0.94,
        "certification_hash": "weather-certification-hash",
        "explanation": {"summary": "certified"},
        "telemetry": {
            "certified": True,
            "certification_level": "certified_for_registry_promotion",
            "certification_score": 0.94,
            "warning_count": 0,
            "blocker_count": 0,
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
        },
        "warnings": [],
        "blockers": [],
    }

    candidate = candidate_from_certification_decision(certification_decision)
    snapshot = promote_adapters([candidate], promoted_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert candidate.candidate_id == "certified.weather"
    assert decision.promoted is True
    assert decision.gates["registry_metadata_promoted"] is True
    assert decision.gates["human_review_promoted"] is True


def test_engine_history_and_json():
    engine = UniversalMarketAdapterPromotionEngine()
    snapshot = engine.promote(demo_candidates(), promoted_at=1760000000.0)

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Promotion Engine" in text
    assert "read_only" in text


def test_architecture_contract():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["adapter_promotion_ready"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_promotion_snapshot_contract()
    test_promoted_candidate_passes_core_gates()
    test_unpromoted_candidate_has_blockers()
    test_candidate_from_certification_decision_mapping()
    test_engine_history_and_json()
    test_architecture_contract()
    print("[PASS] OI-179 Universal Market Adapter Promotion Engine")
    print(promote_adapters(demo_candidates(), promoted_at=1760000000.0).to_dict())
