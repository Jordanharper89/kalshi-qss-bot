from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oci_007_umd_context_binding import UMDContextBinding,verify_umd_context_binding
OCI_008_BUILD_ID="OCI-008"; OCI_008_REVISION="OCI_008_OML_MEMORY_ADMISSION_BINDING_V1"
def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class OMLAdmissionCandidate:
 observation_id:str; canonical_market_id:str; evidence_hash:str; lineage_hash:str; admission_hash:str
@dataclass(frozen=True)
class OMLAdmissionBinding:
 umd_binding_hash:str; candidates:tuple[OMLAdmissionCandidate,...]; binding_hash:str
 oml_read_only:bool=True; writes_memory:bool=False
def build_oml_admission_binding(umd:UMDContextBinding)->OMLAdmissionBinding:
 if not verify_umd_context_binding(umd): raise ValueError("invalid OCI-007 binding")
 rows=[]
 for x in umd.contexts:
  raw={"observation_id":x.observation_id,"canonical_market_id":x.context.canonical_market_id,
       "evidence_hash":x.oi_envelope_hash,"lineage_hash":x.context_hash}
  rows.append(OMLAdmissionCandidate(x.observation_id,x.context.canonical_market_id,x.oi_envelope_hash,x.context_hash,_h(raw)))
 raw={"umd_binding_hash":umd.binding_hash,"candidates":[x.admission_hash for x in rows],"oml_read_only":True,"writes_memory":False}
 return OMLAdmissionBinding(umd.binding_hash,tuple(rows),_h(raw))
def verify_oml_admission_binding(b): return b.oml_read_only and not b.writes_memory and all(x.admission_hash for x in b.candidates)
def build_oci_008_certification_manifest(): return MappingProxyType({"build_id":OCI_008_BUILD_ID,"revision":OCI_008_REVISION,"role":"admission_candidate_only","oml_write":False,"execution":False})
def verify_oci_008_oml_memory_admission_binding():
 from .oci_007_umd_context_binding import UMDContextBinding
 empty=UMDContextBinding("a"*64,(), "b"*64, True)
 return verify_oml_admission_binding(build_oml_admission_binding(empty))
