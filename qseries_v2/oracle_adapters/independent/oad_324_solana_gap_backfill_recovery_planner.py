\

from __future__ import annotations
from dataclasses import dataclass
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaRecoveryPlan:
    checkpoint_slot:int|None; finalized_head:int; start_slot:int; end_slot:int; gap_slots:int; mode:str; execution_authority:bool=False
def build_solana_recovery_plan(finalized_head,root=None,max_backfill_slots=256):
    cp=load_solana_chain_checkpoint(root);head=int(finalized_head)
    if cp.last_committed_slot is None:
        start=max(0,head-min(int(max_backfill_slots),32)+1);mode="BOOTSTRAP"
    else:
        start=cp.last_committed_slot+1;mode="LIVE_CONTINUE" if start>=head else "BACKFILL"
    gap=max(0,head-start+1)
    return SolanaRecoveryPlan(cp.last_committed_slot,head,start,head,gap,mode,False)
def acquire_recovery_batch(finalized_head,root=None,max_backfill_slots=256,per_batch_limit=16,timeout_seconds=20.0):
    p=build_solana_recovery_plan(finalized_head,root,max_backfill_slots)
    if p.gap_slots<=0:return p,None
    limit=min(int(per_batch_limit),p.gap_slots)
    return p,acquire_finalized_block_batch(p.start_slot,limit,timeout_seconds)

