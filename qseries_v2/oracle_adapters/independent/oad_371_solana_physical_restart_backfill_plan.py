\

from __future__ import annotations
from dataclasses import dataclass
from .oad_366_solana_restart_backfill_idempotency_guard import reconcile_restart_idempotency
from .oad_368_solana_physical_checkpoint_contract import discover_checkpoint_contract
from .oad_361_solana_restart_backfill_reconciliation import reconcile_restart_window

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaPhysicalRestartPlan:
    checkpoint_before:int|None
    finalized_head:int
    returned_slots:tuple
    skipped_slots:tuple
    restart_state:str
    replay_idempotent:bool
    accepted_new_ids:tuple
    execution_authority:bool=False

def build_physical_restart_plan(finalized_head,returned_slots,existing_ids=(),replay_ids=(),skipped_slots=(),root=None):
    cp=discover_checkpoint_contract(root)
    before=cp.current_slot
    rec=reconcile_restart_window(before,finalized_head,returned_slots,skipped_slots,root)
    idem=reconcile_restart_idempotency(existing_ids,replay_ids)
    return SolanaPhysicalRestartPlan(
        before,int(finalized_head),tuple(returned_slots),tuple(skipped_slots),
        str(getattr(rec,"state",getattr(rec,"reconciliation_state","UNKNOWN"))),
        bool(idem.idempotent),tuple(idem.accepted_new_ids),False
    )

