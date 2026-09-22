from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping,Any
from .oci_005_intake_batch import IntakeBatch,verify_batch

OCI_006_BUILD_ID="OCI-006"; OCI_006_REVISION="OCI_006_OI_INTAKE_BINDING_V1"
FORBIDDEN=frozenset(("prediction","trade_signal","buy","sell","long","short","order","execution","recommended_action","conclusion"))
def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class OIObservationEnvelope:
    observation_id:str; stream_id:str; batch_sequence:int; source_ref:str; source_hash:str
    payload:Mapping[str,Any]; lineage_hash:str; batch_hash:str; envelope_hash:str
    semantic_role:str="observation_not_conclusion"; execution_allowed:bool=False; publication_allowed:bool=False
@dataclass(frozen=True)
class OIIntakeBinding:
    batch_hash:str; envelopes:tuple[OIObservationEnvelope,...]; binding_hash:str
    read_only:bool=True; upstream_mutation:bool=False
def bind_batch_to_oi(batch:IntakeBatch)->OIIntakeBinding:
    if not verify_batch(batch): raise ValueError("invalid OCI-005 batch")
    env=[]
    for r,l in zip(batch.records,batch.lineage):
        keys={str(k).lower() for k in r.payload}
        bad=keys&FORBIDDEN
        if bad: raise ValueError("conclusion/execution fields forbidden: "+",".join(sorted(bad)))
        payload=MappingProxyType({str(k):r.payload[k] for k in sorted(r.payload)})
        raw={"stream_id":batch.stream_id,"batch_sequence":batch.batch_sequence,"source_ref":r.source_ref,
             "source_hash":r.source_hash,"payload":dict(payload),"lineage_hash":l.lineage_hash,"batch_hash":batch.batch_hash}
        eh=_h(raw); env.append(OIObservationEnvelope("oiobs:"+eh,batch.stream_id,batch.batch_sequence,r.source_ref,r.source_hash,payload,l.lineage_hash,batch.batch_hash,eh))
    raw={"batch_hash":batch.batch_hash,"envelopes":[x.envelope_hash for x in env],"read_only":True,"upstream_mutation":False}
    return OIIntakeBinding(batch.batch_hash,tuple(env),_h(raw))
def verify_oi_binding(b):
    return bool(b.envelopes) and b.read_only and not b.upstream_mutation and all(not x.execution_allowed and not x.publication_allowed for x in b.envelopes)
def build_oci_006_certification_manifest():
    return MappingProxyType({"build_id":OCI_006_BUILD_ID,"revision":OCI_006_REVISION,"input":"OCI-005","output":"OI observation envelopes","mutates_oi":False,"execution":False})
def verify_oci_006_observation_intelligence_intake_binding():
    from .oci_004_intake_cursor import build_genesis_cursor
    from .oci_005_intake_batch import IntakeRecord,assemble_intake_batch
    g=build_genesis_cursor("live_shadow","sequence_id"); r=IntakeRecord.from_payload(1,"row:1",{"headline":"x","value":1})
    b=assemble_intake_batch(g,(r,),"2026-08-12T00:00:00Z")
    return verify_oi_binding(bind_batch_to_oi(b))
