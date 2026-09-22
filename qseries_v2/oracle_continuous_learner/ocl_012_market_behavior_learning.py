from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .ocl_011_market_behavior_observation import MarketBehaviorObservation,verify_market_behavior_observation
OCL_012_BUILD_ID="OCL-012";OCL_012_REVISION="OCL_012_MARKET_BEHAVIOR_LEARNING_ENGINE_V1"
@dataclass(frozen=True)
class MarketBehaviorState:
 market_id:str; behavior_type:str; feature_name:str; evidence_count:int; mean_value:float; mean_absolute_deviation:float; behavior_strength:float
def learn_market_behavior(observations):
 rows=tuple(observations)
 if not rows:raise ValueError("behavior evidence required")
 if not all(verify_market_behavior_observation(x) for x in rows):raise ValueError("invalid behavior observation")
 key={(x.market_id,x.behavior_type,x.feature_name) for x in rows}
 if len(key)!=1:raise ValueError("mixed behavior identities")
 mean=sum(x.feature_value for x in rows)/len(rows);mad=sum(abs(x.feature_value-mean) for x in rows)/len(rows)
 strength=(len(rows)/(len(rows)+5))*(1/(1+mad))
 m,b,f=next(iter(key));return MarketBehaviorState(m,b,f,len(rows),mean,mad,strength)
def build_ocl_012_certification_manifest():return MappingProxyType({"build_id":OCL_012_BUILD_ID,"revision":OCL_012_REVISION,"learning":"repeated_outcome_grounded_behavior","trade_authority":False})
def verify_ocl_012_market_behavior_learning_engine():
 from .ocl_011_market_behavior_observation import build_market_behavior_observation
 rows=tuple(build_market_behavior_observation("m","r","lag",x,"t"+str(x),"a"*64,"b"*64) for x in (2,3,4))
 s=learn_market_behavior(rows);return s.evidence_count==3 and 0<s.behavior_strength<1
