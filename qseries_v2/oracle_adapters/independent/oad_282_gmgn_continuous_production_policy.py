from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class GMGNContinuousPolicy:
    cadence_seconds:float=60.0
    acquisition_timeout_seconds:float=30.0
    persistence_timeout_seconds:float=120.0
    initial_backoff_seconds:float=5.0
    max_backoff_seconds:float=60.0
    checkpoint_every_cycles:int=1
    execution_authority:bool=False

def default_gmgn_continuous_policy():
    return GMGNContinuousPolicy()

def verify_gmgn_continuous_policy(policy=None):
    p=policy or default_gmgn_continuous_policy()
    return (
        p.cadence_seconds>0
        and p.acquisition_timeout_seconds>0
        and p.persistence_timeout_seconds>0
        and p.initial_backoff_seconds>0
        and p.max_backoff_seconds>=p.initial_backoff_seconds
        and p.checkpoint_every_cycles>=1
        and p.execution_authority is False
        and PROBABILITY_ENABLED is False
        and DIRECTION_ENABLED is False
        and PUBLICATION_ALLOWED is False
        and EXECUTION_AUTHORITY is False
    )
