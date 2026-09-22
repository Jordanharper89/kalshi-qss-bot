from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .osr_002_hypothesis_formation import ScientificHypothesis

OSR_003_BUILD_ID="OSR-003"
OSR_003_REVISION="OSR_003_EVIDENCE_EVALUATION_V1"

@dataclass(frozen=True)
class EvidenceItem:
    evidence_id:str
    supports:bool
    weight:float
    independence:float
    reliability:float
    evidence_hash:str

@dataclass(frozen=True)
class HypothesisEvidenceEvaluation:
    hypothesis_id:str
    supporting_weight:float
    contradicting_weight:float
    net_evidence:float
    evidence_count:int
    independent_effective_weight:float
    status:str

def evaluate_hypothesis_evidence(hypothesis,evidence):
    if not isinstance(hypothesis,ScientificHypothesis):
        raise ValueError("scientific hypothesis required")
    rows=tuple(evidence)
    if not rows: raise ValueError("evidence required")
    seen=set()
    sup=con=ind=0.0
    for x in rows:
        if x.evidence_id in seen: raise ValueError("duplicate evidence rejected")
        seen.add(x.evidence_id)
        if len(x.evidence_hash)!=64 or not 0<=x.weight<=1 or not 0<=x.independence<=1 or not 0<=x.reliability<=1:
            raise ValueError("invalid evidence")
        effective=x.weight*x.independence*x.reliability
        ind+=effective
        if x.supports: sup+=effective
        else: con+=effective
    total=sup+con
    net=0.0 if total==0 else (sup-con)/total
    status="supported" if net>=.5 else ("contradicted" if net<=-.5 else "uncertain")
    return HypothesisEvidenceEvaluation(hypothesis.hypothesis_id,sup,con,net,len(rows),ind,status)

def build_osr_003_certification_manifest():
    return MappingProxyType({"build_id":OSR_003_BUILD_ID,"revision":OSR_003_REVISION,"dimensions":"weight+independence+reliability+contradiction","correlation_is_not_causation":True,"execution":False})

def verify_osr_003_evidence_evaluation():
    from .osr_001_foundation import build_scientific_reasoning_input
    from .osr_002_hypothesis_formation import form_hypothesis
    i=build_scientific_reasoning_input("a"*64,"why")
    h=form_hypothesis(i,"h","s","m","f",.5)
    e=(EvidenceItem("e1",True,1,1,.9,"b"*64),EvidenceItem("e2",False,.2,1,.8,"c"*64))
    return evaluate_hypothesis_evidence(h,e).status=="supported"
