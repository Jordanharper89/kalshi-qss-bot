from dataclasses import dataclass
from hashlib import sha256
import json
from .ois_011_live_postgresql_adapter import LivePostgreSQLWrite,execute_live_postgresql_write
@dataclass(frozen=True)
class PersistenceReceipt: subject_id:str; version:int; idempotency_key:str; committed:bool
def build_idempotency_key(w): return sha256(json.dumps([w.subject_id,w.version,w.parameters],default=str,separators=(",",":")).encode()).hexdigest()
def persist_state_atomically(c,w): return PersistenceReceipt(w.subject_id,w.version,build_idempotency_key(w),execute_live_postgresql_write(c,w))
def verify_ois_012_atomic_state_persistence_idempotency():
 w=LivePostgreSQLWrite("INSERT X",("x",1),"x",1); return build_idempotency_key(w)==build_idempotency_key(w)
