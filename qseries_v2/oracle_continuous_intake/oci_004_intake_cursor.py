from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Any
from .oci_003_postgresql_read_contract import verify_oci_003_postgresql_read_only_intake_contract

OCI_004_BUILD_ID="OCI-004"
OCI_004_REVISION="OCI_004_DETERMINISTIC_INTAKE_CURSOR_V1"

def _hash(v:object)->str:
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class IntakeCursor:
    stream_id:str
    cursor_column:str
    cursor_value:int
    last_source_hash:str
    batch_sequence:int
    checkpoint_parent_hash:str
    cursor_hash:str

def build_genesis_cursor(stream_id:str,cursor_column:str)->IntakeCursor:
    if not stream_id or not cursor_column:raise ValueError("stream and cursor column required")
    raw={"stream_id":stream_id,"cursor_column":cursor_column,"cursor_value":0,"last_source_hash":"0"*64,
         "batch_sequence":0,"checkpoint_parent_hash":"0"*64}
    return IntakeCursor(**raw,cursor_hash=_hash(raw))

def advance_cursor(previous:IntakeCursor,new_value:int,last_source_hash:str)->IntakeCursor:
    if new_value <= previous.cursor_value:raise ValueError("cursor must advance monotonically")
    if len(last_source_hash)!=64:raise ValueError("source hash must be sha256 hex")
    int(last_source_hash,16)
    raw={"stream_id":previous.stream_id,"cursor_column":previous.cursor_column,"cursor_value":int(new_value),
         "last_source_hash":last_source_hash,"batch_sequence":previous.batch_sequence+1,
         "checkpoint_parent_hash":previous.cursor_hash}
    return IntakeCursor(**raw,cursor_hash=_hash(raw))

def verify_cursor(cursor:IntakeCursor)->bool:
    raw={k:v for k,v in asdict(cursor).items() if k!="cursor_hash"}
    try:
        int(cursor.last_source_hash,16); int(cursor.checkpoint_parent_hash,16)
    except ValueError:return False
    return len(cursor.last_source_hash)==64 and len(cursor.checkpoint_parent_hash)==64 and cursor.cursor_hash==_hash(raw)

def build_oci_004_certification_manifest()->Mapping[str,Any]:
    raw={"build_id":OCI_004_BUILD_ID,"revision":OCI_004_REVISION,"upstream":"OCI-003",
         "cursor_model":"monotonic_hash_chained","checkpoint_storage_contract":"append_only",
         "destructive_checkpoint_update_allowed":False,"execution_enabled":False,"publication_enabled":False}
    return MappingProxyType({**raw,"manifest_hash":_hash(raw)})

def verify_oci_004_deterministic_intake_cursor()->bool:
    a=build_genesis_cursor("live_shadow","sequence_id")
    b=advance_cursor(a,1,"a"*64)
    return verify_oci_003_postgresql_read_only_intake_contract() and verify_cursor(a) and verify_cursor(b) and b.checkpoint_parent_hash==a.cursor_hash
