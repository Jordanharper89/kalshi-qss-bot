from __future__ import annotations
from dataclasses import dataclass
from .oad_394_solana_finalized_head_missing_slot_scheduler import build_missing_slot_schedule

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class CatchupPlan:
    checkpoint_slot:int|None
    finalized_head:int
    lag:int
    batch_slots:tuple
    state:str
    execution_authority:bool=False

def plan_zero_cost_catchup(checkpoint_slot,finalized_head,max_slots=16,skipped_slots=()):
    s=build_missing_slot_schedule(checkpoint_slot,finalized_head,max_slots=max_slots,skipped_slots=skipped_slots)
    lag=finalized_head+1 if checkpoint_slot is None else max(0,finalized_head-checkpoint_slot)
    state="CAUGHT_UP" if lag<=2 else ("BOUNDED_CATCHUP" if lag<=256 else "DEEP_BACKFILL")
    return CatchupPlan(checkpoint_slot,int(finalized_head),int(lag),s.scheduled_slots,state,False)

def catchup_cycles_for_lag(lag,slots_per_cycle=16,max_cycles=32):
    if lag<=0:return 0
    return min(max_cycles,max(1,(int(lag)+slots_per_cycle-1)//slots_per_cycle))