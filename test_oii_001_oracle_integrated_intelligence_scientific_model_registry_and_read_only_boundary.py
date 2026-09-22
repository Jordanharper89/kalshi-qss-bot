from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_scientific_model_registry import (
    BOUNDARY_TYPE,
    REGISTRY_STATUS,
    REGISTRY_TYPE,
    REQUIRED_MODEL_IDS,
    OracleIntegratedIntelligenceScientificModelRegistryBuilder,
    stable_hash,
)


def main() -> int:
    print("=" * 48)
    print(" OII-001 TEST")
    print(" INTEGRATED INTELLIGENCE MODEL REGISTRY")
    print(" READ-ONLY SCIENTIFIC BOUNDARY")
    print("=" * 48)

    builder = OracleIntegratedIntelligenceScientificModelRegistryBuilder()

    boundary = builder.boundary()
    assert boundary.boundary_type == BOUNDARY_TYPE
    assert boundary.canonical_observation_consumption_allowed
    assert boundary.analytics_read_consumption_allowed
    assert boundary.external_evidence_read_consumption_allowed
    assert boundary.model_inference_allowed
    assert boundary.probability_estimation_allowed
    assert boundary.confidence_estimation_allowed
    assert boundary.edge_estimation_allowed
    assert boundary.causal_claims_require_evidence
    assert boundary.source_origin_verification_required
    assert boundary.adversarial_review_required
    assert boundary.calibration_tracking_required
    assert boundary.human_review_supported
    assert boundary.boundary_hash == stable_hash(
        {
            key: value
            for key, value in boundary.__dict__.items()
            if key != "boundary_hash"
        }
    )

    forbidden_boundary = (
        boundary.publication_allowed,
        boundary.alerting_allowed,
        boundary.qseries_handoff_allowed,
        boundary.qseries_execution_allowed,
        boundary.qseries_execution_performed,
        boundary.order_creation_allowed,
        boundary.order_creation_performed,
        boundary.funds_movement_allowed,
        boundary.funds_movement_performed,
        boundary.portfolio_mutation_allowed,
        boundary.portfolio_mutation_performed,
    )
    assert not any(forbidden_boundary)

    first = builder.build()
    repeated = builder.build()

    assert first == repeated
    assert first.registry_status == REGISTRY_STATUS
    assert first.registry_type == REGISTRY_TYPE
    assert first.model_ids == REQUIRED_MODEL_IDS
    assert first.model_count == 9
    assert first.registry_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "registry_hash"
        }
    )

    assert first.all_required_models_present
    assert first.deterministic_registry_verified
    assert first.immutable_registry_verified
    assert first.replayable_registry_verified
    assert first.explainable_models_required
    assert first.calibrated_models_required
    assert first.source_lineage_required
    assert first.uncertainty_required
    assert first.adversarial_review_required
    assert first.read_only_boundary_verified

    assert not first.qseries_execution_allowed
    assert not first.order_creation_allowed
    assert not first.funds_movement_allowed
    assert not first.portfolio_mutation_allowed

    for model in first.models:
        assert model.contract_hash == stable_hash(
            {
                key: value
                for key, value in model.__dict__.items()
                if key != "contract_hash"
            }
        )
        assert model.deterministic_required
        assert model.immutable_required
        assert model.replayable_required
        assert model.explainable_required
        assert model.calibration_required
        assert model.source_lineage_required
        assert model.uncertainty_required
        assert model.adversarial_review_required
        assert model.read_only_required
        assert not model.execution_allowed
        assert not model.order_creation_allowed
        assert not model.funds_movement_allowed
        assert not model.portfolio_mutation_allowed
        assert "trade_instruction" in model.prohibited_outputs
        assert "order_payload" in model.prohibited_outputs
        assert "execution_authorization" in model.prohibited_outputs

    print("[PASS] All nine approved scientific disciplines registered")
    print("[PASS] Bayesian inference contract installed")
    print("[PASS] Information theory and source-origin contract installed")
    print("[PASS] Causal inference contract installed")
    print("[PASS] Decision theory contract installed")
    print("[PASS] Game theory contract installed")
    print("[PASS] Complex systems and emergence contract installed")
    print("[PASS] Signal detection theory contract installed")
    print("[PASS] Calibration science contract installed")
    print("[PASS] Adversarial epistemology contract installed")
    print("[PASS] Deterministic immutable registry verified")
    print("[PASS] Explainability, uncertainty, lineage, and calibration required")
    print("[PASS] Read-only intelligence boundary established")
    print("[PASS] Publication and alerting remain disabled")
    print("[PASS] Q Series execution remains disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
