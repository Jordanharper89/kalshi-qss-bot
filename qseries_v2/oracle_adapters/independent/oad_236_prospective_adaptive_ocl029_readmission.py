from __future__ import annotations
from dataclasses import dataclass
from .oad_218_existing_ocl_state_hash_envelope import envelope
from .oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases
from .oad_235_prospective_calibration_source_reliability_materialization import materialize_prospective_calibration_source_reliability
from .oad_228_snapshot_market_behavior_maturity_materialization import materialize_snapshot_behavior_maturity
from .oad_229_crypto_physical_entity_relationship_materialization import materialize_entity_relationship_state
from .oad_230_crypto_causal_narrative_physical_resolution import resolve_causal_narrative_physical_state
from .oad_221_crypto_scientific_reasoning_admission_physical_certification import certify_crypto_scientific_reasoning_admission
from qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance import evaluate_meta_learning_performance
from qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight import build_adaptive_learning_weight

READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class ProspectiveAdaptiveReadmission:
    scored_cases:int;adaptive_weight_state_hash:str|None;adaptive_state:str;supplied_hashes:tuple;missing_state_hashes:tuple;admission_state:str;handoff_verified:bool
    probability_enabled:bool=False;direction_enabled:bool=False;publication_allowed:bool=False;execution_authority:bool=False

def run_prospective_adaptive_ocl029_readmission(root=None):
    scored=read_and_score_mature_prospective_cases(root)
    cr=materialize_prospective_calibration_source_reliability(root)
    bm=materialize_snapshot_behavior_maturity(root);er=materialize_entity_relationship_state(root);cn=resolve_causal_narrative_physical_state(root)
    hashes={}
    if bm.market_behavior_state_hash:hashes["market_behavior_state_hash"]=bm.market_behavior_state_hash
    if bm.maturity_state_hash:hashes["maturity_state_hash"]=bm.maturity_state_hash
    if er.entity_relationship_state_hash:hashes["entity_relationship_state_hash"]=er.entity_relationship_state_hash
    if cr.calibration_state_hash:hashes["calibration_state_hash"]=cr.calibration_state_hash
    if cr.source_reliability_state_hash:hashes["source_reliability_state_hash"]=cr.source_reliability_state_hash
    adaptive=None;state="HOLD_META_LEARNING_PERFORMANCE_DELTAS_REQUIRED"
    if scored:
        perf=evaluate_meta_learning_performance("crypto_prospective_empirical_forecast",tuple(x.performance_delta for x in scored))
        maturity_score=float(bm.maturity_score)
        weight=build_adaptive_learning_weight(perf,1.0,maturity_score)
        adaptive=envelope("adaptive_weight",weight).state_hash;hashes["adaptive_weight_state_hash"]=adaptive;state="MATERIALIZED"
    adm=certify_crypto_scientific_reasoning_admission(certified_state_hashes=hashes)
    return ProspectiveAdaptiveReadmission(len(scored),adaptive,state,tuple(sorted(hashes)),tuple(adm.missing_state_hashes),adm.state,bool(adm.handoff_verified))
