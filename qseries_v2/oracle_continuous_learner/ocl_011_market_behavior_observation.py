from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
OCL_011_BUILD_ID="OCL-011";OCL_011_REVISION="OCL_011_MARKET_BEHAVIOR_OBSERVATION_MODEL_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class MarketBehaviorObservation:
 market_id:str; behavior_type:str; feature_name:str; feature_value:float; observed_at:str; evidence_hash:str; outcome_hash:str; observation_hash:str
def build_market_behavior_observation(market_id,behavior_type,feature_name,feature_value,observed_at,evidence_hash,outcome_hash):
 if not market_id or not behavior_type or not feature_name or not observed_at:raise ValueError("behavior identity fields required")
 for x in (evidence_hash,outcome_hash):
  if len(x)!=64:raise ValueError("sha256 evidence/outcome required")
 raw={"market_id":market_id,"behavior_type":behavior_type,"feature_name":feature_name,"feature_value":float(feature_value),"observed_at":observed_at,"evidence_hash":evidence_hash,"outcome_hash":outcome_hash}
 return MarketBehaviorObservation(market_id,behavior_type,feature_name,float(feature_value),observed_at,evidence_hash,outcome_hash,_h(raw))
def verify_market_behavior_observation(o):
 raw={"market_id":o.market_id,"behavior_type":o.behavior_type,"feature_name":o.feature_name,"feature_value":o.feature_value,"observed_at":o.observed_at,"evidence_hash":o.evidence_hash,"outcome_hash":o.outcome_hash}
 return o.observation_hash==_h(raw)
def build_ocl_011_certification_manifest():return MappingProxyType({"build_id":OCL_011_BUILD_ID,"revision":OCL_011_REVISION,"role":"behavior_observation_not_trade_signal","execution":False})
def verify_ocl_011_market_behavior_observation_model():
 o=build_market_behavior_observation("m","reaction","lag_seconds",4.0,"t","a"*64,"b"*64);return verify_market_behavior_observation(o)
