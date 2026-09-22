\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaContiguousSlotProof:
    requested_start:int
    requested_end:int
    returned_slots:tuple
    skipped_slots:tuple
    missing_slots:tuple
    highest_contiguous_accounted_slot:int|None
    safe_to_advance:bool
    execution_authority:bool=False

def prove_contiguous_slot_accounting(requested_start,requested_end,returned_slots,skipped_slots=()):
    a=int(requested_start); b=int(requested_end)
    if b<a: raise ValueError("requested_end before requested_start")
    returned={int(x) for x in returned_slots if a<=int(x)<=b}
    skipped={int(x) for x in skipped_slots if a<=int(x)<=b}
    overlap=returned & skipped
    if overlap: raise ValueError("slot cannot be both returned and skipped")
    accounted=returned|skipped; missing=[]
    high=None
    for slot in range(a,b+1):
        if slot not in accounted:
            missing.append(slot); break
        high=slot
    if missing:
        missing.extend(x for x in range(missing[0]+1,b+1) if x not in accounted)
    return SolanaContiguousSlotProof(a,b,tuple(sorted(returned)),tuple(sorted(skipped)),tuple(missing),high,high==b,False)

def safe_checkpoint_target(proof,current_checkpoint=None):
    target=proof.highest_contiguous_accounted_slot
    if target is None: return current_checkpoint
    if current_checkpoint is not None and target<int(current_checkpoint):
        raise RuntimeError("checkpoint regression prohibited")
    return target

