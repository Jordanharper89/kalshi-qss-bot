\

from __future__ import annotations
from dataclasses import dataclass
from .oad_358_solana_skipped_slot_safe_checkpoint import prove_contiguous_slot_accounting,safe_checkpoint_target
from .oad_359_solana_immutable_gap_lineage_ledger import append_gap_lineage
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaRestartReconciliation:
    checkpoint_before:int|None; finalized_head:int; recovery_start:int; recovery_end:int; returned_slots:tuple; skipped_slots:tuple
    missing_slots:tuple; checkpoint_after:int|None; state:str; execution_authority:bool=False
def reconcile_restart_window(checkpoint_before,finalized_head,returned_slots,skipped_slots=(),root=None):
    head=int(finalized_head); start=(int(checkpoint_before)+1) if checkpoint_before is not None else min(tuple(returned_slots) or (head,))
    end=head
    proof=prove_contiguous_slot_accounting(start,end,returned_slots,skipped_slots)
    if proof.skipped_slots: append_gap_lineage(start,end,"FINALIZED_SKIPPED_SLOTS",proof.skipped_slots,root)
    if proof.missing_slots: append_gap_lineage(start,end,"UNRECOVERED_FINALIZED_GAP",proof.missing_slots,root)
    after=safe_checkpoint_target(proof,checkpoint_before)
    state="RECONCILED_TO_HEAD" if after==head else "BACKFILL_REQUIRED"
    return SolanaRestartReconciliation(checkpoint_before,head,start,end,proof.returned_slots,proof.skipped_slots,proof.missing_slots,after,state,False)

