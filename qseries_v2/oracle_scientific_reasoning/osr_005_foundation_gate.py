from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .osr_001_foundation import verify_osr_001_scientific_reasoning_foundation
from .osr_002_hypothesis_formation import verify_osr_002_hypothesis_formation
from .osr_003_evidence_evaluation import verify_osr_003_evidence_evaluation
from .osr_004_competing_hypotheses import verify_osr_004_competing_hypothesis_analysis

OSR_005_BUILD_ID="OSR-005"
OSR_005_REVISION="OSR_005_FOUNDATION_HYPOTHESIS_EVIDENCE_CERTIFICATION_GATE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class ScientificReasoningFoundationCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_osr_001_through_005():
    checks=(verify_osr_001_scientific_reasoning_foundation(),verify_osr_002_hypothesis_formation(),verify_osr_003_evidence_evaluation(),verify_osr_004_competing_hypothesis_analysis())
    if not all(checks): raise RuntimeError("Scientific Reasoning foundation certification failed")
    builds=tuple("OSR-%03d"%i for i in range(1,6))
    raw={"builds":builds,"capability":"scientific_hypothesis_and_evidence_reasoning","next_capability":"bayesian_causal_and_temporal_reasoning","certified":True}
    return ScientificReasoningFoundationCertification(builds,raw["capability"],raw["next_capability"],_h(raw))

def build_osr_005_certification_manifest():
    c=certify_osr_001_through_005()
    return MappingProxyType({"build_id":OSR_005_BUILD_ID,"revision":OSR_005_REVISION,"capability":c.capability,"next_capability":c.next_capability,"certified":True,"execution":False,"publication":False})

def verify_osr_005_foundation_hypothesis_evidence_certification_gate():
    c=certify_osr_001_through_005()
    return c.certified and len(c.builds)==5 and c.next_capability=="bayesian_causal_and_temporal_reasoning"
