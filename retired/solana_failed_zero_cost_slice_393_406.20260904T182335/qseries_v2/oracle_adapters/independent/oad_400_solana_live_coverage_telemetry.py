from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .oad_394_solana_finalized_head_missing_slot_scheduler import read_last_committed_slot
from .oad_396_solana_websocket_assisted_live_head import observe_live_head

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class LiveCoverageTelemetry:
    finalized_head:int
    last_committed_slot:int|None
    checkpoint_lag:int
    source:str
    state:str
    execution_authority:bool=False

def classify_lag(lag):
    if lag<=2: return "CAUGHT_UP"
    if lag<=32: return "NEAR_LIVE"
    if lag<=256: return "CATCHING_UP"
    return "BACKLOG"

def capture_live_coverage(root=None,rpc_head_fn=None):
    r=Path(root).resolve() if root else Path.cwd().resolve()
    head=observe_live_head(rpc_head_fn=rpc_head_fn)
    cp=read_last_committed_slot(r)
    lag=head.slot+1 if cp is None else max(0,head.slot-cp)
    return LiveCoverageTelemetry(head.slot,cp,lag,head.source,classify_lag(lag),False)