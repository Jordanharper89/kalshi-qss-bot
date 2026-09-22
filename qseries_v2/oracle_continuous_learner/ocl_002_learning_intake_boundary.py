from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_001_foundation import verify_ocl_001_continuous_learner_foundation
OCL_002_BUILD_ID="OCL-002";OCL_002_REVISION="OCL_002_CERTIFIED_OML_OCI_LEARNING_INTAKE_BOUNDARY_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class LearningIntakeBoundary:
 source_capability:str; source_freeze_hash:str; memory_read_only:bool=True; intake_read_only:bool=True; execution:bool=False
def build_learning_intake_boundary(source_freeze_hash):
 if len(source_freeze_hash)!=64:raise ValueError("freeze hash required")
 return LearningIntakeBoundary("OCI-001..010_to_OML_boundary",source_freeze_hash)
def verify_learning_intake_boundary(b):return b.memory_read_only and b.intake_read_only and not b.execution and len(b.source_freeze_hash)==64
def build_ocl_002_certification_manifest():return MappingProxyType({"build_id":OCL_002_BUILD_ID,"revision":OCL_002_REVISION,"OCI_frozen":True,"OML_read_only":True,"mutation":False})
def verify_ocl_002_learning_intake_boundary():return verify_ocl_001_continuous_learner_foundation() and verify_learning_intake_boundary(build_learning_intake_boundary("a"*64))
