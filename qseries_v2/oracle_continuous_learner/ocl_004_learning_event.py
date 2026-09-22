from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_001_foundation import build_learning_identity
from .ocl_003_outcome_observation import OutcomeObservation,verify_outcome_observation
OCL_004_BUILD_ID="OCL-004";OCL_004_REVISION="OCL_004_DETERMINISTIC_LEARNING_EVENT_ASSEMBLY_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class LearningEvent:
 event_id:str; subject_id:str; evidence_hash:str; outcome_hash:str; lineage_hash:str; outcome_type:str; event_hash:str
def assemble_learning_event(subject_id,evidence_hash,lineage_hash,outcome):
 if not verify_outcome_observation(outcome):raise ValueError("invalid outcome")
 if outcome.subject_id!=subject_id:raise ValueError("subject mismatch")
 ident=build_learning_identity(subject_id,evidence_hash,outcome.outcome_hash,lineage_hash)
 raw={"event_id":ident.learning_event_id,"subject_id":subject_id,"evidence_hash":evidence_hash,"outcome_hash":outcome.outcome_hash,"lineage_hash":lineage_hash,"outcome_type":outcome.outcome_type}
 return LearningEvent(ident.learning_event_id,subject_id,evidence_hash,outcome.outcome_hash,lineage_hash,outcome.outcome_type,_h(raw))
def verify_learning_event(e):return e.event_hash==_h({"event_id":e.event_id,"subject_id":e.subject_id,"evidence_hash":e.evidence_hash,"outcome_hash":e.outcome_hash,"lineage_hash":e.lineage_hash,"outcome_type":e.outcome_type})
def build_ocl_004_certification_manifest():return MappingProxyType({"build_id":OCL_004_BUILD_ID,"revision":OCL_004_REVISION,"deterministic":True,"requires_evidence":True,"requires_outcome":True,"execution":False})
def verify_ocl_004_deterministic_learning_event_assembly():
 from .ocl_003_outcome_observation import build_outcome_observation
 o=build_outcome_observation("m","settlement",1,"t","s","a"*64);e=assemble_learning_event("m","b"*64,"c"*64,o);return verify_learning_event(e)
