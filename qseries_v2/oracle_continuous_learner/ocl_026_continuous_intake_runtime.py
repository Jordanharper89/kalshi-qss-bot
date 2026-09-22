from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Any

OCL_026_BUILD_ID="OCL-026"
OCL_026_REVISION="OCL_026_CONTINUOUS_LEARNER_INTAKE_RUNTIME_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class LearnerRuntimeInput:
    sequence:int
    source_kind:str
    source_ref:str
    source_hash:str
    payload:Mapping[str,Any]
    input_hash:str

@dataclass(frozen=True)
class LearnerRuntimeBatch:
    inputs:tuple[LearnerRuntimeInput,...]
    start_sequence:int
    end_sequence:int
    batch_hash:str

def build_runtime_input(sequence,source_kind,source_ref,source_hash,payload):
    if sequence < 1 or not source_kind or not source_ref or len(source_hash)!=64:
        raise ValueError("invalid runtime input identity")
    canonical={str(k):payload[k] for k in sorted(payload)}
    raw={"sequence":sequence,"source_kind":source_kind,"source_ref":source_ref,"source_hash":source_hash,"payload":canonical}
    return LearnerRuntimeInput(sequence,source_kind,source_ref,source_hash,MappingProxyType(canonical),_h(raw))

def assemble_runtime_batch(inputs):
    rows=tuple(sorted(inputs,key=lambda x:x.sequence))
    if not rows: raise ValueError("runtime inputs required")
    seq=[x.sequence for x in rows]
    if len(seq)!=len(set(seq)) or any(b<=a for a,b in zip(seq,seq[1:])):
        raise ValueError("runtime sequence must be unique and monotonic")
    raw={"input_hashes":[x.input_hash for x in rows],"start_sequence":rows[0].sequence,"end_sequence":rows[-1].sequence}
    return LearnerRuntimeBatch(rows,rows[0].sequence,rows[-1].sequence,_h(raw))

def verify_runtime_batch(b):
    raw={"input_hashes":[x.input_hash for x in b.inputs],"start_sequence":b.start_sequence,"end_sequence":b.end_sequence}
    return bool(b.inputs) and b.batch_hash==_h(raw)

def build_ocl_026_certification_manifest():
    return MappingProxyType({"build_id":OCL_026_BUILD_ID,"revision":OCL_026_REVISION,"runtime":"continuous_read_only_intake","postgresql_write":False,"execution":False,"publication":False})

def verify_ocl_026_continuous_learner_intake_runtime():
    a=build_runtime_input(1,"oml","obs:1","a"*64,{"x":1})
    b=build_runtime_input(2,"outcome","out:1","b"*64,{"y":2})
    return verify_runtime_batch(assemble_runtime_batch((b,a)))
