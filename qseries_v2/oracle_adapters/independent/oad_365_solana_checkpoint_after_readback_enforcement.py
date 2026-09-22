\

from __future__ import annotations
from dataclasses import dataclass
from .oad_358_solana_skipped_slot_safe_checkpoint import safe_checkpoint_target

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaCheckpointAdmission:
    current_checkpoint: int|None
    candidate_checkpoint: int|None
    admitted_checkpoint: int|None
    readback_exact: bool
    continuity_safe: bool
    state: str
    execution_authority: bool=False

def admit_checkpoint_after_readback(current_checkpoint, continuity_proof, reconciliation):
    candidate=safe_checkpoint_target(continuity_proof,current_checkpoint)
    readback_exact=(getattr(reconciliation,"reconciliation_state","")=="POST_COMMIT_RECONCILED")
    continuity_safe=bool(getattr(continuity_proof,"safe_to_advance",False))
    if not readback_exact:
        return SolanaCheckpointAdmission(current_checkpoint,candidate,current_checkpoint,False,continuity_safe,"BLOCKED_READBACK",False)
    if not continuity_safe:
        return SolanaCheckpointAdmission(current_checkpoint,candidate,current_checkpoint,True,False,"BLOCKED_CONTINUITY",False)
    return SolanaCheckpointAdmission(current_checkpoint,candidate,candidate,True,True,"CHECKPOINT_ADMITTED",False)

