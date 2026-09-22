from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA_VERSION = "OII-001"
ENGINE_ID = "OII-001"
POLICY_ID = "oracle.integrated-intelligence.scientific-model-registry.v1"
REGISTRY_STATUS = "oracle_integrated_intelligence_scientific_model_registry_active"
REGISTRY_TYPE = "immutable_read_only_scientific_intelligence_model_registry"
BOUNDARY_TYPE = "oracle_integrated_intelligence_read_only_boundary"

MODEL_BAYESIAN_INFERENCE = "bayesian_inference"
MODEL_INFORMATION_THEORY_SOURCE_ORIGIN = "information_theory_and_source_origin"
MODEL_CAUSAL_INFERENCE = "causal_inference"
MODEL_DECISION_THEORY = "decision_theory"
MODEL_GAME_THEORY = "game_theory"
MODEL_COMPLEX_SYSTEMS_EMERGENCE = "complex_systems_and_emergence"
MODEL_SIGNAL_DETECTION = "signal_detection_theory"
MODEL_CALIBRATION_SCIENCE = "calibration_science"
MODEL_ADVERSARIAL_EPISTEMOLOGY = "adversarial_epistemology"

REQUIRED_MODEL_IDS = (
    MODEL_BAYESIAN_INFERENCE,
    MODEL_INFORMATION_THEORY_SOURCE_ORIGIN,
    MODEL_CAUSAL_INFERENCE,
    MODEL_DECISION_THEORY,
    MODEL_GAME_THEORY,
    MODEL_COMPLEX_SYSTEMS_EMERGENCE,
    MODEL_SIGNAL_DETECTION,
    MODEL_CALIBRATION_SCIENCE,
    MODEL_ADVERSARIAL_EPISTEMOLOGY,
)


class OracleIntegratedIntelligenceModelRegistryInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleIntegratedIntelligenceModelRegistryInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntegratedIntelligenceModelRegistryInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class OracleScientificModelContract:
    model_id: str
    model_name: str
    model_family: str
    purpose: str
    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    prohibited_outputs: tuple[str, ...]
    deterministic_required: bool
    immutable_required: bool
    replayable_required: bool
    explainable_required: bool
    calibration_required: bool
    source_lineage_required: bool
    uncertainty_required: bool
    adversarial_review_required: bool
    read_only_required: bool
    execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    contract_hash: str


@dataclass(frozen=True)
class OracleIntegratedIntelligenceReadOnlyBoundary:
    boundary_type: str
    canonical_observation_consumption_allowed: bool
    analytics_read_consumption_allowed: bool
    external_evidence_read_consumption_allowed: bool
    model_inference_allowed: bool
    probability_estimation_allowed: bool
    confidence_estimation_allowed: bool
    edge_estimation_allowed: bool
    causal_claims_require_evidence: bool
    source_origin_verification_required: bool
    adversarial_review_required: bool
    calibration_tracking_required: bool
    human_review_supported: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    order_creation_allowed: bool
    order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    boundary_hash: str


@dataclass(frozen=True)
class OracleIntegratedIntelligenceScientificModelRegistry:
    registry_id: str
    registry_status: str
    registry_type: str
    schema_version: str
    engine_id: str
    policy_id: str
    model_ids: tuple[str, ...]
    models: tuple[OracleScientificModelContract, ...]
    model_count: int
    all_required_models_present: bool
    deterministic_registry_verified: bool
    immutable_registry_verified: bool
    replayable_registry_verified: bool
    explainable_models_required: bool
    calibrated_models_required: bool
    source_lineage_required: bool
    uncertainty_required: bool
    adversarial_review_required: bool
    read_only_boundary_verified: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    registry_hash: str


def _contract(
    *,
    model_id: str,
    model_name: str,
    model_family: str,
    purpose: str,
    required_inputs: tuple[str, ...],
    required_outputs: tuple[str, ...],
) -> OracleScientificModelContract:
    prohibited_outputs = (
        "trade_instruction",
        "order_payload",
        "funds_transfer_instruction",
        "portfolio_mutation_instruction",
        "execution_authorization",
    )
    body = {
        "model_id": model_id,
        "model_name": model_name,
        "model_family": model_family,
        "purpose": purpose,
        "required_inputs": required_inputs,
        "required_outputs": required_outputs,
        "prohibited_outputs": prohibited_outputs,
        "deterministic_required": True,
        "immutable_required": True,
        "replayable_required": True,
        "explainable_required": True,
        "calibration_required": True,
        "source_lineage_required": True,
        "uncertainty_required": True,
        "adversarial_review_required": True,
        "read_only_required": True,
        "execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
    }
    return OracleScientificModelContract(
        **body,
        contract_hash=stable_hash(body),
    )


