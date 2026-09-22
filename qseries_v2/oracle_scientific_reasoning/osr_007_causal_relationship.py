from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_007_BUILD_ID="OSR-007"
OSR_007_REVISION="OSR_007_CAUSAL_RELATIONSHIP_EVALUATION_V1"

@dataclass(frozen=True)
class CausalCriterion:
    name:str
    satisfied:bool
    weight:float

@dataclass(frozen=True)
class CausalRelationshipEvaluation:
    cause_id:str
    effect_id:str
    support_score:float
    counterevidence_score:float
    net_score:float
    satisfied_criteria:int
    status:str

def evaluate_causal_relationship(cause_id,effect_id,criteria,counterevidence_weights=()):
    if not cause_id or not effect_id or cause_id==effect_id:
        raise ValueError("distinct cause/effect identities required")
    rows=tuple(criteria)
    if not rows: raise ValueError("causal criteria required")
    support=0.0; total=0.0; satisfied=0
    for c in rows:
        if not 0<=c.weight<=1: raise ValueError("criterion weight outside [0,1]")
        total+=c.weight
        if c.satisfied:
            support+=c.weight; satisfied+=1
    support_score=0.0 if total==0 else support/total
    counter=sum(max(0.0,min(1.0,float(x))) for x in counterevidence_weights)
    counter_score=min(1.0,counter/len(tuple(counterevidence_weights))) if tuple(counterevidence_weights) else 0.0
    net=support_score-counter_score
    temporal_ok=any(c.name=="temporal_precedence" and c.satisfied for c in rows)
    mechanism_ok=any(c.name=="mechanism" and c.satisfied for c in rows)
    status="supported" if net>=.5 and temporal_ok and mechanism_ok else ("contradicted" if net<=-.5 else "uncertain")
    return CausalRelationshipEvaluation(cause_id,effect_id,support_score,counter_score,net,satisfied,status)

def build_osr_007_certification_manifest():
    return MappingProxyType({"build_id":OSR_007_BUILD_ID,"revision":OSR_007_REVISION,"requires_temporal_precedence":True,"requires_mechanism":True,"supports_counterevidence":True,"execution":False})

def verify_osr_007_causal_relationship_evaluation():
    c=(CausalCriterion("temporal_precedence",True,1),CausalCriterion("mechanism",True,1),CausalCriterion("dose_response",True,.5))
    return evaluate_causal_relationship("a","b",c,()).status=="supported"
