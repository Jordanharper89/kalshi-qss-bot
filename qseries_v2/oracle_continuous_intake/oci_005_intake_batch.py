from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Any, Iterable
from .oci_001_foundation import OCIIntakeLineage
from .oci_004_intake_cursor import IntakeCursor, advance_cursor, verify_cursor, verify_oci_004_deterministic_intake_cursor

OCI_005_BUILD_ID="OCI-005"
OCI_005_REVISION="OCI_005_DETERMINISTIC_INTAKE_BATCH_ASSEMBLY_V1"

def _hash(v:object)->str:
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()).hexdigest()

@dataclass(frozen=True)
class IntakeRecord:
    cursor_value:int
    source_ref:str
    payload:Mapping[str,Any]
    source_hash:str

    @staticmethod
    def from_payload(cursor_value:int,source_ref:str,payload:Mapping[str,Any])->"IntakeRecord":
        if cursor_value < 0 or not source_ref:raise ValueError("invalid source identity")
        canonical={str(k):payload[k] for k in sorted(payload)}
        h=_hash({"cursor_value":cursor_value,"source_ref":source_ref,"payload":canonical})
        return IntakeRecord(cursor_value,source_ref,MappingProxyType(canonical),h)

@dataclass(frozen=True)
class IntakeBatch:
    stream_id:str
    batch_sequence:int
    records:tuple[IntakeRecord,...]
    start_cursor_hash:str
    end_cursor:IntakeCursor
    lineage:tuple[OCIIntakeLineage,...]
    batch_hash:str

def assemble_intake_batch(cursor:IntakeCursor,records:Iterable[IntakeRecord],observed_at:str)->IntakeBatch:
    if not verify_cursor(cursor):raise ValueError("invalid starting cursor")
    ordered=tuple(sorted(records,key=lambda r:(r.cursor_value,r.source_hash)))
    if not ordered:raise ValueError("empty intake batch")
    values=[r.cursor_value for r in ordered]
    if any(v <= cursor.cursor_value for v in values):raise ValueError("records must be after cursor")
    if len(values)!=len(set(values)):raise ValueError("duplicate cursor value")
    end=advance_cursor(cursor,ordered[-1].cursor_value,ordered[-1].source_hash)
    lineage=tuple(OCIIntakeLineage("postgresql",r.source_ref,r.source_hash,observed_at,i) for i,r in enumerate(ordered,start=1))
    raw={"stream_id":cursor.stream_id,"batch_sequence":end.batch_sequence,
         "record_hashes":[r.source_hash for r in ordered],"start_cursor_hash":cursor.cursor_hash,
         "end_cursor_hash":end.cursor_hash,"lineage_hashes":[x.lineage_hash for x in lineage]}
    return IntakeBatch(cursor.stream_id,end.batch_sequence,ordered,cursor.cursor_hash,end,lineage,_hash(raw))

def verify_batch(batch:IntakeBatch)->bool:
    if not batch.records or not verify_cursor(batch.end_cursor):return False
    raw={"stream_id":batch.stream_id,"batch_sequence":batch.batch_sequence,
         "record_hashes":[r.source_hash for r in batch.records],"start_cursor_hash":batch.start_cursor_hash,
         "end_cursor_hash":batch.end_cursor.cursor_hash,"lineage_hashes":[x.lineage_hash for x in batch.lineage]}
    return batch.batch_hash==_hash(raw) and len(batch.records)==len(batch.lineage)

def build_oci_005_certification_manifest()->Mapping[str,Any]:
    raw={"build_id":OCI_005_BUILD_ID,"revision":OCI_005_REVISION,"upstream_builds":("OCI-001","OCI-004"),
         "capability_slice":"postgresql_live_shadow_to_deterministic_intake_batch",
         "next_boundary":"OI_UMD_OML_read_only_binding","network_write_enabled":False,
         "postgresql_write_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**raw,"manifest_hash":_hash(raw)})

def verify_oci_005_deterministic_intake_batch_assembly()->bool:
    from .oci_004_intake_cursor import build_genesis_cursor
    g=build_genesis_cursor("live_shadow","sequence_id")
    recs=(IntakeRecord.from_payload(1,"row:1",{"x":1}),IntakeRecord.from_payload(2,"row:2",{"x":2}))
    b=assemble_intake_batch(g,recs,"2026-08-12T00:00:00Z")
    m=build_oci_005_certification_manifest()
    return verify_oci_004_deterministic_intake_cursor() and verify_batch(b) and not m["postgresql_write_enabled"] and not m["execution_enabled"]
