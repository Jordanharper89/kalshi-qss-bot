from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
import time
from .oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy
from .oad_203_crypto_continuous_learning_repeated_cycle_worker import run_crypto_continuous_learning_worker_cycle
from .oad_200_crypto_continuous_learning_postgresql_checkpoint import read_checkpoint,verify_checkpoint

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoContinuousLearningMultiCycleCertification:
    checkpoint_start:int
    checkpoint_end:int
    cycles_completed:int
    experiences_formed:int
    exact_outcomes:int
    learned_cases_committed:int
    checkpoint_advances:int
    restart_resume_verified:bool
    assets:tuple
    cycle_states:tuple
    physical_ready:bool
    certified_at:str
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def run_crypto_continuous_learning_multi_cycle_physical_certification(
    root=None,
    cycles:int=2,
    cadence_seconds:float=65.0,
    horizon_seconds:int=60,
    timeout_seconds:float=120.0,
    acquisition_timeout_seconds:float=20.0,
    sleep_fn=time.sleep,
):
    n=int(cycles)
    if n<2: raise ValueError("multi-cycle certification requires at least 2 cycles")
    p=build_crypto_continuous_learning_worker_policy(
        cadence_seconds=cadence_seconds,horizon_seconds=horizon_seconds,
        acquisition_timeout_seconds=acquisition_timeout_seconds,
        persistence_timeout_seconds=timeout_seconds
    )
    first=read_checkpoint(root)
    if not verify_checkpoint(first): raise RuntimeError("initial checkpoint invalid")
    prior=first
    total_formed=total_outcomes=total_learned=advances=0
    states=[]; assets=set()
    for i in range(n):
        cycle=run_crypto_continuous_learning_worker_cycle(root,p,i+1)
        current=read_checkpoint(root)
        if not verify_checkpoint(current): raise RuntimeError("cycle checkpoint invalid")
        if current.cycle_sequence!=prior.cycle_sequence+1:
            raise RuntimeError("checkpoint failed monotonic cycle advance")
        if current.parent_state_hash!=prior.state_hash:
            raise RuntimeError("checkpoint failed hash-chain resume")
        advances+=1
        total_formed+=int(cycle.experiences_formed)
        total_outcomes+=int(cycle.exact_outcomes)
        total_learned+=int(cycle.learned_cases_committed)
        states.append(cycle.cycle_state)
        prior=current
        if i<n-1:
            sleep_fn(p.cadence_seconds)
    ready=bool(
        advances==n and prior.cycle_sequence==first.cycle_sequence+n and
        all(s for s in states)
    )
    return CryptoContinuousLearningMultiCycleCertification(
        first.cycle_sequence,prior.cycle_sequence,n,total_formed,total_outcomes,total_learned,
        advances,True,tuple(sorted(assets)),tuple(states),ready,
        datetime.now(timezone.utc).isoformat(),False,False,False
    )
