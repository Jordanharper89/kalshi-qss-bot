from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OCL_019_BUILD_ID="OCL-019"
OCL_019_REVISION="OCL_019_NARRATIVE_MARKET_RELATIONSHIP_LEARNING_V1"

@dataclass(frozen=True)
class NarrativeMarketRelationship:
    narrative_id:str
    market_id:str
    evidence_count:int
    mean_reaction:float
    mean_lag_seconds:float
    directional_consistency:float
    relationship_strength:float

def learn_narrative_market_relationship(narrative_id,market_id,reactions):
    rows=tuple((float(delta),float(lag)) for delta,lag in reactions)
    if not narrative_id or not market_id or not rows:
        raise ValueError("narrative/market evidence required")
    mean_reaction=sum(x for x,_ in rows)/len(rows)
    mean_lag=sum(l for _,l in rows)/len(rows)
    pos=sum(1 for x,_ in rows if x>0);neg=sum(1 for x,_ in rows if x<0)
    consistency=abs(pos-neg)/len(rows)
    strength=(len(rows)/(len(rows)+5))*consistency*(abs(mean_reaction)/(1+abs(mean_reaction)))
    return NarrativeMarketRelationship(narrative_id,market_id,len(rows),mean_reaction,mean_lag,consistency,strength)

def build_ocl_019_certification_manifest():
    return MappingProxyType({"build_id":OCL_019_BUILD_ID,"revision":OCL_019_REVISION,"relationship":"historical_narrative_market_reaction","trade_signal":False,"execution":False})

def verify_ocl_019_narrative_market_relationship_learning():
    x=learn_narrative_market_relationship("n","m",((.2,3),(.3,4),(.1,2)))
    return x.evidence_count==3 and x.relationship_strength>0 and not build_ocl_019_certification_manifest()["trade_signal"]
