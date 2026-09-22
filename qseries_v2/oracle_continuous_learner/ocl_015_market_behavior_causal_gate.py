from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_011_market_behavior_observation import verify_ocl_011_market_behavior_observation_model
from .ocl_012_market_behavior_learning import verify_ocl_012_market_behavior_learning_engine
from .ocl_013_cross_market_dependency import verify_ocl_013_cross_market_dependency_learning
from .ocl_014_causal_evidence import verify_ocl_014_causal_evidence_learning
OCL_015_BUILD_ID="OCL-015";OCL_015_REVISION="OCL_015_MARKET_BEHAVIOR_CAUSAL_CERTIFICATION_GATE_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class MarketBehaviorCausalCertification:
 builds:tuple[str,...]; capability:str; next_capability:str; certification_hash:str; certified:bool=True
def certify_ocl_011_through_015():
 checks=(verify_ocl_011_market_behavior_observation_model(),verify_ocl_012_market_behavior_learning_engine(),verify_ocl_013_cross_market_dependency_learning(),verify_ocl_014_causal_evidence_learning())
 if not all(checks):raise RuntimeError("capability certification failed")
 builds=tuple("OCL-%03d"%i for i in range(11,16));raw={"builds":builds,"capability":"market_behavior_and_causal_learning","next_capability":"narrative_entity_and_relationship_learning","certified":True}
 return MarketBehaviorCausalCertification(builds,raw["capability"],raw["next_capability"],_h(raw))
def build_ocl_015_certification_manifest():
 c=certify_ocl_011_through_015();return MappingProxyType({"build_id":OCL_015_BUILD_ID,"revision":OCL_015_REVISION,"capability":c.capability,"next_capability":c.next_capability,"certified":True,"execution":False,"publication":False})
def verify_ocl_015_market_behavior_causal_certification_gate():
 c=certify_ocl_011_through_015();return c.certified and len(c.builds)==5 and c.next_capability=="narrative_entity_and_relationship_learning"
