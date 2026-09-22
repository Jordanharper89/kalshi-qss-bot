
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json, os

STATE_NAME="oracle_pre_settlement_coverage_runtime_state.json"

@dataclass(frozen=True)
class DurableCoverageRuntimeState:
    cycles_completed:int=0
    markets_planned:int=0
    markets_persisted:int=0
    transient_failures:int=0
    consecutive_failures:int=0
    last_cycle_status:str="NEVER_RUN"
    last_cycle_at:str=""
    state_hash:str=""

def state_path(root=None):
    return Path(root or Path.cwd()).resolve()/"runtime_state"/STATE_NAME

def _hash_payload(payload):
    clean=dict(payload)
    clean["state_hash"]=""
    return sha256(json.dumps(clean,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def load_coverage_runtime_state(root=None):
    p=state_path(root)
    if not p.exists():
        return DurableCoverageRuntimeState()
    data=json.loads(p.read_text(encoding="utf-8"))
    return DurableCoverageRuntimeState(**data)

def save_coverage_runtime_state(state,root=None):
    p=state_path(root)
    p.parent.mkdir(parents=True,exist_ok=True)
    payload=asdict(state)
    payload["state_hash"]=_hash_payload(payload)
    tmp=p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,indent=2),encoding="utf-8")
    os.replace(tmp,p)
    return DurableCoverageRuntimeState(**payload)

def advance_coverage_runtime_state(state,*,planned,persisted,status,transient_failure=False,at=None):
    at=at or datetime.now(timezone.utc).isoformat()
    failed=status!="SUCCESS"
    return DurableCoverageRuntimeState(
        cycles_completed=state.cycles_completed+1,
        markets_planned=state.markets_planned+int(planned),
        markets_persisted=state.markets_persisted+int(persisted),
        transient_failures=state.transient_failures+(1 if transient_failure else 0),
        consecutive_failures=(state.consecutive_failures+1 if failed else 0),
        last_cycle_status=str(status),
        last_cycle_at=str(at),
        state_hash="",
    )

def verify_opc_017_durable_coverage_runtime_state():
    s=DurableCoverageRuntimeState()
    n=advance_coverage_runtime_state(s,planned=10,persisted=10,status="SUCCESS",at="2026-01-01T00:00:00+00:00")
    return n.cycles_completed==1 and n.markets_persisted==10 and n.consecutive_failures==0
