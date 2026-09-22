from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import time
from .oad_148_solana_mainnet_chain_state_acquisition import _rpc
from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint
from .oad_326_solana_universal_resilient_worker import run_solana_universal_worker_cycle
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaProductionCatchupCertification:
    before_head:int;after_head:int;before_checkpoint:int|None;after_checkpoint:int|None;before_lag:int;after_lag:int;head_growth:int;checkpoint_growth:int;cycles:int;kept_pace:bool;state:str;execution_authority:bool=False

def _lag(head,checkpoint):
    return int(head)+1 if checkpoint is None else max(0,int(head)-int(checkpoint))

def run_production_catchup_physical_gate(root=None,max_cycles=2,timeout_seconds=180.0,acquisition_timeout_seconds=20.0,progress=None):
    if int(max_cycles)<1: raise ValueError("max_cycles must be >= 1")
    r=Path(root or Path.cwd()).resolve()
    before_head=int(_rpc("getSlot",[{"commitment":"finalized"}],acquisition_timeout_seconds))
    before_cp=load_solana_chain_checkpoint(r).last_committed_slot
    cycles=0
    for i in range(int(max_cycles)):
        x=run_solana_universal_worker_cycle(r,per_batch_limit=32,timeout_seconds=timeout_seconds,acquisition_timeout_seconds=acquisition_timeout_seconds)
        cycles+=1
        if progress: progress("[CYCLE]",i+1,"before=",x.before_slot,"after=",x.after_slot,"slots=",x.requested_slots,"state=",x.state)
        probe_head=int(_rpc("getSlot",[{"commitment":"finalized"}],acquisition_timeout_seconds))
        probe_cp=load_solana_chain_checkpoint(r).last_committed_slot
        if _lag(probe_head,probe_cp)<=_lag(before_head,before_cp): break
    after_head=int(_rpc("getSlot",[{"commitment":"finalized"}],acquisition_timeout_seconds))
    after_cp=load_solana_chain_checkpoint(r).last_committed_slot
    before_lag=_lag(before_head,before_cp); after_lag=_lag(after_head,after_cp)
    head_growth=max(0,after_head-before_head)
    if before_cp is None: checkpoint_growth=0 if after_cp is None else 1
    else: checkpoint_growth=max(0,(after_cp if after_cp is not None else before_cp)-before_cp)
    kept=checkpoint_growth>0 and checkpoint_growth>=head_growth and after_lag<=before_lag
    state="SOLANA_PRODUCTION_CATCHUP_CERTIFIED" if kept else "SOLANA_PRODUCTION_CATCHUP_NOT_CERTIFIED"
    return SolanaProductionCatchupCertification(before_head,after_head,before_cp,after_cp,before_lag,after_lag,head_growth,checkpoint_growth,cycles,kept,state,False)
