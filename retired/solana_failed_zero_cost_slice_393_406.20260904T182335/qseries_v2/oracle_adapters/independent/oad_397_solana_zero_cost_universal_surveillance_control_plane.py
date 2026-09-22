from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .oad_394_solana_finalized_head_missing_slot_scheduler import build_missing_slot_schedule,read_last_committed_slot
from .oad_396_solana_websocket_assisted_live_head import observe_live_head
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaSurveillanceSnapshot:
    state:str
    finalized_head:int
    last_committed_slot:int|None
    checkpoint_lag:int
    scheduled_slots:tuple
    gaps_pending:int
    rpc_requests:int
    throttle_count:int
    blocks_seen:int
    transactions_seen:int
    economic_events:int
    unknown_programs:int
    universe_entities:int
    active_entities:int
    hot_entities:int
    ultra_hot_entities:int
    execution_authority:bool=False

def classify_surveillance_state(checkpoint_lag,throttle_count=0):
    if checkpoint_lag<=2 and throttle_count==0: return "RUNNING_CAUGHT_UP"
    if checkpoint_lag<=32: return "RUNNING_CATCHING_UP"
    return "BACKFILL_REQUIRED"

def build_surveillance_snapshot(finalized_head,last_committed_slot,*,max_schedule_slots=32,rpc_requests=0,throttle_count=0,blocks_seen=0,transactions_seen=0,economic_events=0,unknown_programs=0,universe_entities=0,active_entities=0,hot_entities=0,ultra_hot_entities=0):
    lag=0 if last_committed_slot is not None and last_committed_slot>=finalized_head else (finalized_head+1 if last_committed_slot is None else finalized_head-last_committed_slot)
    sched=build_missing_slot_schedule(last_committed_slot,finalized_head,max_schedule_slots)
    return SolanaSurveillanceSnapshot(classify_surveillance_state(lag,throttle_count),int(finalized_head),last_committed_slot,int(lag),sched.scheduled_slots,sched.remaining_lag_slots,int(rpc_requests),int(throttle_count),int(blocks_seen),int(transactions_seen),int(economic_events),int(unknown_programs),int(universe_entities),int(active_entities),int(hot_entities),int(ultra_hot_entities),False)

def live_read_only_snapshot(root=None,rpc_head_fn=None):
    r=Path(root).resolve() if root else Path.cwd().resolve()
    head=observe_live_head(rpc_head_fn=rpc_head_fn)
    checkpoint=read_last_committed_slot(r)
    return build_surveillance_snapshot(head.slot,checkpoint)