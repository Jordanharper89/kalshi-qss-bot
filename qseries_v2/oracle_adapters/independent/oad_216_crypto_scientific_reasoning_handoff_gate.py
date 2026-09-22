from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_continuous_learner.ocl_029_scientific_reasoning_handoff import build_scientific_reasoning_handoff,verify_scientific_reasoning_handoff
from .oad_215_crypto_ocl_incremental_state_consumption import read_crypto_ocl_state
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
REQUIRED_NON_LEARNER_HASHES=('calibration_state_hash','source_reliability_state_hash','market_behavior_state_hash','causal_state_hash','narrative_state_hash','entity_relationship_state_hash','maturity_state_hash','adaptive_weight_state_hash')
@dataclass(frozen=True,slots=True)
class CryptoScientificReasoningHandoffGate:
 learner_state_hash:str;learner_state_verified:bool;missing_state_hashes:tuple;handoff:object|None;handoff_verified:bool;state:str;physical_ready:bool;probability_enabled:bool=False;direction_enabled:bool=False;execution_authority:bool=False
def evaluate_crypto_scientific_reasoning_handoff(root=None,certified_state_hashes=None):
 cycle,state,_=read_crypto_ocl_state(root);learner=str(state.state_hash);learner_ok=len(learner)==64 and state.applied_through_sequence>=0;sup=dict(certified_state_hashes or {});missing=tuple(n for n in REQUIRED_NON_LEARNER_HASHES if len(str(sup.get(n,'')))!=64)
 if missing:return CryptoScientificReasoningHandoffGate(learner,learner_ok,missing,None,False,'HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED',learner_ok,False,False,False)
 hashes={'learner_state_hash':learner};hashes.update({n:str(sup[n]) for n in REQUIRED_NON_LEARNER_HASHES});h=build_scientific_reasoning_handoff(**hashes);ok=verify_scientific_reasoning_handoff(h)
 if not ok:raise RuntimeError('OCL-029 Scientific Reasoning handoff verification failed')
 return CryptoScientificReasoningHandoffGate(learner,learner_ok,tuple(),h,True,'READY_FOR_SCIENTIFIC_REASONING_HANDOFF',bool(learner_ok and ok),False,False,False)
