from __future__ import annotations
from dataclasses import dataclass
from .oad_222_crypto_physical_calibration_state_materialization import materialize_physical_calibration_state
from .oad_223_crypto_physical_source_reliability_state_materialization import materialize_physical_source_reliability_state
from .oad_224_crypto_physical_market_behavior_state_materialization import materialize_physical_market_behavior_state
from .oad_225_crypto_physical_maturity_state_materialization import materialize_physical_maturity_state
from .oad_221_crypto_scientific_reasoning_admission_physical_certification import certify_crypto_scientific_reasoning_admission
from qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance import verify_ocl_023_meta_learning_performance_evaluation
from qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight import verify_ocl_024_adaptive_learning_weight_model
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class AdaptiveAndReadmission:
    calibration_state:str
    source_reliability_state:str
    market_behavior_state_hash:str|None
    maturity_state_hash:str|None
    adaptive_weight_state_hash:str|None
    adaptive_state:str
    supplied_hashes:tuple[str,...]
    missing_state_hashes:tuple[str,...]
    admission_state:str
    handoff_verified:bool
    physical_ready:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False
def run_physical_adaptive_and_ocl029_readmission(root=None):
    if not verify_ocl_023_meta_learning_performance_evaluation() or not verify_ocl_024_adaptive_learning_weight_model():
        raise RuntimeError("Frozen OCL-023/OCL-024 verifier failed")
    cal=materialize_physical_calibration_state(root);rel=materialize_physical_source_reliability_state(root)
    mb=materialize_physical_market_behavior_state(root);mat=materialize_physical_maturity_state(root)
    adaptive_hash=None
    adaptive_state="HOLD_META_LEARNING_PERFORMANCE_DELTAS_REQUIRED"
    hashes={}
    if mb.market_behavior_state_hash:hashes["market_behavior_state_hash"]=mb.market_behavior_state_hash
    if mat.maturity_state_hash:hashes["maturity_state_hash"]=mat.maturity_state_hash
    admission=certify_crypto_scientific_reasoning_admission(certified_state_hashes=hashes)
    return AdaptiveAndReadmission(cal.state,rel.state,mb.market_behavior_state_hash,mat.maturity_state_hash,adaptive_hash,adaptive_state,tuple(sorted(hashes)),tuple(admission.missing_state_hashes),admission.state,bool(admission.handoff_verified))
