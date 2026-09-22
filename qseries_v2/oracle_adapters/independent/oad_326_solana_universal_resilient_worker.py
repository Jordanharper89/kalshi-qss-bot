from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .oad_148_solana_mainnet_chain_state_acquisition import _rpc
from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint,commit_solana_chain_checkpoint
from .oad_324_solana_gap_backfill_recovery_planner import build_solana_recovery_plan
from .oad_325_solana_universal_single_writer_persistence import persist_solana_universal_chain_batch
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaUniversalWorkerCycle:
    head_slot:int;before_slot:int|None;after_slot:int|None;mode:str;requested_slots:int;transactions:int;observations:int;committed_events:int;state:str;execution_authority:bool=False

def _adaptive_batch_size(gap_slots,cap=32):
    gap=max(0,int(gap_slots)); cap=max(1,min(int(cap),32))
    if gap<=4: desired=gap
    elif gap<=16: desired=8
    elif gap<=64: desired=16
    else: desired=32
    return min(cap,gap,desired)

def run_solana_universal_worker_cycle(root=None,per_batch_limit=32,timeout_seconds=180.0,acquisition_timeout_seconds=20.0):
    root=Path(root or Path.cwd()).resolve()
    head=int(_rpc("getSlot",[{"commitment":"finalized"}],acquisition_timeout_seconds))
    plan=build_solana_recovery_plan(head,root)
    before=load_solana_chain_checkpoint(root)
    if plan.gap_slots<=0:
        return SolanaUniversalWorkerCycle(head,before.last_committed_slot,before.last_committed_slot,plan.mode,0,0,0,0,"CAUGHT_UP",False)
    count=_adaptive_batch_size(plan.gap_slots,per_batch_limit)
    p=persist_solana_universal_chain_batch(plan.start_slot,count,root,timeout_seconds,acquisition_timeout_seconds)
    if p.coverage_state!="UNIVERSAL_BATCH_ACCOUNTED":
        raise RuntimeError("coverage gate refused checkpoint advance")
    if int(p.observations)!=int(p.committed_events):
        raise RuntimeError("exact PostgreSQL readback did not account for full Solana batch")
    target=int(plan.start_slot)+int(count)-1
    commit_solana_chain_checkpoint(target,None,root)
    return SolanaUniversalWorkerCycle(head,before.last_committed_slot,target,plan.mode,count,int(p.transactions),int(p.observations),int(p.committed_events),"COMMITTED",False)
