from __future__ import annotations
from dataclasses import dataclass

from .oad_218_existing_ocl_state_hash_envelope import envelope
from qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity import (
    evaluate_learning_maturity,
    verify_ocl_022_learning_confidence_evidence_maturity,
)
from qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance import (
    evaluate_meta_learning_performance,
    verify_ocl_023_meta_learning_performance_evaluation,
)
from qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight import (
    build_adaptive_learning_weight,
    verify_ocl_024_adaptive_learning_weight_model,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class MaturityAdaptiveResolution:
    maturity:object
    adaptive_weight:object
    maturity_state_hash:str
    adaptive_weight_state_hash:str
    frozen_contracts_verified:bool
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def verify_frozen_maturity_adaptive_contracts():
    return bool(
        verify_ocl_022_learning_confidence_evidence_maturity()
        and verify_ocl_023_meta_learning_performance_evaluation()
        and verify_ocl_024_adaptive_learning_weight_model()
    )

def resolve_maturity_adaptive_state(
    evidence_count,
    independent_sources,
    consistency,
    contradiction_rate,
    calibration_quality,
    performance_history,
):
    if not verify_frozen_maturity_adaptive_contracts():
        raise RuntimeError("Frozen OCL-022/OCL-023/OCL-024 contract verification failed")

    maturity=evaluate_learning_maturity(
        int(evidence_count),
        int(independent_sources),
        float(consistency),
        float(contradiction_rate),
        float(calibration_quality),
    )

    performance=evaluate_meta_learning_performance(
        "crypto_verified_learning",
        tuple(float(x) for x in performance_history),
    )

    weight=build_adaptive_learning_weight(
        performance,
        1.0,
        maturity.maturity_score,
    )

    return MaturityAdaptiveResolution(
        maturity,
        weight,
        envelope("maturity",maturity).state_hash,
        envelope("adaptive_weight",weight).state_hash,
        True,
        False,
        False,
        False,
    )