class OracleIntegratedIntelligenceScientificModelRegistryBuilder:
    def boundary(self) -> OracleIntegratedIntelligenceReadOnlyBoundary:
        body = {
            "boundary_type": BOUNDARY_TYPE,
            "canonical_observation_consumption_allowed": True,
            "analytics_read_consumption_allowed": True,
            "external_evidence_read_consumption_allowed": True,
            "model_inference_allowed": True,
            "probability_estimation_allowed": True,
            "confidence_estimation_allowed": True,
            "edge_estimation_allowed": True,
            "causal_claims_require_evidence": True,
            "source_origin_verification_required": True,
            "adversarial_review_required": True,
            "calibration_tracking_required": True,
            "human_review_supported": True,
            "publication_allowed": False,
            "alerting_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "order_creation_allowed": False,
            "order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
        }
        return OracleIntegratedIntelligenceReadOnlyBoundary(
            **body,
            boundary_hash=stable_hash(body),
        )

    def build(self) -> OracleIntegratedIntelligenceScientificModelRegistry:
        models = (
            _contract(
                model_id=MODEL_BAYESIAN_INFERENCE,
                model_name="Bayesian Inference",
                model_family="probabilistic_inference",
                purpose=(
                    "Update prior probabilities with new evidence while preserving "
                    "explicit uncertainty and evidence lineage."
                ),
                required_inputs=(
                    "prior_probability",
                    "evidence_likelihood",
                    "evidence_reliability",
                    "source_lineage",
                ),
                required_outputs=(
                    "posterior_probability",
                    "posterior_uncertainty",
                    "bayes_factor",
                    "evidence_contribution",
                ),
            ),
            _contract(
                model_id=MODEL_INFORMATION_THEORY_SOURCE_ORIGIN,
                model_name="Information Theory and Source Origin",
                model_family="information_quality",
                purpose=(
                    "Measure information gain, redundancy, novelty, entropy, and "
                    "source independence."
                ),
                required_inputs=(
                    "evidence_items",
                    "source_origins",
                    "source_relationships",
                    "prior_information_state",
                ),
                required_outputs=(
                    "information_gain",
                    "entropy_reduction",
                    "redundancy_score",
                    "source_independence_score",
                ),
            ),
            _contract(
                model_id=MODEL_CAUSAL_INFERENCE,
                model_name="Causal Inference",
                model_family="causal_reasoning",
                purpose=(
                    "Separate correlation from supported causal mechanisms and "
                    "identify confounding, mediation, and intervention effects."
                ),
                required_inputs=(
                    "candidate_causes",
                    "candidate_effects",
                    "confounders",
                    "temporal_ordering",
                    "causal_evidence",
                ),
                required_outputs=(
                    "causal_support_score",
                    "confounding_risk",
                    "counterfactual_estimate",
                    "causal_claim_limits",
                ),
            ),
            _contract(
                model_id=MODEL_DECISION_THEORY,
                model_name="Decision Theory",
                model_family="decision_quality",
                purpose=(
                    "Evaluate expected utility, asymmetric payoff, uncertainty, "
                    "opportunity cost, and abstention value without executing."
                ),
                required_inputs=(
                    "probability_distribution",
                    "market_prices",
                    "payoff_structure",
                    "uncertainty",
                    "risk_constraints",
                ),
                required_outputs=(
                    "expected_value",
                    "expected_utility",
                    "value_of_information",
                    "abstention_value",
                ),
            ),
            _contract(
                model_id=MODEL_GAME_THEORY,
                model_name="Game Theory",
                model_family="strategic_interaction",
                purpose=(
                    "Model strategic participants, incentives, signaling, crowd "
                    "behavior, and equilibrium-sensitive market effects."
                ),
                required_inputs=(
                    "participant_classes",
                    "incentives",
                    "observable_actions",
                    "information_asymmetries",
                    "market_microstructure",
                ),
                required_outputs=(
                    "strategic_pressure_score",
                    "equilibrium_risk",
                    "signaling_interpretation",
                    "crowd_behavior_assessment",
                ),
            ),
            _contract(
                model_id=MODEL_COMPLEX_SYSTEMS_EMERGENCE,
                model_name="Complex Systems and Emergence",
                model_family="complex_adaptive_systems",
                purpose=(
                    "Detect nonlinear interactions, regime shifts, cascades, "
                    "feedback loops, and emergent cross-market behavior."
                ),
                required_inputs=(
                    "market_network",
                    "cross_market_dependencies",
                    "time_series_state",
                    "feedback_signals",
                ),
                required_outputs=(
                    "regime_state",
                    "cascade_risk",
                    "feedback_loop_score",
                    "emergence_signal",
                ),
            ),
            _contract(
                model_id=MODEL_SIGNAL_DETECTION,
                model_name="Signal Detection Theory",
                model_family="signal_quality",
                purpose=(
                    "Separate actionable signal from noise while controlling false "
                    "positives, misses, and threshold sensitivity."
                ),
                required_inputs=(
                    "candidate_signal",
                    "noise_model",
                    "base_rate",
                    "decision_threshold",
                ),
                required_outputs=(
                    "signal_strength",
                    "false_positive_risk",
                    "miss_risk",
                    "detection_confidence",
                ),
            ),
            _contract(
                model_id=MODEL_CALIBRATION_SCIENCE,
                model_name="Calibration Science",
                model_family="forecast_calibration",
                purpose=(
                    "Track whether forecast probabilities match observed outcomes "
                    "across time, categories, and confidence bands."
                ),
                required_inputs=(
                    "forecast_probabilities",
                    "observed_outcomes",
                    "forecast_categories",
                    "confidence_bands",
                ),
                required_outputs=(
                    "calibration_score",
                    "reliability_curve",
                    "brier_score",
                    "confidence_adjustment",
                ),
            ),
            _contract(
                model_id=MODEL_ADVERSARIAL_EPISTEMOLOGY,
                model_name="Adversarial Epistemology",
                model_family="adversarial_reasoning",
                purpose=(
                    "Challenge assumptions, detect deception, source capture, "
                    "narrative manipulation, motivated reasoning, and model fragility."
                ),
                required_inputs=(
                    "claims",
                    "supporting_evidence",
                    "source_incentives",
                    "contradictory_evidence",
                    "model_assumptions",
                ),
                required_outputs=(
                    "adversarial_risk_score",
                    "assumption_fragility",
                    "deception_risk",
                    "contradiction_summary",
                ),
            ),
        )

        model_ids = tuple(model.model_id for model in models)
        if model_ids != REQUIRED_MODEL_IDS:
            raise OracleIntegratedIntelligenceModelRegistryInvariantError(
                "required model order or membership mismatch"
            )
        if len(set(model_ids)) != len(model_ids):
            raise OracleIntegratedIntelligenceModelRegistryInvariantError(
                "duplicate model id detected"
            )
        if any(
            model.execution_allowed
            or model.order_creation_allowed
            or model.funds_movement_allowed
            or model.portfolio_mutation_allowed
            for model in models
        ):
            raise OracleIntegratedIntelligenceModelRegistryInvariantError(
                "execution-capable scientific model detected"
            )

        registry_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "policy_id": POLICY_ID,
                "model_ids": model_ids,
                "model_contract_hashes": tuple(model.contract_hash for model in models),
                "registry_type": REGISTRY_TYPE,
            }
        )

        body = {
            "registry_id": registry_id,
            "registry_status": REGISTRY_STATUS,
            "registry_type": REGISTRY_TYPE,
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "policy_id": POLICY_ID,
            "model_ids": model_ids,
            "models": models,
            "model_count": len(models),
            "all_required_models_present": True,
            "deterministic_registry_verified": True,
            "immutable_registry_verified": True,
            "replayable_registry_verified": True,
            "explainable_models_required": True,
            "calibrated_models_required": True,
            "source_lineage_required": True,
            "uncertainty_required": True,
            "adversarial_review_required": True,
            "read_only_boundary_verified": True,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }

        return OracleIntegratedIntelligenceScientificModelRegistry(
            **body,
            registry_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "REGISTRY_STATUS",
    "REGISTRY_TYPE",
    "BOUNDARY_TYPE",
    "REQUIRED_MODEL_IDS",
    "MODEL_BAYESIAN_INFERENCE",
    "MODEL_INFORMATION_THEORY_SOURCE_ORIGIN",
    "MODEL_CAUSAL_INFERENCE",
    "MODEL_DECISION_THEORY",
    "MODEL_GAME_THEORY",
    "MODEL_COMPLEX_SYSTEMS_EMERGENCE",
    "MODEL_SIGNAL_DETECTION",
    "MODEL_CALIBRATION_SCIENCE",
    "MODEL_ADVERSARIAL_EPISTEMOLOGY",
    "OracleScientificModelContract",
    "OracleIntegratedIntelligenceReadOnlyBoundary",
    "OracleIntegratedIntelligenceScientificModelRegistry",
    "OracleIntegratedIntelligenceScientificModelRegistryBuilder",
    "OracleIntegratedIntelligenceModelRegistryInvariantError",
    "stable_hash",
]
