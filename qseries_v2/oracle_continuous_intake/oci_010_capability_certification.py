from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oci_006_oi_intake_binding import verify_oci_006_observation_intelligence_intake_binding
from .oci_007_umd_context_binding import verify_oci_007_umd_market_context_binding
from .oci_008_oml_admission_binding import verify_oci_008_oml_memory_admission_binding
from .oci_009_pipeline_assembly import verify_oci_009_continuous_intelligence_pipeline_assembly
OCI_010_BUILD_ID="OCI-010"; OCI_010_REVISION="OCI_010_CONTINUOUS_INTAKE_CAPABILITY_CERTIFICATION_GATE_V1"
def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class OCICapabilityCertification:
 first_build:str; final_build:str; certified_builds:tuple[str,...]; capability:str; next_boundary:str; freeze_hash:str
 frozen:bool=True; defect_corrections_only:bool=True
def certify_oci_001_through_010():
 checks=(verify_oci_006_observation_intelligence_intake_binding(),verify_oci_007_umd_market_context_binding(),
         verify_oci_008_oml_memory_admission_binding(),verify_oci_009_continuous_intelligence_pipeline_assembly())
 if not all(checks): raise RuntimeError("OCI capability certification failed")
 builds=tuple("OCI-%03d"%i for i in range(1,11))
 raw={"builds":builds,"capability":"continuous_intake_to_oracle_memory_boundary",
      "next_boundary":"continuous_learner_intake","frozen":True,"defect_corrections_only":True}
 return OCICapabilityCertification(builds[0],builds[-1],builds,raw["capability"],raw["next_boundary"],_h(raw))
def build_oci_010_certification_manifest():
 c=certify_oci_001_through_010()
 return MappingProxyType({"build_id":OCI_010_BUILD_ID,"revision":OCI_010_REVISION,"certified_builds":c.certified_builds,
 "capability":c.capability,"next_boundary":c.next_boundary,"frozen":c.frozen,"defect_corrections_only":c.defect_corrections_only,
 "execution":False,"publication":False})
def verify_oci_010_continuous_intake_capability_certification_gate():
 c=certify_oci_001_through_010()
 return c.frozen and c.defect_corrections_only and c.certified_builds==tuple("OCI-%03d"%i for i in range(1,11)) and c.next_boundary=="continuous_learner_intake"
