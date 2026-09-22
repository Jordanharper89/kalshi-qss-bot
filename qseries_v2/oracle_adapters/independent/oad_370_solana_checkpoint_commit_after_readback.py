\

from __future__ import annotations
from dataclasses import dataclass
from .oad_365_solana_checkpoint_after_readback_enforcement import admit_checkpoint_after_readback
from .oad_368_solana_physical_checkpoint_contract import commit_checkpoint_exact

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaCheckpointCommitResult:
    before_slot:int|None
    candidate_slot:int|None
    committed_slot:int|None
    state:str
    execution_authority:bool=False

def commit_checkpoint_after_exact_readback(current_checkpoint, continuity_proof, reconciliation, signature=None, root=None):
    admission=admit_checkpoint_after_readback(current_checkpoint,continuity_proof,reconciliation)
    if admission.state!="CHECKPOINT_ADMITTED":
        return SolanaCheckpointCommitResult(current_checkpoint,admission.candidate_checkpoint,current_checkpoint,admission.state,False)
    target=admission.admitted_checkpoint
    commit_checkpoint_exact(target,signature=signature,root=root)
    return SolanaCheckpointCommitResult(current_checkpoint,target,target,"CHECKPOINT_PHYSICALLY_COMMITTED",False)

