from __future__ import annotations
from dataclasses import dataclass
from .oad_200_crypto_continuous_learning_postgresql_checkpoint import read_checkpoint,verify_checkpoint
from .oad_203_crypto_continuous_learning_repeated_cycle_worker import run_crypto_continuous_learning_worker_cycle
from .oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoLearningRestartResumeResult:
    checkpoint_before_restart:int
    checkpoint_after_resume:int
    state_hash_before_restart:str
    parent_hash_after_resume:str
    state_hash_after_resume:str
    monotonic_resume:bool
    hash_chain_resume:bool
    physical_ready:bool
    execution_authority:bool=False

def verify_crypto_learning_restart_resume(root=None,policy=None):
    p=policy or build_crypto_continuous_learning_worker_policy()
    before=read_checkpoint(root)
    if not verify_checkpoint(before):
        raise RuntimeError("pre-restart checkpoint invalid")
    cycle=run_crypto_continuous_learning_worker_cycle(root,p,worker_cycle=before.cycle_sequence+1)
    after=read_checkpoint(root)
    if not verify_checkpoint(after):
        raise RuntimeError("post-resume checkpoint invalid")
    monotonic=(after.cycle_sequence==before.cycle_sequence+1==cycle.checkpoint_after)
    chained=(after.parent_state_hash==before.state_hash)
    return CryptoLearningRestartResumeResult(
        before.cycle_sequence,after.cycle_sequence,before.state_hash,
        after.parent_state_hash,after.state_hash,monotonic,chained,
        bool(monotonic and chained and cycle.physical_ready),False
    )
