from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json, os

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class GMGNRuntimeCheckpoint:
    cycles:int
    successes:int
    failures:int
    last_success_at:str|None
    last_error:str|None
    last_token_address:str|None
    last_observation_ids:tuple
    execution_authority:bool=False

def genesis_gmgn_runtime_checkpoint():
    return GMGNRuntimeCheckpoint(0,0,0,None,None,None,(),False)

def checkpoint_path(root=None):
    r=Path(root or Path.cwd()).resolve()
    p=r/"runtime_state"
    p.mkdir(parents=True,exist_ok=True)
    return p/"oad_283_gmgn_continuous_runtime_checkpoint.json"

def load_gmgn_runtime_checkpoint(root=None):
    p=checkpoint_path(root)
    if not p.exists(): return genesis_gmgn_runtime_checkpoint()
    d=json.loads(p.read_text(encoding="utf-8"))
    return GMGNRuntimeCheckpoint(
        int(d["cycles"]),int(d["successes"]),int(d["failures"]),
        d.get("last_success_at"),d.get("last_error"),d.get("last_token_address"),
        tuple(d.get("last_observation_ids") or ()),False
    )

def save_gmgn_runtime_checkpoint(cp,root=None):
    if cp.execution_authority is not False: raise RuntimeError("execution boundary violation")
    p=checkpoint_path(root)
    d=asdict(cp); d["last_observation_ids"]=list(cp.last_observation_ids)
    tmp=p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    os.replace(tmp,p)
    return p

def advance_success(cp,token_address,observation_ids):
    return GMGNRuntimeCheckpoint(
        cp.cycles+1,cp.successes+1,cp.failures,
        datetime.now(timezone.utc).isoformat(),None,str(token_address),
        tuple(observation_ids),False
    )

def advance_failure(cp,error):
    return GMGNRuntimeCheckpoint(
        cp.cycles+1,cp.successes,cp.failures+1,
        cp.last_success_at,str(error)[:500],cp.last_token_address,
        cp.last_observation_ids,False
    )
