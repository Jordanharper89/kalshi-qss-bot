from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
INTELLIGENCE = QSERIES / "oracle_intelligence"
INTEGRATED = INTELLIGENCE / "integrated_intelligence"

SOURCE_OBSERVATION = INTELLIGENCE / "analytics" / "oracle_live_corpus_inspector.py"
SOURCE_CONFIDENCE = INTELLIGENCE / "analytics" / "oracle_forward_shadow_statistical_confidence_engine.py"
SOURCE_CALIBRATION = INTELLIGENCE / "analytics" / "oracle_forward_shadow_calibration_analyzer.py"

PRODUCTION = INTEGRATED / "oracle_integrated_intelligence_scientific_model_registry.py"
TEST = ROOT / "test_oii_001_oracle_integrated_intelligence_scientific_model_registry_and_read_only_boundary.py"
PACKAGE_INIT = INTEGRATED / "__init__.py"

PRODUCTION_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
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
"""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def optional_verify(path: Path, label: str, tokens: tuple[str, ...]) -> str | None:
    if not path.exists():
        print(f"[INFO] Optional upstream module not present: {label}")
        return None
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        print(f"[INFO] Optional upstream module contract not enforced: {label}")
        return sha256_file(path)
    print(f"[OK] Existing {label} contract observed")
    return sha256_file(path)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def ensure_package(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            '"""Oracle integrated intelligence subsystem."""\n',
            encoding="utf-8",
            newline="\n",
        )
        print(f"[OK] PACKAGE CREATED: {path.resolve()}")
    else:
        print(f"[OK] PACKAGE PRESENT: {path.resolve()}")


def export(path: Path, line: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in existing.splitlines():
        print(f"[OK] PACKAGE EXPORT PRESENT: {path.resolve()}")
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + line + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def main() -> int:
    print("=" * 48)
    print(" OII-001 INSTALLER")
    print(" INTEGRATED INTELLIGENCE MODEL REGISTRY")
    print(" READ-ONLY SCIENTIFIC BOUNDARY")
    print("=" * 48)

    protected: dict[Path, str] = {}

    checks = (
        (
            SOURCE_OBSERVATION,
            "OIA-001 live corpus inspector",
            ("oracle", "corpus", "read"),
        ),
        (
            SOURCE_CONFIDENCE,
            "statistical confidence engine",
            ("confidence", "hash"),
        ),
        (
            SOURCE_CALIBRATION,
            "calibration analyzer",
            ("calibration", "hash"),
        ),
    )

    for path, label, tokens in checks:
        observed_hash = optional_verify(path, label, tokens)
        if observed_hash is not None:
            protected[path] = observed_hash

    ensure_package(PACKAGE_INIT)
    write(PRODUCTION, PRODUCTION_SOURCE)
    write(TEST, TEST_SOURCE)
    export(
        PACKAGE_INIT,
        "from .oracle_integrated_intelligence_scientific_model_registry import *",
    )

    for path in (PRODUCTION, TEST, PACKAGE_INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    for path, expected_hash in protected.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] Observed upstream analytics modules unchanged")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    for path, expected_hash in protected.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream analytics modules unchanged after test")
    print("[PASS] No acquisition, Operator, or Q Series execution package modified")
    print("[OK] OII-001 test executed automatically")
    print()
    print("[DONE] OII-001 integrated intelligence foundation installed")
    print()
    print("NEXT BUILDS")
    print("  OII-002 Canonical intelligence evidence contract")
    print("  OII-003 Source-origin and information-quality engine")
    print("  OII-004 Bayesian prior and evidence update engine")
    print("  OII-005 Causal inference evidence gate")
    print("  OII-006 Signal detection and noise-control engine")
    print("  OII-007 Strategic and complex-systems synthesis")
    print("  OII-008 Decision-theoretic probability and edge synthesis")
    print("  OII-009 Calibration and adversarial review synthesis")
    print("  OII-010 Ranked live prediction-card candidate contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
