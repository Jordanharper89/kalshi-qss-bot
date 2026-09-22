from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_018_BUILD_ID="OCL-018"
OCL_018_REVISION="OCL_018_NARRATIVE_LEARNING_ENGINE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class NarrativeObservation:
    narrative_id:str
    stance:str
    weight:float
    source_id:str
    evidence_hash:str

@dataclass(frozen=True)
class NarrativeLearningState:
    narrative_id:str
    supporting_weight:float
    contradicting_weight:float
    source_count:int
    strength:float
    status:str
    narrative_hash:str

def learn_narrative_state(observations):
    rows=tuple(observations)
    if not rows: raise ValueError("narrative evidence required")
    ids={x.narrative_id for x in rows}
    if len(ids)!=1: raise ValueError("mixed narrative ids")
    sup=sum(max(0.0,x.weight) for x in rows if x.stance=="support")
    con=sum(max(0.0,x.weight) for x in rows if x.stance=="contradict")
    sources=len({x.source_id for x in rows})
    total=sup+con
    strength=0.0 if total==0 else (sup-con)/total
    status="strengthening" if strength>=.5 else ("weakening" if strength<=-.5 else "contested")
    narrative_id=next(iter(ids))
    raw={"narrative_id":narrative_id,"supporting_weight":sup,"contradicting_weight":con,"source_count":sources,"strength":strength,"status":status}
    return NarrativeLearningState(narrative_id,sup,con,sources,strength,status,_h(raw))

def verify_narrative_learning_state(x):
    raw={"narrative_id":x.narrative_id,"supporting_weight":x.supporting_weight,"contradicting_weight":x.contradicting_weight,"source_count":x.source_count,"strength":x.strength,"status":x.status}
    return -1<=x.strength<=1 and x.narrative_hash==_h(raw)

def build_ocl_018_certification_manifest():
    return MappingProxyType({"build_id":OCL_018_BUILD_ID,"revision":OCL_018_REVISION,"supports_contradictions":True,"publication":False,"execution":False})

def verify_ocl_018_narrative_learning_engine():
    rows=(NarrativeObservation("n","support",1.0,"s1","a"*64),NarrativeObservation("n","contradict",.2,"s2","b"*64))
    return verify_narrative_learning_state(learn_narrative_state(rows))
