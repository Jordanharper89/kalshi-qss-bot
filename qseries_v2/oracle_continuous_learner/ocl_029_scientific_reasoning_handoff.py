from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_029_BUILD_ID="OCL-029"
OCL_029_REVISION="OCL_029_SCIENTIFIC_REASONING_HANDOFF_CONTRACT_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class ScientificReasoningHandoff:
    learner_state_hash:str
    calibration_state_hash:str
    source_reliability_state_hash:str
    market_behavior_state_hash:str
    causal_state_hash:str
    narrative_state_hash:str
    entity_relationship_state_hash:str
    maturity_state_hash:str
    adaptive_weight_state_hash:str
    handoff_hash:str
    read_only:bool=True
    execution_allowed:bool=False
    publication_allowed:bool=False

def build_scientific_reasoning_handoff(**hashes):
    required=("learner_state_hash","calibration_state_hash","source_reliability_state_hash","market_behavior_state_hash","causal_state_hash","narrative_state_hash","entity_relationship_state_hash","maturity_state_hash","adaptive_weight_state_hash")
    for name in required:
        if name not in hashes or len(hashes[name])!=64:
            raise ValueError("missing certified state hash: "+name)
    raw={k:hashes[k] for k in required}
    raw.update({"read_only":True,"execution_allowed":False,"publication_allowed":False})
    return ScientificReasoningHandoff(**{k:hashes[k] for k in required},handoff_hash=_h(raw))

def verify_scientific_reasoning_handoff(x):
    raw={
        "learner_state_hash":x.learner_state_hash,"calibration_state_hash":x.calibration_state_hash,
        "source_reliability_state_hash":x.source_reliability_state_hash,"market_behavior_state_hash":x.market_behavior_state_hash,
        "causal_state_hash":x.causal_state_hash,"narrative_state_hash":x.narrative_state_hash,
        "entity_relationship_state_hash":x.entity_relationship_state_hash,"maturity_state_hash":x.maturity_state_hash,
        "adaptive_weight_state_hash":x.adaptive_weight_state_hash,"read_only":True,"execution_allowed":False,"publication_allowed":False,
    }
    return x.read_only and not x.execution_allowed and not x.publication_allowed and x.handoff_hash==_h(raw)

def build_ocl_029_certification_manifest():
    return MappingProxyType({"build_id":OCL_029_BUILD_ID,"revision":OCL_029_REVISION,"downstream":"Scientific Reasoning","read_only":True,"execution":False,"publication":False})

def verify_ocl_029_scientific_reasoning_handoff_contract():
    names=("learner_state_hash","calibration_state_hash","source_reliability_state_hash","market_behavior_state_hash","causal_state_hash","narrative_state_hash","entity_relationship_state_hash","maturity_state_hash","adaptive_weight_state_hash")
    h=build_scientific_reasoning_handoff(**{n:("a"*64 if i%2==0 else "b"*64) for i,n in enumerate(names)})
    return verify_scientific_reasoning_handoff(h)
