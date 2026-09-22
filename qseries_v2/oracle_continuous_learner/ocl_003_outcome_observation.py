from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_002_learning_intake_boundary import verify_ocl_002_learning_intake_boundary
OCL_003_BUILD_ID="OCL-003";OCL_003_REVISION="OCL_003_OUTCOME_OBSERVATION_CONTRACT_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class OutcomeObservation:
 subject_id:str; outcome_type:str; observed_value:object; observed_at:str; source_ref:str; source_hash:str; outcome_hash:str
def build_outcome_observation(subject_id,outcome_type,value,observed_at,source_ref,source_hash):
 if not subject_id or not outcome_type or not observed_at or not source_ref:raise ValueError("outcome identity fields required")
 if len(source_hash)!=64:raise ValueError("source hash required")
 raw={"subject_id":subject_id,"outcome_type":outcome_type,"observed_value":value,"observed_at":observed_at,"source_ref":source_ref,"source_hash":source_hash}
 return OutcomeObservation(subject_id,outcome_type,value,observed_at,source_ref,source_hash,_h(raw))
def verify_outcome_observation(o):return len(o.source_hash)==64 and o.outcome_hash==_h({"subject_id":o.subject_id,"outcome_type":o.outcome_type,"observed_value":o.observed_value,"observed_at":o.observed_at,"source_ref":o.source_ref,"source_hash":o.source_hash})
def build_ocl_003_certification_manifest():return MappingProxyType({"build_id":OCL_003_BUILD_ID,"revision":OCL_003_REVISION,"outcomes_are_observations":True,"retroactive_rewrite":False,"execution":False})
def verify_ocl_003_outcome_observation_contract():
 o=build_outcome_observation("m1","settlement",True,"2026-08-12T00:00:00Z","venue:m1","a"*64)
 return verify_ocl_002_learning_intake_boundary() and verify_outcome_observation(o)
