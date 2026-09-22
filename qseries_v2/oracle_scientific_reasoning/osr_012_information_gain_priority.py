from __future__ import annotations
from dataclasses import dataclass
from math import log2
from types import MappingProxyType

OSR_012_BUILD_ID="OSR-012"
OSR_012_REVISION="OSR_012_INFORMATION_GAIN_EVIDENCE_PRIORITY_ENGINE_V1"

@dataclass(frozen=True)
class EvidenceCandidate:
    candidate_id:str
    probability_of_positive:float
    expected_uncertainty_reduction:float
    acquisition_cost:float

@dataclass(frozen=True)
class EvidencePriority:
    candidate_id:str
    expected_information_gain:float
    utility_score:float
    rank:int

def _entropy(p):
    p=float(p)
    if p<=0 or p>=1: return 0.0
    return -(p*log2(p)+(1-p)*log2(1-p))

def prioritize_evidence_candidates(candidates):
    rows=tuple(candidates)
    if not rows: raise ValueError("evidence candidates required")
    scored=[]
    seen=set()
    for c in rows:
        if c.candidate_id in seen: raise ValueError("duplicate evidence candidate")
        seen.add(c.candidate_id)
        if not 0<=c.probability_of_positive<=1 or not 0<=c.expected_uncertainty_reduction<=1 or c.acquisition_cost<0:
            raise ValueError("invalid evidence candidate")
        ig=_entropy(c.probability_of_positive)*c.expected_uncertainty_reduction
        utility=ig/(1+c.acquisition_cost)
        scored.append((c.candidate_id,ig,utility))
    scored=sorted(scored,key=lambda x:(-x[2],x[0]))
    return tuple(EvidencePriority(cid,ig,u,i+1) for i,(cid,ig,u) in enumerate(scored))

def build_osr_012_certification_manifest():
    return MappingProxyType({"build_id":OSR_012_BUILD_ID,"revision":OSR_012_REVISION,"objective":"expected_information_gain_per_cost","network_acquisition":False,"execution":False})

def verify_osr_012_information_gain_evidence_priority_engine():
    a=EvidenceCandidate("a",.5,.9,0)
    b=EvidenceCandidate("b",.99,.9,0)
    return prioritize_evidence_candidates((b,a))[0].candidate_id=="a"
